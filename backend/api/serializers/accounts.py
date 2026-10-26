# accounts/serializers.py
import base64
import io
import re
import uuid

from accounts.models import Follow
from api.serializers.recipes import RecipeMinifiedSerializer
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from PIL import Image
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения данных пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
        )

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return user.followers.filter(user=request.user).exists()
        return False


class UserWithRecipesSerializer(UserSerializer):
    """
    Сериализатор для отображения пользователя с информацией о рецептах.

    Наследует логику is_subscribed от UserSerializer.
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, user):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit', 0)

        queryset = user.recipes.all()

        if recipes_limit:
            queryset = queryset[: int(recipes_limit)]

        return RecipeMinifiedSerializer(
            queryset, many=True, context={'request': request}
        ).data

    def get_recipes_count(self, user):
        return user.recipes.count()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для создания нового пользователя (регистрация)."""

    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'password',
        )

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password'],
        )
        return user


class SetPasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля."""

    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

    def validate_current_password(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if not user.check_password(value):
                raise serializers.ValidationError('Неверный текущий пароль.')
        return value


class SetAvatarSerializer(serializers.Serializer):
    """
    Сериализатор для установки аватара.

    Принимает base64 строку и сохраняет файл.
    Имя файла формируется на основе username пользователя для уникальности.
    """

    avatar = serializers.CharField(required=True)

    def validate_avatar(self, value):
        """Преобразует base64 строку в файл изображения."""
        if not value:
            raise serializers.ValidationError('Аватар не может быть пустым.')

        request = self.context.get('request')
        if (
            request
            and request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'username')
        ):
            username = request.user.username
        else:
            username = f'user_{uuid.uuid4().hex}'

        safe_username = re.sub(r'[^\w]', '_', username)

        try:
            if ',' in value:
                header, encoded = value.split(',', 1)
            else:
                header = ''
                encoded = value
        except ValueError as invalid_format_error:
            raise serializers.ValidationError(
                'Некорректный формат base64 строки.'
            ) from invalid_format_error

        if header:
            try:
                image_format = header.split('/')[1].split(';')[0]
            except (IndexError, ValueError) as invalid_mime_error:
                raise serializers.ValidationError(
                    f'Некорректный MIME-тип: {header}'
                ) from invalid_mime_error
        else:
            image_format = 'png'

        try:
            image_data = base64.b64decode(encoded, validate=True)
        except (ValueError, TypeError) as decode_error:
            raise serializers.ValidationError(
                'Некорректные Base64-данные изображения.'
            ) from decode_error

        try:
            Image.open(io.BytesIO(image_data))
        except OSError as invalid_image_error:
            raise serializers.ValidationError(
                'Загруженный файл не является изображением или повреждён.'
            ) from invalid_image_error

        filename = f'avatar_{safe_username}.{image_format}'
        return ContentFile(image_data, name=filename)


class AvatarResponseSerializer(serializers.ModelSerializer):
    """Сериализатор для ответа с обновленным аватаром."""

    class Meta:
        model = User
        fields = ('avatar',)


class DeleteAvatarSerializer(serializers.Serializer):

    def validate(self, attrs):
        if not self.instance or not self.instance.avatar:
            raise serializers.ValidationError(
                {'avatar': 'Аватар не установлен.'}
            )
        return attrs


class SubscribeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Follow
        fields = ('user', 'following')
        read_only_fields = fields

    def validate(self, attrs):
        request = self.context['request']
        author = self.context['author']

        is_following = request.user.subscriptions.filter(
            following=author
        ).exists()

        if request.method == 'POST':
            if request.user == author:
                raise serializers.ValidationError(
                    {'errors': 'Нельзя подписаться на самого себя.'}
                )
            if is_following:
                raise serializers.ValidationError(
                    {'errors': 'Вы уже подписаны на этого пользователя.'}
                )

        elif request.method == 'DELETE' and not is_following:
            raise serializers.ValidationError(
                {'errors': 'Вы не подписаны на этого пользователя.'}
            )

        return attrs
