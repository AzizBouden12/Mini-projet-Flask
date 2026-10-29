import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "oui", "on")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-cle-a-changer-en-production-7f3a9c")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "instance", "biblio.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    FORCE_HTTPS = _env_bool("FORCE_HTTPS", False)

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = FORCE_HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = FORCE_HTTPS
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    API_TOKEN_MAX_AGE = 3600

    UPLOADS_DEFAULT_DEST = os.path.join(BASE_DIR, "instance", "uploads")
    UPLOADS_AUTOSERVE = True
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    USER_APP_NAME = "BiblioFlask"
    USER_APP_VERSION = "1.0"
    USER_CORPORATION_NAME = "SESAME - INGTA2"
    USER_COPYRIGHT_YEAR = 2026
    USER_ENABLE_EMAIL = True
    USER_ENABLE_USERNAME = True
    USER_ENABLE_CONFIRM_EMAIL = False
    USER_ENABLE_FORGOT_PASSWORD = False
    USER_ENABLE_CHANGE_USERNAME = False
    USER_ENABLE_MULTIPLE_EMAILS = False
    USER_ALLOW_LOGIN_WITHOUT_CONFIRMED_EMAIL = True
    USER_SEND_PASSWORD_CHANGED_EMAIL = False
    USER_SEND_REGISTERED_EMAIL = False
    USER_SEND_USERNAME_CHANGED_EMAIL = False
    USER_REQUIRE_RETYPE_PASSWORD = True
    USER_EMAIL_SENDER_EMAIL = "no-reply@biblioflask.local"
    USER_EMAIL_SENDER_NAME = "BiblioFlask"
    USER_AFTER_LOGIN_ENDPOINT = "main.index"
    USER_AFTER_LOGOUT_ENDPOINT = "main.index"
    USER_AFTER_REGISTER_ENDPOINT = "main.index"
    USER_UNAUTHENTICATED_ENDPOINT = "user.login"
    USER_UNAUTHORIZED_ENDPOINT = "main.forbidden"

    MAIL_SUPPRESS_SEND = True
    MAIL_DEFAULT_SENDER = "no-reply@biblioflask.local"

    LOAN_DURATION_DAYS = 14
    MAX_ACTIVE_LOANS = 3
    BOOKS_PER_PAGE = 12
