from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("_allauth/", include("allauth.headless.urls")),
    path("api/v1/", include("CuidadosApp.api.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("planes/", include("PlanesApp.urls")),
    path("cuidados/", include("CuidadosApp.urls")),
    path("privacidad/", include("PrivacidadApp.urls")),
    path("", include("homeApp.urls")),
    path("", include("UsuarioApp.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
