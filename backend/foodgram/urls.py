from accounts.admin_site import foodgram_admin_site
from api.views.short_links import short_link_redirect
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path('admin/', foodgram_admin_site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/', include('api.urls')),
    path('s/<str:code>/', short_link_redirect, name='short-link-redirect'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
