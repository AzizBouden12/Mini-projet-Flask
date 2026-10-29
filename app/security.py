import secrets
from functools import wraps

from flask import current_app, g, jsonify, redirect, request
from flask_login import current_user
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from .extensions import db

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


def init_security(app):
    @app.before_request
    def _force_https_and_nonce():
        g.csp_nonce = secrets.token_urlsafe(16)

        if app.config.get("FORCE_HTTPS") and not request.is_secure and not app.testing:
            return redirect(request.url.replace("http://", "https://", 1), code=301)

    @app.after_request
    def _security_headers(response):
        nonce = getattr(g, "csp_nonce", "")
        cdn = "https://cdn.jsdelivr.net"
        script_src = f"'self' {cdn} 'nonce-{nonce}'"
        if request.path.startswith("/admin"):
            script_src = f"'self' {cdn} 'unsafe-inline'"

        csp = (
            "default-src 'self'; "
            f"script-src {script_src}; "
            f"style-src 'self' 'unsafe-inline' {cdn} https://fonts.googleapis.com; "
            f"font-src 'self' {cdn} https://fonts.gstatic.com data:; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "form-action 'self'; "
            "base-uri 'self'; "
            "object-src 'self'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        if request.is_secure:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="api-token")


def generate_api_token(user):
    return _serializer().dumps({"uid": user.id})


def verify_api_token(token):
    from .models import User

    try:
        data = _serializer().loads(token, max_age=current_app.config["API_TOKEN_MAX_AGE"])
    except (SignatureExpired, BadSignature):
        return None
    user = db.session.get(User, data.get("uid"))
    if user is None or not user.active:
        return None
    return user


def check_basic_credentials(username, password):
    from .models import User

    if not username or not password:
        return None
    user = User.query.filter((User.username == username) | (User.email == username)).first()
    if user is None or not user.active:
        return None
    if not current_app.user_manager.verify_password(password, user.password):
        return None
    return user


def json_error(status, message, **extra):
    payload = {"error": message, "status": status}
    payload.update(extra)
    response = jsonify(payload)
    response.status_code = status
    if status == 401:
        response.headers["WWW-Authenticate"] = 'Bearer realm="BiblioFlask API", Basic realm="BiblioFlask API"'
    return response


def authenticate_request():
    auth = request.authorization
    header = request.headers.get("Authorization", "")

    if header.startswith("Bearer "):
        user = verify_api_token(header[7:].strip())
        return (user, "bearer") if user else (None, None)

    if auth is not None and auth.type == "basic":
        user = check_basic_credentials(auth.username, auth.password)
        return (user, "basic") if user else (None, None)

    if request.method in SAFE_METHODS and current_user.is_authenticated:
        return (current_user._get_current_object(), "session")

    return (None, None)


def api_auth_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user, mode = authenticate_request()
            if user is None:
                return json_error(401, "Authentification requise (Bearer ou Basic).")
            if roles and not user.has_roles(roles):
                return json_error(403, "Droits insuffisants pour cette ressource.", required_roles=list(roles))
            g.api_user, g.auth_mode = user, mode
            return view(*args, **kwargs)

        return wrapper

    return decorator
