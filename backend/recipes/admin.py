from accounts.admin_site import foodgram_admin_site
from django.contrib import admin

from .models import Ingredient, Recipe, RecipeIngredient, Tag


class IngredientInline(admin.TabularInline):
    """Inline-редактор ингредиентов в рецепте."""

    model = RecipeIngredient
    extra = 1
    fields = ('ingredient', 'amount')
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Recipe, site=foodgram_admin_site)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-интерфейс для рецептов."""

    list_display = (
        'name',
        'author',
        'cooking_time',
        'favorite_count',
        'in_cart_count',
    )
    list_filter = ('tags', 'author')
    search_fields = ('name', 'text', 'author__username')
    readonly_fields = ('favorite_count', 'in_cart_count')
    raw_id_fields = ('author',)
    inlines = (IngredientInline,)
    list_per_page = 20

    @admin.display(description='В избранном')
    def favorite_count(self, obj):
        return obj.favorites.count()

    @admin.display(description='В корзине')
    def in_cart_count(self, obj):
        return obj.shopping_cart_items.count()


@admin.register(Ingredient, site=foodgram_admin_site)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-интерфейс для ингредиентов."""

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)
    list_per_page = 20


@admin.register(Tag, site=foodgram_admin_site)
class TagAdmin(admin.ModelAdmin):
    """Админ-интерфейс для тегов."""

    list_display = ('name', 'slug')
    search_fields = ('name',)
