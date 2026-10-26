import django_filters
from django import forms
from django.db.models import Q
from recipes.models import Recipe
from rest_framework.filters import BaseFilterBackend


class TagsFilter(BaseFilterBackend):
    """
    Фильтр для выборки рецептов по тегам.

    Поддерживает два формата:
    - ?tags=breakfast,lunch (значения через запятую)
    - ?tags=breakfast&tags=lunch (несколько ключей)
    Возвращает рецепты, содержащие хотя бы один из указанных тегов (OR).
    """

    def filter_queryset(self, request, queryset, view):
        tags_values = request.query_params.getlist('tags')
        if not tags_values:
            return queryset

        slugs = []
        for tag_value in tags_values:
            if ',' in tag_value:
                slugs.extend(
                    slug.strip()
                    for slug in tag_value.split(',')
                    if slug.strip()
                )
            else:
                slugs.append(tag_value.strip())

        if not slugs:
            return queryset

        query = Q()
        for slug in slugs:
            query |= Q(tags__slug=slug)

        return queryset.filter(query).distinct()


class RecipeFilter(django_filters.FilterSet):
    author = django_filters.NumberFilter(field_name='author__id')
    is_favorited = django_filters.BooleanFilter(
        method='filter_is_favorited',
        widget=forms.TextInput,
    )
    is_in_shopping_cart = django_filters.BooleanFilter(
        method='filter_is_in_shopping_cart',
        widget=forms.TextInput,
    )

    class Meta:
        model = Recipe
        fields = ('author', 'is_favorited', 'is_in_shopping_cart')

    def _get_user(self):
        """Возвращает пользователя из запроса, если он есть и не анонимен."""
        if hasattr(self, 'request') and self.request:
            user = self.request.user
            if not user.is_anonymous:
                return user
        return None

    def filter_is_favorited(self, queryset, name, value):
        """Фильтрует рецепты, добавленные в избранное пользователя."""
        if not value:
            return queryset
        user = self._get_user()
        if user:
            return queryset.filter(favorites__user=user).distinct()
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if not value:
            return queryset
        user = self._get_user()
        if user:
            return queryset.filter(shopping_cart_items__user=user).distinct()
        return queryset
