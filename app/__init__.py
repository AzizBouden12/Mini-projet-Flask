import os
from datetime import datetime

from flask import Flask, g, render_template, request
from flask_babel import Babel
from flask_uploads import configure_uploads
from flask_user import UserManager
from flask_user.signals import user_registered

from config import Config

from .extensions import covers, csrf, db, mail
from .i18n import translate


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    configure_uploads(app, covers)

    from .models import Role, User
    app.user_manager = UserManager(app, db, User)

    @user_registered.connect_via(app)
    def _assign_default_role(sender, user, **extra):
        role = Role.query.filter_by(name="membre").first()
        if role and role not in user.roles:
            user.roles.append(role)
            db.session.commit()

    Babel(app, locale_selector=lambda: "fr", timezone_selector=lambda: "Africa/Tunis")

    from .security import init_security
    init_security(app)

    from .main import bp as main_bp
    from .api import bp as api_bp
    from .dashboard import bp as dashboard_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    csrf.exempt(api_bp)

    from .admin import init_admin
    init_admin(app)

    _register_template_helpers(app)
    _register_error_handlers(app)

    from .cli import register_cli
    register_cli(app)

    with app.app_context():
        db.create_all()

    return app


def _register_template_helpers(app):
    @app.template_filter("date_fr")
    def date_fr(value, fmt="%d/%m/%Y"):
        return value.strftime(fmt) if value else "—"

    @app.template_filter("fr")
    def fr(message):
        return translate(message)

    @app.template_filter("plural")
    def plural(n, singular, plural_form=None):
        return f"{n} {singular if n in (0, 1) else (plural_form or singular + 's')}"

    @app.context_processor
    def inject_globals():
        return {
            "now": datetime.utcnow(),
            "csp_nonce": getattr(g, "csp_nonce", ""),
            "app_name": app.config["USER_APP_NAME"],
        }


def _register_error_handlers(app):
    from .security import json_error

    def _handler(code):
        def handle(e):
            if request.path.startswith("/api/"):
                return json_error(code, getattr(e, "description", "Erreur"))
            return render_template(f"errors/{code}.html", error=e), code
        return handle

    for code in (403, 404, 413, 500):
        app.register_error_handler(code, _handler(code))
