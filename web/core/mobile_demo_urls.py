from django.conf import settings
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.urls import path
from django.views.static import serve

from .urls import urlpatterns as project_patterns


def mobile(request, asset="index.html"):
    return serve(
        request,
        asset or "index.html",
        document_root=settings.REPO_DIR / "mobile" / "build" / "web",
    )


def download_page(request):
    return render(request, "mobile_demo_download.html", {"server_url": request.build_absolute_uri("/").rstrip("/")})


def download_apk(request):
    artifact = settings.REPO_DIR / "mobile/build/app/outputs/flutter-apk/app-debug.apk"
    if not artifact.is_file():
        raise Http404("APK todavía no generado")
    return FileResponse(artifact.open("rb"), as_attachment=True, filename="VIGIA-android-prueba.apk",
                        content_type="application/vnd.android.package-archive")


urlpatterns = [
    path("descargar/", download_page, name="demo_download"),
    path("descargar/android.apk", download_apk, name="demo_apk"),
    path("mobile/", mobile),
    path("mobile/<path:asset>", mobile),
] + project_patterns
