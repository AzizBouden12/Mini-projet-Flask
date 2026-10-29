import os
import uuid

from flask import redirect, request, url_for
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_admin.form import FileUploadField
from flask_admin.menu import MenuLink
from flask_admin.theme import Bootstrap4Theme
from flask_login import current_user
from flask_wtf import FlaskForm
from markupsafe import Markup, escape
from wtforms import PasswordField
from wtforms.validators import Length, Optional, ValidationError

from .extensions import covers, db
from .models import Book, Category, Loan, Role, User
from .services import compute_stats


def _random_name(obj, file_data):
    ext = os.path.splitext(file_data.filename)[1].lower()
    return f"{uuid.uuid4().hex}{ext}"


class SecureMixin:
    allowed_roles = ("admin",)

    def is_accessible(self):
        return current_user.is_authenticated and current_user.has_roles(self.allowed_roles)

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for("user.login", next=request.url))
        return redirect(url_for("main.forbidden"))


class SecureModelView(SecureMixin, ModelView):
    form_base_class = FlaskForm
    page_size = 20
    can_export = True
    can_view_details = True


class StaffIndexView(SecureMixin, AdminIndexView):
    allowed_roles = ("admin", "bibliothecaire")

    @expose("/")
    def index(self):
        return self.render("admin/index.html", stats=compute_stats())


class UserAdmin(SecureModelView):
    column_list = ("username", "email", "first_name", "last_name", "roles", "active", "created_at")
    column_searchable_list = ("username", "email", "first_name", "last_name")
    column_filters = ("active", "roles.name", "created_at")
    column_labels = {
        "username": "Identifiant", "email": "E-mail", "first_name": "Prénom", "last_name": "Nom",
        "roles": "Rôles", "active": "Actif", "created_at": "Inscrit le", "new_password": "Nouveau mot de passe",
    }
    column_exclude_list = ("password",)
    column_details_exclude_list = ("password",)
    form_excluded_columns = ("password", "loans", "email_confirmed_at", "created_at")
    form_extra_fields = {
        "new_password": PasswordField(
            "Nouveau mot de passe",
            validators=[Optional(), Length(min=6, message="6 caractères minimum.")],
            description="Laisser vide pour conserver le mot de passe actuel.",
        )
    }
    can_export = False

    def on_model_change(self, form, model, is_created):
        from flask import current_app

        if form.new_password.data:
            model.password = current_app.user_manager.hash_password(form.new_password.data)
        elif is_created:
            raise ValidationError("Un mot de passe est obligatoire pour un nouvel utilisateur.")

    def on_model_delete(self, model):
        if model.id == current_user.id:
            raise ValidationError("Vous ne pouvez pas supprimer votre propre compte.")


class RoleAdmin(SecureModelView):
    column_list = ("name", "label")
    column_labels = {"name": "Code", "label": "Libellé"}
    form_excluded_columns = ("users",)
    can_export = False


class CategoryAdmin(SecureModelView):
    allowed_roles = ("admin", "bibliothecaire")
    column_list = ("name", "color")
    column_labels = {"name": "Nom", "color": "Couleur"}
    form_excluded_columns = ("books",)
    column_formatters = {
        "color": lambda v, c, m, p: Markup(
            f'<span class="badge" style="background:{escape(m.color)};color:#fff">{escape(m.color)}</span>'
        )
    }


class BookAdmin(SecureModelView):
    allowed_roles = ("admin", "bibliothecaire")
    upload_root = None
    column_list = ("cover", "title", "author", "category", "year", "copies", "isbn")
    column_searchable_list = ("title", "author", "isbn")
    column_filters = ("category.name", "year", "author")
    column_sortable_list = ("title", "author", "year", "copies", ("category", "category.name"))
    column_labels = {
        "cover": "Couverture", "title": "Titre", "author": "Auteur", "category": "Catégorie",
        "year": "Année", "copies": "Exemplaires", "summary": "Résumé",
        "created_at": "Ajouté le",
    }
    form_excluded_columns = ("loans", "created_at")
    column_formatters = {
        "cover": lambda v, c, m, p: Markup(
            f'<img src="{escape(m.cover_url)}" alt="" style="height:48px;border-radius:4px">'
        ) if m.cover else "—",
    }

    def scaffold_form(self):
        form_class = super().scaffold_form()
        form_class.cover = FileUploadField(
            "Couverture", base_path=os.path.join(self.upload_root, covers.name), namegen=_random_name,
            allowed_extensions=list(covers.extensions))
        return form_class


class LoanAdmin(SecureModelView):
    allowed_roles = ("admin", "bibliothecaire")
    column_list = ("id", "book", "user", "borrowed_at", "due_at", "returned_at", "status")
    column_default_sort = ("borrowed_at", True)
    column_filters = ("borrowed_at", "due_at", "returned_at", "user.username", "book.title")
    column_searchable_list = ("book.title", "user.username")
    column_labels = {
        "book": "Livre", "user": "Membre", "borrowed_at": "Emprunté le", "due_at": "Retour prévu",
        "returned_at": "Rendu le", "status": "État",
    }
    _badges = {"en_cours": "primary", "en_retard": "danger", "rendu": "success"}
    column_formatters = {
        "status": lambda v, c, m, p: Markup(
            f'<span class="badge badge-{LoanAdmin._badges[m.status]}">{m.status_label}</span>'),
        "borrowed_at": lambda v, c, m, p: m.borrowed_at.strftime("%d/%m/%Y"),
        "due_at": lambda v, c, m, p: m.due_at.strftime("%d/%m/%Y"),
        "returned_at": lambda v, c, m, p: m.returned_at.strftime("%d/%m/%Y") if m.returned_at else "—",
    }


def init_admin(app):
    BookAdmin.upload_root = app.config["UPLOADS_DEFAULT_DEST"]
    admin = Admin(
        app,
        name="BiblioFlask · Admin",
        index_view=StaffIndexView(name="Accueil", url="/admin"),
        theme=Bootstrap4Theme(swatch="default", fluid=True),
    )
    admin.add_view(BookAdmin(Book, db.session, name="Livres", category="Catalogue"))
    admin.add_view(CategoryAdmin(Category, db.session, name="Catégories", category="Catalogue"))
    admin.add_view(LoanAdmin(Loan, db.session, name="Emprunts"))
    admin.add_view(UserAdmin(User, db.session, name="Utilisateurs", category="Comptes"))
    admin.add_view(RoleAdmin(Role, db.session, name="Rôles", category="Comptes"))
    admin.add_link(MenuLink(name="Tableau de bord", endpoint="dashboard.index"))
    admin.add_link(MenuLink(name="Retour au site", endpoint="main.index"))
    return admin
