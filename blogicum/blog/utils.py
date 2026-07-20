from django.core.paginator import Paginator

from .constants import POSTS_ON_INDEX_PAGE


def paginate(request, queryset):
    """Вернуть страницу пагинатора для queryset."""
    paginator = Paginator(queryset, POSTS_ON_INDEX_PAGE)
    page_number = request.GET.get("page")
    return paginator.get_page(page_number)
