from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .admin_site import foodgram_admin_site
from .models import Follow, User


@admin.register(User, site=foodgram_admin_site)
class UserAdmin(DjangoUserAdmin):
    """Кастомный админ-интерфейс для модели User."""

    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'favorite_count',
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (
            'Personal info',
            {'fields': ('username', 'first_name', 'last_name', 'avatar')},
        ),
        (
            'Permissions',
            {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': ('email', 'username', 'password1', 'password2'),
            },
        ),
    )
    readonly_fields = ('favorite_count',)

    @admin.display(description='Избранное')
    def favorite_count(self, user):
        """Возвращает количество рецептов в избранном у пользователя."""
        return user.favorites.count()


@admin.register(Follow, site=foodgram_admin_site)
class FollowAdmin(admin.ModelAdmin):
    """Админ-интерфейс для подписок."""

    ordering = ('user__username', 'following__username')
    list_display = ('id', 'user', 'following')
    list_filter = ('following',)
    search_fields = ('user__username', 'following__username')
    list_per_page = 20
