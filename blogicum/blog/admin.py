from django.contrib import admin

from .models import Category, Comment, Location, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'slug',
        'is_published',
        'created_at',
    )
    list_filter = (
        'is_published',
        'created_at',
    )
    search_fields = (
        'title',
        'slug',
    )
    prepopulated_fields = {
        'slug': ('title',)
    }


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'is_published',
        'created_at',
    )
    list_filter = (
        'is_published',
        'created_at',
    )
    search_fields = (
        'name',
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'is_published',
        'category',
        'location',
        'author',
    )
    list_filter = (
        'is_published',
        'pub_date',
        'category',
    )
    search_fields = (
        'title',
        'text',
    )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        "text",
        "author",
        "post",
        "created_at",
    )
    list_filter = (
        "created_at",
        "author",
    )
    search_fields = (
        "text",
    )
