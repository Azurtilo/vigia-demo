"""Explicit disposable demo; never imports real settings or .env."""

import os

from .demo_safety import demo_secret_key, private_hosts
from .test_settings import *

DEBUG = True
ROOT_URLCONF = "core.mobile_demo_urls"
DEMO_DIR = REPO_DIR / ".mobile-demo"
DEMO_DIR.mkdir(exist_ok=True)
# Never sign sessions or action tokens with the versioned test key.
SECRET_KEY = demo_secret_key(DEMO_DIR / "secret_key")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DEMO_DIR / "demo.sqlite3",
    }
}
MEDIA_ROOT = DEMO_DIR / "media"
STATIC_ROOT = DEMO_DIR / "static"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "10.0.2.2", "testserver"] + private_hosts(
    os.environ.get("VIGIA_DEMO_HOSTS", "")
)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
PRIVACY_ENFORCED = True  # the demo behaves like production (spec 014)
ACCOUNT_RATE_LIMITS = {"login": "30/m/ip", "login_failed": "20/m/ip,20/m/key"}
