from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _

from .forms import AdminAuthenticationForm


class FoodgramAdminSite(AdminSite):
    """Сайт администратора Foodgram с авторизацией по username."""

    login_form = AdminAuthenticationForm

    site_header = _('Управление рецептами')
    site_title = _('Админ-панель Foodgram')
    index_title = _('Добро пожаловать в админ-панель')


foodgram_admin_site = FoodgramAdminSite(name='foodgram_admin')
