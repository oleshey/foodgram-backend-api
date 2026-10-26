import base64
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from rest_framework.test import APIClient

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(
        username='alice',
        email='alice@example.com',
        password='StrongPass123',
        first_name='Alice',
        last_name='Tester',
    )


@pytest.fixture
def author():
    return User.objects.create_user(
        username='bob',
        email='bob@example.com',
        password='StrongPass123',
        first_name='Bob',
        last_name='Author',
    )


@pytest.fixture
def ingredient():
    return Ingredient.objects.create(
        name='Картошка',
        measurement_unit='шт.',
    )


@pytest.fixture
def tag():
    return Tag.objects.create(
        name='Завтрак',
        slug='breakfast',
    )


def make_png_file():
    png_bytes = (
        b'\x89PNG\r\n\x1a\n'
        b'\x00\x00\x00\rIHDR'
        b'\x00\x00\x00\x01\x00\x00\x00\x01'
        b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\x0cIDATx\x9cc```\x00\x00\x00\x02\x00\x01\xe5\x27\xca'
        b'\x00\x00\x00\x00IEND\xaeB`\x82'
    )
    return SimpleUploadedFile('test.png', png_bytes, content_type='image/png')


def make_base64_image():
    return 'data:image/png;base64,{}'.format(
        base64.b64encode(make_png_file().read()).decode('utf-8')
    )


def create_recipe(author, ingredient, tag):
    recipe = Recipe.objects.create(
        author=author,
        name='Омлет',
        text='Очень вкусный омлет',
        cooking_time=10,
        image=make_png_file(),
    )
    recipe.tags.add(tag)
    RecipeIngredient.objects.create(
        recipe=recipe,
        ingredient=ingredient,
        amount=2,
    )
    return recipe


def test_user_registration(api_client):
    payload = {
        'username': 'charlie',
        'email': 'charlie@example.com',
        'password': 'StrongPass123',
        'first_name': 'Charlie',
        'last_name': 'User',
    }

    existing_user_ids = set(User.objects.values_list('pk', flat=True))

    url = reverse('user-list')
    response = api_client.post(url, payload, format='json')

    assert response.status_code == HTTPStatus.CREATED

    new_users = User.objects.exclude(pk__in=existing_user_ids)
    assert new_users.count() == 1

    new_user = new_users.first()
    assert new_user.username == payload['username']


def test_token_login(api_client, user):
    payload = {
        'email': 'alice@example.com',
        'password': 'StrongPass123',
    }

    url = reverse('login')
    response = api_client.post(url, payload, format='json')

    assert response.status_code == HTTPStatus.OK
    assert 'auth_token' in response.data


def test_get_recipes_list(api_client, author, ingredient, tag):
    recipe = create_recipe(author, ingredient, tag)

    url = reverse('recipe-list')
    response = api_client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert response.data['count'] >= 1
    assert response.data['results'][0]['name'] == recipe.name


def test_author_can_create_recipe(api_client, user, ingredient, tag):
    api_client.force_authenticate(user=user)

    existing_recipe_ids = set(Recipe.objects.values_list('id', flat=True))

    payload = {
        'name': 'Гречка',
        'text': 'Вкусная гречка',
        'cooking_time': 20,
        'image': make_base64_image(),
        'tags': [tag.id],
        'ingredients': [
            {'id': ingredient.id, 'amount': 3},
        ],
    }

    url = reverse('recipe-list')
    response = api_client.post(url, payload, format='json')

    assert response.status_code == HTTPStatus.CREATED
    assert response.data['name'] == 'Гречка'

    new_recipes = Recipe.objects.exclude(id__in=existing_recipe_ids)
    assert new_recipes.count() == 1
    new_recipe = new_recipes.first()
    assert new_recipe.name == 'Гречка'
    assert new_recipe.author == user


def test_toggle_favorite(api_client, user, author, ingredient, tag):
    recipe = create_recipe(author, ingredient, tag)
    api_client.force_authenticate(user=user)

    url = reverse('recipe-favorite', kwargs={'pk': recipe.id})
    response = api_client.post(url)

    assert response.status_code == HTTPStatus.CREATED

    is_favorited = recipe.favorites.filter(user=user).exists()
    assert is_favorited

    delete_response = api_client.delete(url)

    assert delete_response.status_code == HTTPStatus.NO_CONTENT

    is_favorited_after_delete = recipe.favorites.filter(user=user).exists()
    assert not is_favorited_after_delete


def test_subscribe_and_unsubscribe(api_client, user, author):
    api_client.force_authenticate(user=user)

    url = reverse('user-subscribe', kwargs={'pk': author.id})
    subscribe_response = api_client.post(url)

    assert subscribe_response.status_code == HTTPStatus.CREATED

    is_subscribed = author.followers.filter(user=user).exists()
    assert is_subscribed

    unsubscribe_response = api_client.delete(url)

    assert unsubscribe_response.status_code == HTTPStatus.NO_CONTENT

    is_subscribed_after_delete = author.followers.filter(user=user).exists()
    assert is_subscribed
    assert not is_subscribed_after_delete
