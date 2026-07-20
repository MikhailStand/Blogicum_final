from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CommentForm, PostForm, UserEditForm
from .models import Category, Comment, Post
from .utils import paginate

User = get_user_model()

POST_SELECT_RELATED = ("author", "category", "location")
HIDDEN_POST_404_TEXT = "Публикация не найдена."


def get_published_posts(queryset=None):
    """Базовый QuerySet опубликованных постов с нужными связями и фильтрами."""
    queryset = queryset or Post.objects
    return (
        queryset.select_related(*POST_SELECT_RELATED)
        .filter(
            is_published=True,
            pub_date__lte=timezone.now(),
            category__is_published=True,
        )
        .annotate(comment_count=Count("comments"))
        .order_by("-pub_date")
    )


def _ensure_post_visible_for_user(post, user):
    """Проверить доступ к неопубликованному/отложенному посту.

    Автор видит свои посты всегда, остальные — только опубликованные и в
    опубликованной категории, не в будущем.
    """
    if post.author == user:
        return

    now = timezone.now()
    if (not post.is_published) or (post.pub_date > now) or (
        not post.category.is_published
    ):
        raise Http404(HIDDEN_POST_404_TEXT)


def index(request):
    page_obj = paginate(request, get_published_posts())
    return render(
        request,
        "blog/index.html",
        {"page_obj": page_obj},
    )


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related(*POST_SELECT_RELATED),
        pk=post_id,
    )
    _ensure_post_visible_for_user(post, request.user)

    comments = post.comments.select_related("author").order_by("created_at")
    context = {
        "post": post,
        "comments": comments,
        "form": CommentForm(),
    }
    return render(
        request,
        "blog/detail.html",
        context,
    )


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True,
    )
    page_obj = paginate(request, get_published_posts(category.posts.all()))
    return render(
        request,
        "blog/category.html",
        {
            "category": category,
            "page_obj": page_obj,
        },
    )


def profile(request, username):
    profile_user = get_object_or_404(User, username=username)
    qs = (
        Post.objects.select_related(*POST_SELECT_RELATED)
        .filter(author=profile_user)
        .annotate(comment_count=Count("comments"))
        .order_by("-pub_date")
    )
    if request.user != profile_user:
        qs = get_published_posts(qs)

    page_obj = paginate(request, qs)
    return render(
        request,
        "blog/profile.html",
        {"profile": profile_user, "page_obj": page_obj},
    )


def registration(request):
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect("blog:profile", username=user.username)

    return render(
        request,
        "registration/registration_form.html",
        {"form": form},
    )


@login_required
def edit_profile(request):
    form = UserEditForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("blog:profile", username=request.user.username)

    return render(
        request,
        "blog/user.html",
        {"form": form},
    )


@login_required
def create_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        form.save_m2m()
        return redirect("blog:profile", username=request.user.username)

    return render(
        request,
        "blog/create.html",
        {"form": form},
    )


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect("blog:post_detail", post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("blog:post_detail", post_id=post_id)

    return render(
        request,
        "blog/create.html",
        {"form": form},
    )


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author and not request.user.is_staff:
        return redirect("blog:post_detail", post_id=post_id)

    form = PostForm(instance=post)
    if request.method == "POST":
        post.delete()
        return redirect("blog:profile", username=request.user.username)

    return render(
        request,
        "blog/create.html",
        {"form": form},
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related("category"),
        pk=post_id,
    )
    _ensure_post_visible_for_user(post, request.user)

    form = CommentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect("blog:post_detail", post_id=post_id)

    comments = post.comments.select_related("author").order_by("created_at")
    return render(
        request,
        "blog/detail.html",
        {"post": post, "comments": comments, "form": form},
    )


def _get_comment_or_404(post_id, comment_id):
    return get_object_or_404(Comment, pk=comment_id, post_id=post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = _get_comment_or_404(post_id, comment_id)
    if request.user != comment.author and not request.user.is_staff:
        return redirect("blog:post_detail", post_id=post_id)

    form = CommentForm(request.POST or None, instance=comment)
    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("blog:post_detail", post_id=post_id)

    return render(
        request,
        "blog/comment.html",
        {"comment": comment, "form": form},
    )


@login_required
def delete_comment(request, post_id, comment_id):
    comment = _get_comment_or_404(post_id, comment_id)
    if request.user != comment.author and not request.user.is_staff:
        return redirect("blog:post_detail", post_id=post_id)

    if request.method == "POST":
        comment.delete()
        return redirect("blog:post_detail", post_id=post_id)

    return render(
        request,
        "blog/comment.html",
        {"comment": comment},
    )
