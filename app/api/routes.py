from flask import current_app, g, jsonify, request, url_for
from sqlalchemy import or_
from werkzeug.exceptions import HTTPException

from ..extensions import covers, db
from ..models import Book, Category, Loan
from ..security import (api_auth_required, check_basic_credentials, generate_api_token,
                        json_error)
from ..services import BusinessError, borrow_book, compute_stats, return_loan, save_upload
from . import bp

STAFF = ("admin", "bibliothecaire")


@bp.errorhandler(HTTPException)
def _http_error(e):
    return json_error(e.code, e.description)


@bp.errorhandler(BusinessError)
def _business_error(e):
    return json_error(409, str(e))


def _json_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


@bp.get("/")
def index():
    return jsonify({
        "name": "BiblioFlask API",
        "version": "1.0",
        "resources": {
            "books": url_for("api.list_books", _external=True),
            "categories": url_for("api.list_categories", _external=True),
            "loans": url_for("api.list_loans", _external=True),
            "stats": url_for("api.stats", _external=True),
            "me": url_for("api.me", _external=True),
            "token": url_for("api.create_token", _external=True),
        },
    })


@bp.post("/auth/token")
def create_token():
    auth = request.authorization
    body = _json_body() or {}
    username = auth.username if auth else body.get("username")
    password = auth.password if auth else body.get("password")

    user = check_basic_credentials(username, password)
    if user is None:
        return json_error(401, "Identifiants invalides.")
    return jsonify({
        "token": generate_api_token(user),
        "token_type": "Bearer",
        "expires_in": current_app.config["API_TOKEN_MAX_AGE"],
        "user": user.to_dict(),
    }), 201


@bp.get("/me")
@api_auth_required()
def me():
    user = g.api_user
    data = user.to_dict()
    data["auth_mode"] = g.auth_mode
    data["active_loans"] = [l.to_dict() for l in user.active_loans]
    return jsonify(data)


@bp.get("/books")
def list_books():
    query = Book.query
    q = request.args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        query = query.filter(or_(Book.title.ilike(like), Book.author.ilike(like)))
    category = request.args.get("category", type=int)
    if category:
        query = query.filter(Book.category_id == category)

    per_page = min(request.args.get("per_page", 20, type=int), 100)
    page = query.order_by(Book.title).paginate(page=request.args.get("page", 1, type=int),
                                               per_page=per_page, error_out=False)
    return jsonify({
        "items": [b.to_dict() for b in page.items],
        "page": page.page,
        "pages": page.pages,
        "total": page.total,
        "next": url_for("api.list_books", page=page.next_num, per_page=per_page, _external=True)
        if page.has_next else None,
    })


@bp.get("/books/<int:book_id>")
def get_book(book_id):
    return jsonify(db.get_or_404(Book, book_id).to_dict())


def _apply_book_payload(book, data, partial=False):
    errors = {}
    required = ("title", "author")
    for field in required:
        if not partial and not str(data.get(field, "")).strip():
            errors[field] = "Champ obligatoire."

    if "category_id" in data and data["category_id"] is not None:
        if db.session.get(Category, data["category_id"]) is None:
            errors["category_id"] = "Catégorie inconnue."
    for field in ("copies", "year"):
        if field in data and data[field] is not None:
            try:
                data[field] = int(data[field])
            except (TypeError, ValueError):
                errors[field] = "Doit être un entier."
    if "copies" in data and isinstance(data.get("copies"), int) and data["copies"] < 1:
        errors["copies"] = "Au moins 1 exemplaire."
    if data.get("isbn"):
        other = Book.query.filter(Book.isbn == data["isbn"], Book.id != (book.id or 0)).first()
        if other:
            errors["isbn"] = "ISBN déjà utilisé."
    if errors:
        return errors

    for field in ("title", "author", "isbn", "year", "summary", "copies", "category_id"):
        if field in data:
            value = data[field]
            setattr(book, field, value.strip() if isinstance(value, str) else value)
    return None


@bp.post("/books")
@api_auth_required(*STAFF)
def create_book():
    data = _json_body()
    if data is None:
        return json_error(400, "Corps JSON attendu.")
    book = Book(copies=1)
    errors = _apply_book_payload(book, data)
    if errors:
        return json_error(422, "Données invalides.", fields=errors)
    db.session.add(book)
    db.session.commit()
    response = jsonify(book.to_dict())
    response.status_code = 201
    response.headers["Location"] = url_for("api.get_book", book_id=book.id, _external=True)
    return response


@bp.route("/books/<int:book_id>", methods=["PUT", "PATCH"])
@api_auth_required(*STAFF)
def update_book(book_id):
    book = db.get_or_404(Book, book_id)
    data = _json_body()
    if data is None:
        return json_error(400, "Corps JSON attendu.")
    errors = _apply_book_payload(book, data, partial=request.method == "PATCH")
    if errors:
        return json_error(422, "Données invalides.", fields=errors)
    db.session.commit()
    return jsonify(book.to_dict())


@bp.delete("/books/<int:book_id>")
@api_auth_required(*STAFF)
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)
    if any(l.returned_at is None for l in book.loans):
        return json_error(409, "Ce livre a des emprunts en cours.")
    db.session.delete(book)
    db.session.commit()
    return "", 204


@bp.post("/books/<int:book_id>/cover")
@api_auth_required(*STAFF)
def upload_cover(book_id):
    from flask_uploads import UploadNotAllowed

    book = db.get_or_404(Book, book_id)
    file = request.files.get("file")
    if file is None or not file.filename:
        return json_error(400, "Fichier manquant (champ « file »).")
    try:
        book.cover = save_upload(covers, file)
    except UploadNotAllowed:
        return json_error(415, "Type de fichier non autorisé.", allowed=list(covers.extensions))
    db.session.commit()
    return jsonify(book.to_dict()), 201


@bp.get("/categories")
def list_categories():
    return jsonify([c.to_dict() for c in Category.query.order_by(Category.name)])


@bp.post("/categories")
@api_auth_required(*STAFF)
def create_category():
    data = _json_body() or {}
    name = str(data.get("name", "")).strip()
    if not name:
        return json_error(422, "Données invalides.", fields={"name": "Champ obligatoire."})
    if Category.query.filter_by(name=name).first():
        return json_error(409, "Cette catégorie existe déjà.")
    category = Category(name=name, color=data.get("color") or "#334155")
    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201


@bp.get("/loans")
@api_auth_required()
def list_loans():
    user = g.api_user
    query = Loan.query.order_by(Loan.borrowed_at.desc())
    if not user.has_roles(STAFF):
        query = query.filter(Loan.user_id == user.id)
    loans = query.all()
    status = request.args.get("status")
    if status:
        loans = [l for l in loans if l.status == status]
    return jsonify([l.to_dict() for l in loans])


@bp.post("/loans")
@api_auth_required()
def create_loan():
    data = _json_body() or {}
    book = db.session.get(Book, data.get("book_id") or 0)
    if book is None:
        return json_error(404, "Livre introuvable.")
    loan = borrow_book(g.api_user, book)
    return jsonify(loan.to_dict()), 201


@bp.post("/loans/<int:loan_id>/return")
@api_auth_required()
def return_loan_api(loan_id):
    loan = db.get_or_404(Loan, loan_id)
    if loan.user_id != g.api_user.id and not g.api_user.has_roles(STAFF):
        return json_error(403, "Cet emprunt ne vous appartient pas.")
    return jsonify(return_loan(loan).to_dict())


@bp.get("/stats")
@api_auth_required(*STAFF)
def stats():
    months = max(1, min(request.args.get("months", 6, type=int), 24))
    return jsonify(compute_stats(months=months))
