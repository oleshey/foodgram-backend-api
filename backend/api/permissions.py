from rest_framework.permissions import BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Разрешение для проверки, что пользователь является автором объекта."""

    def has_object_permission(self, request, view, recipe):
        return (
            request.method in {'GET', 'HEAD', 'OPTIONS'}
            or recipe.author == request.user
        )
