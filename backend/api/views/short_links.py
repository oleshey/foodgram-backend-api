from actions.models import ShortLink
from django.shortcuts import get_object_or_404, redirect

FRONTEND_RECIPE_PATH = '/recipes/{recipe_id}/'


def short_link_redirect(request, code):
    short_link = get_object_or_404(ShortLink, code=code)
    return redirect(
        FRONTEND_RECIPE_PATH.format(recipe_id=short_link.recipe_id)
    )
