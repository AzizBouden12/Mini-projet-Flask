from datetime import datetime, timedelta

from flask import current_app, url_for
from flask_user import UserMixin

from .extensions import covers, db


class Role(db.Model):
    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    label = db.Column(db.String(100))

    def __str__(self):
        return self.label or self.name


class UserRoles(db.Model):
    __tablename__ = "user_roles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id", ondelete="CASCADE"))


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean, nullable=False, server_default="1")

    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    email_confirmed_at = db.Column(db.DateTime())
    password = db.Column(db.String(255), nullable=False, server_default="")

    first_name = db.Column(db.String(100), nullable=False, server_default="")
    last_name = db.Column(db.String(100), nullable=False, server_default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship("Role", secondary="user_roles", backref=db.backref("users", lazy="dynamic"))
    loans = db.relationship("Loan", back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name or self.username

    @property
    def initials(self):
        parts = [p for p in (self.first_name, self.last_name) if p]
        if not parts:
            return self.username[:2].upper()
        return "".join(p[0] for p in parts).upper()

    @property
    def role_names(self):
        return [r.name for r in self.roles]

    @property
    def is_staff(self):
        return self.has_roles(("admin", "bibliothecaire"))

    @property
    def active_loans(self):
        return [l for l in self.loans if l.returned_at is None]

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "roles": self.role_names,
            "active": self.active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __str__(self):
        return f"{self.full_name} ({self.username})"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    color = db.Column(db.String(7), default="#334155")

    books = db.relationship("Book", back_populates="category")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "color": self.color, "books": len(self.books)}

    def __str__(self):
        return self.name


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(150), nullable=False)
    isbn = db.Column(db.String(20), unique=True)
    year = db.Column(db.Integer)
    summary = db.Column(db.Text)
    copies = db.Column(db.Integer, nullable=False, default=1)
    cover = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    category = db.relationship("Category", back_populates="books")
    loans = db.relationship("Loan", back_populates="book", cascade="all, delete-orphan")

    @property
    def available(self):
        borrowed = sum(1 for l in self.loans if l.returned_at is None)
        return max(self.copies - borrowed, 0)

    @property
    def cover_url(self):
        return covers.url(self.cover) if self.cover else None

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "year": self.year,
            "summary": self.summary,
            "copies": self.copies,
            "available": self.available,
            "category": self.category.name if self.category else None,
            "category_id": self.category_id,
            "cover_url": self.cover_url,
            "url": url_for("api.get_book", book_id=self.id, _external=True),
        }

    def __str__(self):
        return f"{self.title} — {self.author}"


class Loan(db.Model):
    __tablename__ = "loans"

    STATUS_LABELS = {"en_cours": "En cours", "en_retard": "En retard", "rendu": "Rendu"}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id"), nullable=False)
    borrowed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    due_at = db.Column(db.DateTime, nullable=False)
    returned_at = db.Column(db.DateTime)

    user = db.relationship("User", back_populates="loans")
    book = db.relationship("Book", back_populates="loans")

    @staticmethod
    def default_due_date(start=None):
        start = start or datetime.utcnow()
        return start + timedelta(days=current_app.config["LOAN_DURATION_DAYS"])

    @property
    def status(self):
        if self.returned_at is not None:
            return "rendu"
        if self.due_at < datetime.utcnow():
            return "en_retard"
        return "en_cours"

    @property
    def status_label(self):
        return self.STATUS_LABELS[self.status]

    def to_dict(self):
        return {
            "id": self.id,
            "book": {"id": self.book.id, "title": self.book.title},
            "user": {"id": self.user.id, "username": self.user.username},
            "borrowed_at": self.borrowed_at.isoformat(),
            "due_at": self.due_at.isoformat(),
            "returned_at": self.returned_at.isoformat() if self.returned_at else None,
            "status": self.status,
        }

    def __str__(self):
        return f"#{self.id} {self.book.title} → {self.user.username}"
