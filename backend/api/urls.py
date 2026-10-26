from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views.accounts import UserViewSet
from .views.recipes import IngredientViewSet, RecipeViewSet, TagViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')

urlpatterns = [
    path('', include(router.urls)),
]
