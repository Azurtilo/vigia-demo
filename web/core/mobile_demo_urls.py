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


def android_artifact():
    """Prefers the copy kept by mobile/tool/build_android.sh over Flutter's build output."""
    stable = settings.REPO_DIR / "artifacts/android/VIGIA-android-prueba.apk"
    if stable.is_file():
        return stable
    return settings.REPO_DIR / "mobile/build/app/outputs/flutter-apk/app-debug.apk"


def download_page(request):
    return render(request, "mobile_demo_download.html", {
        "server_url": request.build_absolute_uri("/").rstrip("/"),
        "apk_available": android_artifact().is_file(),
    })


def download_apk(request):
    artifact = android_artifact()
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
