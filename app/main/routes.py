import os

from flask import current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user
from flask_user import login_required, roles_required
from sqlalchemy import or_

from ..extensions import covers, db
from ..forms import BookForm, ConfirmForm
from ..models import Book, Category, Loan
from ..services import BusinessError, borrow_book, save_upload
from . import bp

STAFF = ["admin", "bibliothecaire"]


@bp.route("/")
def index():
    latest = Book.query.order_by(Book.created_at.desc(), Book.id.desc()).limit(8).all()
    categories = Category.query.order_by(Category.name).all()
    counts = {
        "books": Book.query.count(),
        "categories": len(categories),
        "loans": Loan.query.count(),
    }
    return render_template("main/index.html", latest=latest, categories=categories, counts=counts)


@bp.route("/catalogue")
def catalogue():
    q = request.args.get("q", "").strip()
    category_id = request.args.get("categorie", type=int)

    query = Book.query
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Book.title.ilike(like), Book.author.ilike(like), Book.isbn.ilike(like)))
    if category_id:
        query = query.filter(Book.category_id == category_id)

    pagination = query.order_by(Book.created_at.desc(), Book.id.desc()).paginate(
        page=request.args.get("page", 1, type=int),
        per_page=current_app.config["BOOKS_PER_PAGE"], error_out=False)

    return render_template(
        "main/catalogue.html",
        books=pagination.items, pagination=pagination, q=q, category_id=category_id,
        categories=Category.query.order_by(Category.name).all(),
    )


@bp.route("/livres/<int:book_id>")
def book_detail(book_id):
    book = db.get_or_404(Book, book_id)
    already = current_user.is_authenticated and any(l.book_id == book.id for l in current_user.active_loans)
    return render_template("main/book_detail.html", book=book, already=already, form=ConfirmForm())


@bp.route("/livres/<int:book_id>/emprunter", methods=["POST"])
@login_required
def borrow(book_id):
    form = ConfirmForm()
    book = db.get_or_404(Book, book_id)
    if form.validate_on_submit():
        try:
            loan = borrow_book(current_user, book)
            flash(f"« {book.title} » emprunté. À rendre avant le {loan.due_at:%d/%m/%Y}.", "success")
        except BusinessError as e:
            flash(str(e), "warning")
    return redirect(url_for("main.book_detail", book_id=book.id))


def _category_choices(form):
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.name)]


def _delete_file(upload_set, filename):
    if filename:
        path = upload_set.path(filename)
        if os.path.exists(path):
            os.remove(path)


def _fill_book(form, book):
    for field in ("title", "author", "year", "category_id", "copies", "summary"):
        setattr(book, field, getattr(form, field).data)
    book.isbn = (form.isbn.data or "").strip() or None


def _apply_upload(form, book):
    if form.cover.data and getattr(form.cover.data, "filename", ""):
        old = book.cover
        book.cover = save_upload(covers, form.cover.data)
        _delete_file(covers, old)


@bp.route("/livres/nouveau", methods=["GET", "POST"])
@roles_required(STAFF)
def book_new():
    form = BookForm()
    _category_choices(form)
    if form.validate_on_submit():
        book = Book()
        _fill_book(form, book)
        _apply_upload(form, book)
        db.session.add(book)
        db.session.commit()
        flash(f"Livre « {book.title} » ajouté au catalogue.", "success")
        return redirect(url_for("main.book_detail", book_id=book.id))
    return render_template("main/book_form.html", form=form, book=None)


@bp.route("/livres/<int:book_id>/modifier", methods=["GET", "POST"])
@roles_required(STAFF)
def book_edit(book_id):
    book = db.get_or_404(Book, book_id)
    form = BookForm(obj=book)
    _category_choices(form)
    if form.validate_on_submit():
        _fill_book(form, book)
        _apply_upload(form, book)
        db.session.commit()
        flash("Modifications enregistrées.", "success")
        return redirect(url_for("main.book_detail", book_id=book.id))
    return render_template("main/book_form.html", form=form, book=book)


@bp.route("/livres/<int:book_id>/supprimer", methods=["POST"])
@roles_required(STAFF)
def book_delete(book_id):
    book = db.get_or_404(Book, book_id)
    if ConfirmForm().validate_on_submit():
        if any(l.returned_at is None for l in book.loans):
            flash("Impossible de supprimer un livre ayant des emprunts en cours.", "danger")
            return redirect(url_for("main.book_detail", book_id=book.id))
        _delete_file(covers, book.cover)
        db.session.delete(book)
        db.session.commit()
        flash(f"« {book.title} » a été supprimé.", "success")
    return redirect(url_for("main.catalogue"))


@bp.route("/acces-refuse")
def forbidden():
    return render_template("errors/403.html"), 403


@bp.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(current_app.static_folder, "img"), "logo.svg",
                               mimetype="image/svg+xml")


@bp.route("/accueil")
def legacy_home():
    return redirect(url_for("main.index"))


@bp.route("/catalog")
@bp.route("/books")
def legacy_catalogue():
    return redirect(url_for("main.catalogue", **request.args), code=301)


@bp.route("/isbn/<isbn>")
def by_isbn(isbn):
    book = Book.query.filter_by(isbn=isbn).first_or_404()
    return redirect(url_for("main.book_detail", book_id=book.id), code=303)
