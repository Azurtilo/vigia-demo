"""Explicit disposable demo; never imports real settings or .env."""

import os

from .test_settings import *

DEBUG = True
ROOT_URLCONF = "core.mobile_demo_urls"
DEMO_DIR = REPO_DIR / ".mobile-demo"
DEMO_DIR.mkdir(exist_ok=True)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DEMO_DIR / "demo.sqlite3",
    }
}
MEDIA_ROOT = DEMO_DIR / "media"
STATIC_ROOT = DEMO_DIR / "static"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "10.0.2.2", "testserver"] + [
    x for x in os.environ.get("VIGIA_DEMO_HOSTS", "").split(",") if x
]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
ACCOUNT_RATE_LIMITS = {"login": "30/m/ip", "login_failed": "20/m/ip,20/m/key"}
