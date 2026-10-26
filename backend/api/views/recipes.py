import hashlib

from actions.models import ShortLink
from api.filters import RecipeFilter, TagsFilter
from api.pagination import LimitOffsetPagination
from api.permissions import IsAuthorOrReadOnly
from api.serializers.recipes import (
    FavoriteSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    ShortLinkSerializer,
    TagSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from recipes.models import Ingredient, Recipe, Tag
from recipes.services import generate_shopping_cart_response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с тегами (только чтение)."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для работы с ингредиентами (только чтение).

    Фильтрация по начальному вхождению имени.
    """

    serializer_class = IngredientSerializer
    pagination_class = None

    def get_queryset(self):
        queryset = Ingredient.objects.all()
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""

    queryset = (
        Recipe.objects.select_related('author')
        .prefetch_related('tags', 'recipeingredients__ingredient')
        .order_by('-id')
    )

    permission_classes = (AllowAny,)

    filter_backends = (
        DjangoFilterBackend,
        TagsFilter,
    )
    filterset_class = RecipeFilter
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        """Метод для определения разрешений в зависимости от действия."""
        if self.action in (
            'create',
            'favorite',
            'shopping_cart',
            'download_shopping_cart',
        ):
            permission_classes = (IsAuthenticated,)
        elif self.action in ('update', 'partial_update', 'destroy'):
            permission_classes = (IsAuthenticated, IsAuthorOrReadOnly)
        else:
            permission_classes = (AllowAny,)

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeCreateUpdateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def _process_recipe_action(self, request, recipe, serializer_class):
        serializer = serializer_class(
            data={},
            context={
                'request': request,
                'recipe': recipe,
                'remove': request.method == 'DELETE',
            },
        )
        serializer.is_valid(raise_exception=True)

        if request.method == 'DELETE':
            serializer.remove()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer.save()

        return Response(
            RecipeMinifiedSerializer(
                recipe,
                context={'request': request},
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='favorite',
        url_name='favorite',
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        return self._process_recipe_action(
            request,
            recipe,
            FavoriteSerializer,
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='shopping_cart',
        url_name='shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        return self._process_recipe_action(
            request,
            recipe,
            ShoppingCartSerializer,
        )

    @action(
        detail=False,
        methods=('get',),
        url_path='download_shopping_cart',
        url_name='download_shopping_cart',
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в текстовом файле."""
        return generate_shopping_cart_response(request.user)

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        url_name='get-link',
        permission_classes=(AllowAny,),
    )
    def get_short_link(self, request, pk=None):
        """Получение короткой ссылки на рецепт."""
        recipe = self.get_object()

        base_code = str(recipe.id)
        short_code = hashlib.sha256(base_code.encode()).hexdigest()[:5]

        short_link_obj, _ = ShortLink.objects.get_or_create(
            recipe=recipe, defaults={'code': short_code}
        )

        serializer = ShortLinkSerializer(recipe, context={'request': request})
        return Response(serializer.data)
