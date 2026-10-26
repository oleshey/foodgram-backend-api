import io

from django.db.models import Sum
from django.http import FileResponse
from recipes.models import RecipeIngredient


def build_shopping_cart_text(user):
    """
    Формирует текстовое содержимое файла со списком покупок для пользователя.

    Агрегирует ингредиенты из всех рецептов, в корзине пользователя.
    """
    shopping_cart_recipes = user.shopping_cart_items.values_list(
        'recipe_id', flat=True
    )

    if not shopping_cart_recipes:
        return 'Список покупок пуст'

    ingredients_data = (
        RecipeIngredient.objects.filter(recipe_id__in=shopping_cart_recipes)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )

    lines = [
        f'{item["ingredient__name"]} '
        f'({item["ingredient__measurement_unit"]}) — {item["total_amount"]}'
        for item in ingredients_data
    ]

    return '\n'.join(lines)


def generate_shopping_cart_response(user):
    """Возвращает HTTP-ответ с файлом списка покупок (TXT)."""
    file_content = build_shopping_cart_text(user)

    response = FileResponse(
        io.BytesIO(file_content.encode('utf-8')),
        content_type='text/plain; charset=utf-8',
    )
    response['Content-Disposition'] = (
        'attachment; filename="shopping_cart.txt"'
    )
    return response
