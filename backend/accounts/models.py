from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """
    Кастомная модель пользователя.

    USERNAME_FIELD = 'email' позволяет логиниться по email.
    """

    email = models.EmailField(
        unique=True,
        help_text=('Required. 254 characters or fewer. Email address.'),
        verbose_name='Email',
    )

    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='Аватар',
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username',)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписки: кто (user) подписан на кого (following)."""

    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Подписчик',
    )
    following = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='followers',
        verbose_name='Подпиской на кого',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'following'),
                name='unique_follow',
            ),
        ]

    def clean(self):
        if self.user == self.following:
            raise ValidationError('Нельзя подписаться на самого себя.')
        super().clean()

    def __str__(self):
        return f'{self.user.username} -> {self.following.username}'
