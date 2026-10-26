from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Favorite(models.Model):
    """Модель для хранения рецептов в избранном пользователя."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='favorites',
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='favorites',
    )

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_favorite',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} added {self.recipe.name} to favorites'


class ShoppingCart(models.Model):
    """Модель для хранения рецептов в списке покупок пользователя."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Пользователь',
        related_name='shopping_cart_items'
    )
    recipe = models.ForeignKey(
        'recipes.Recipe',
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='shopping_cart_items',
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_user_recipe_shopping_cart',
            )
        ]
        ordering = ['-id']

    def __str__(self):
        return (
            f'{self.user.username} added {self.recipe.name} to shopping cart'
        )


class ShortLink(models.Model):
    """
    Модель для хранения коротких ссылок на рецепты.
    """

    recipe = models.OneToOneField(
        'recipes.Recipe', on_delete=models.CASCADE, related_name='short_link'
    )
    code = models.CharField(
        max_length=10, unique=True, verbose_name='Код ссылки'
    )

    class Meta:
        verbose_name = 'Короткая ссылка'
        verbose_name_plural = 'Короткие ссылки'

    def __str__(self):
        return f'Short link for {self.recipe.name}: {self.code}'
