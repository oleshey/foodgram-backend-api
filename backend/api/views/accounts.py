from api.pagination import LimitOffsetPagination
from api.serializers.accounts import (AvatarResponseSerializer,
                                      DeleteAvatarSerializer,
                                      SetAvatarSerializer,
                                      SetPasswordSerializer,
                                      SubscribeSerializer,
                                      UserRegistrationSerializer,
                                      UserSerializer,
                                      UserWithRecipesSerializer)
from django.contrib.auth import get_user_model
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями."""

    queryset = User.objects.all().order_by('id')
    pagination_class = LimitOffsetPagination

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        if self.action in {
            'subscribe',
            'subscriptions',
            'me',
            'avatar',
            'set_password',
        }:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        if self.action in ['subscribe', 'subscriptions']:
            return UserWithRecipesSerializer
        return UserSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False, methods=['get'], permission_classes=(IsAuthenticated,)
    )
    def me(self, request):
        serializer = self.get_serializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=False, methods=['post'], permission_classes=(IsAuthenticated,)
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save(update_fields=['password'])

        return Response(
            {'detail': 'Пароль успешно изменен'},
            status=status.HTTP_204_NO_CONTENT,
        )

    @action(
        detail=False,
        url_path='me/avatar',
        methods=('put', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        user = request.user

        if request.method == 'PUT':
            serializer = SetAvatarSerializer(
                data=request.data,
                context={'request': request},
            )
            serializer.is_valid(raise_exception=True)

            user.avatar = serializer.validated_data['avatar']
            user.save(update_fields=['avatar'])

            response_serializer = AvatarResponseSerializer(
                user,
                context={'request': request},
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK,
            )

        serializer = DeleteAvatarSerializer(instance=user, data={})
        serializer.is_valid(raise_exception=True)

        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, pk=None):
        """Обработка подписки (POST) и отписки (DELETE)."""
        author = self.get_object()

        serializer = SubscribeSerializer(
            data={},
            context={
                'request': request,
                'author': author,
            },
        )
        serializer.is_valid(raise_exception=True)

        if request.method == 'POST':
            serializer.save(
                user=request.user,
                following=author,
            )

            response_serializer = self.get_serializer(
                author,
                context={'request': request},
            )
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED,
            )

        author.followers.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False, methods=('get',), permission_classes=(IsAuthenticated,)
    )
    def subscriptions(self, request):
        """Список пользователей, на которых подписан текущий пользователь."""
        followed_users = User.objects.filter(followers__user=request.user)

        page = self.paginate_queryset(followed_users)
        if page is not None:
            serializer = self.get_serializer(
                page, many=True, context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(
            followed_users, many=True, context={'request': request}
        )
        return Response(serializer.data)
