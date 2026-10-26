from actions.models import Favorite, ShoppingCart
from api.image_fields import Base64ImageField
from django.contrib.auth import get_user_model
from django.urls import reverse
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework import serializers

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class UserShortSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return user.followers.filter(following=obj).exists()


class RecipeIngredientSerializer(serializers.Serializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.CharField(source='image.url', read_only=True)
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    ingredients = RecipeIngredientSerializer(
        source='recipeingredients', many=True
    )
    tags = TagSerializer(many=True, read_only=True)
    author = UserShortSerializer(read_only=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.favorites.filter(user=user).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return obj.shopping_cart_items.filter(user=user).exists()


class RecipeIngredientInputSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField(min_value=1)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientInputSerializer(
        many=True,
        write_only=True,
        required=True,
        allow_empty=False,
    )
    tags = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=True,
        allow_empty=False,
        help_text='Список ID тегов или объектов с полем id',
    )
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time',
        )

    def validate_tags(self, value):
        """Валидирует и нормализует список тегов для рецепта."""
        tag_ids = []
        for item in value:
            if isinstance(item, dict):
                if 'id' not in item:
                    raise serializers.ValidationError(
                        'Каждый тег должен содержать поле id.'
                    )
                tag_id = item['id']
            else:
                tag_id = item

            try:
                tag_id = int(tag_id)
            except (ValueError, TypeError):
                raise serializers.ValidationError(
                    'ID тега должен быть числом.'
                )

            if not Tag.objects.filter(id=tag_id).exists():
                raise serializers.ValidationError(
                    f'Тег с id {tag_id} не найден.'
                )
            tag_ids.append(tag_id)

        if len(tag_ids) != len(set(tag_ids)):
            raise serializers.ValidationError('Теги не должны повторяться.')
        return tag_ids

    def validate_ingredients(self, value):
        seen_ids = set()

        for item in value:
            ingredient_id = item['id']

            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} не найден.'
                )

            if ingredient_id in seen_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} '
                    f'указан более одного раза.'
                )

            seen_ids.add(ingredient_id)

        return value

    @staticmethod
    def _create_recipe_ingredients(recipe, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=item['id'],
                    amount=item['amount'],
                )
                for item in ingredients_data
            ]
        )

    def create(self, validated_data):
        author = self.context['request'].user

        validated_data_copy = validated_data.copy()
        ingredients_data = validated_data_copy.pop('ingredients')
        tags_data = validated_data_copy.pop('tags')
        validated_data_copy.pop('author', None)

        recipe = Recipe.objects.create(author=author, **validated_data_copy)

        recipe.tags.set(tags_data)
        self._create_recipe_ingredients(recipe, ingredients_data)

        return recipe

    def update(self, instance, validated_data):
        validated_data_copy = validated_data.copy()
        ingredients_data = validated_data_copy.pop('ingredients')
        tags_data = validated_data_copy.pop('tags')
        validated_data_copy.pop('author', None)

        instance.name = validated_data_copy.get('name', instance.name)
        instance.text = validated_data_copy.get('text', instance.text)
        instance.cooking_time = validated_data_copy.get(
            'cooking_time', instance.cooking_time
        )
        if 'image' in validated_data_copy:
            instance.image = validated_data_copy['image']
        instance.save()

        instance.tags.set(tags_data)

        existing_ingredients = {
            ri.ingredient_id: ri for ri in instance.recipeingredients.all()
        }
        current_ids = set(existing_ingredients.keys())
        new_ids = {item['id'] for item in ingredients_data}

        ids_to_delete = current_ids - new_ids
        if ids_to_delete:
            instance.recipeingredients.filter(
                ingredient_id__in=ids_to_delete
            ).delete()

        ingredients_to_update = []
        ingredients_to_create = []

        for item in ingredients_data:
            ing_id = item['id']
            amount = item['amount']

            if ing_id in existing_ingredients:
                ingredients_to_update.append(
                    (existing_ingredients[ing_id].id, amount)
                )
            else:
                ingredients_to_create.append(item)

        if ingredients_to_update:
            update_objects = []
            for pk, amount in ingredients_to_update:
                ri = RecipeIngredient(id=pk, amount=amount)
                update_objects.append(ri)
            RecipeIngredient.objects.bulk_update(update_objects, ('amount',))

        if ingredients_to_create:
            self._create_recipe_ingredients(instance, ingredients_to_create)

        return instance

    def to_representation(self, instance):
        return RecipeSerializer(
            instance=instance,
            context=self.context,
        ).data


class ShortLinkSerializer(serializers.Serializer):
    """
    Сериализатор для короткой ссылки на рецепт.

    Возвращает URL вида /s/{code}/.
    """

    short_link = serializers.SerializerMethodField()

    class Meta:
        fields = ('short_link',)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'short_link' in ret:
            ret['short-link'] = ret.pop('short_link')
        return ret

    def get_short_link(self, obj):
        request = self.context.get('request')
        short_link = getattr(obj, 'short_link', None)

        if not request or not short_link:
            return None

        path = reverse(
            'short-link-redirect',
            kwargs={'code': short_link.code},
        )
        return request.build_absolute_uri(path)


class RecipeActionSerializer(serializers.Serializer):
    model = None
    add_error = ''
    remove_error = ''

    def validate(self, attrs):
        user = self.context['request'].user
        recipe = self.context['recipe']

        exists = self.model.objects.filter(
            user=user,
            recipe=recipe,
        ).exists()

        if self.context.get('remove'):
            if not exists:
                raise serializers.ValidationError(self.remove_error)
        elif exists:
            raise serializers.ValidationError(self.add_error)

        return attrs

    def create(self, validated_data):
        return self.model.objects.create(
            user=self.context['request'].user,
            recipe=self.context['recipe'],
        )

    def remove(self):
        self.model.objects.filter(
            user=self.context['request'].user,
            recipe=self.context['recipe'],
        ).delete()


class FavoriteSerializer(RecipeActionSerializer):
    model = Favorite
    add_error = 'Рецепт уже в избранном.'
    remove_error = 'Рецепт не в избранном.'


class ShoppingCartSerializer(RecipeActionSerializer):
    model = ShoppingCart
    add_error = 'Рецепт уже в списке покупок.'
    remove_error = 'Рецепт не в списке покупок.'
