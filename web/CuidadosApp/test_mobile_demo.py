import tempfile
from pathlib import Path

from django.test import TestCase, override_settings


class MobileDemoDownloadTests(TestCase):
    """RF-015-05: the demo download page only offers an APK that exists."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name)
        demo = override_settings(ROOT_URLCONF="core.mobile_demo_urls", REPO_DIR=self.repo)
        demo.enable()
        self.addCleanup(demo.disable)

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True)
        path.write_bytes(content)

    def test_without_apk_page_says_so_and_download_is_404(self):
        page = self.client.get("/descargar/")
        self.assertContains(page, "APK Android no disponible")
        self.assertNotContains(page, "/descargar/android.apk")
        self.assertEqual(self.client.get("/descargar/android.apk").status_code, 404)

    def test_stable_artifact_is_preferred_over_build_output(self):
        self.write("mobile/build/app/outputs/flutter-apk/app-debug.apk", b"debug")
        self.write("artifacts/android/VIGIA-android-prueba.apk", b"stable")
        page = self.client.get("/descargar/")
        self.assertContains(page, "/descargar/android.apk")
        r = self.client.get("/descargar/android.apk")
        self.assertEqual(b"".join(r.streaming_content), b"stable")
        self.assertIn("VIGIA-android-prueba.apk", r["Content-Disposition"])

    def test_build_output_is_used_when_there_is_no_stable_artifact(self):
        self.write("mobile/build/app/outputs/flutter-apk/app-debug.apk", b"debug")
        r = self.client.get("/descargar/android.apk")
        self.assertEqual(b"".join(r.streaming_content), b"debug")
