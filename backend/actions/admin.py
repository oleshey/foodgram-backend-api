from accounts.admin_site import foodgram_admin_site
from django.contrib import admin

from .models import Favorite, ShoppingCart, ShortLink


@admin.register(Favorite, site=foodgram_admin_site)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-интерфейс для избранного."""

    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    raw_id_fields = ('user', 'recipe')
    list_per_page = 20


@admin.register(ShoppingCart, site=foodgram_admin_site)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-интерфейс для списка покупок."""

    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')
    raw_id_fields = ('user', 'recipe')
    list_per_page = 20


@admin.register(ShortLink, site=foodgram_admin_site)
class ShortLinkAdmin(admin.ModelAdmin):
    """Админ-интерфейс для коротких ссылок."""

    list_display = ('recipe', 'code')
    search_fields = ('recipe__name', 'code')
    raw_id_fields = ('recipe',)
