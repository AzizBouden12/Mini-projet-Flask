import uuid
from collections import Counter, OrderedDict
from datetime import datetime, timedelta

from flask import current_app
from sqlalchemy import func

from .extensions import db
from .models import Book, Category, Loan, Role, User

MONTHS_FR = ["janv.", "févr.", "mars", "avr.", "mai", "juin",
             "juil.", "août", "sept.", "oct.", "nov.", "déc."]


class BusinessError(Exception):
    pass


def save_upload(upload_set, storage):
    return upload_set.save(storage, name=f"{uuid.uuid4().hex}.")


def borrow_book(user, book):
    if book.available <= 0:
        raise BusinessError("Aucun exemplaire disponible pour le moment.")
    if any(l.book_id == book.id for l in user.active_loans):
        raise BusinessError("Vous avez déjà emprunté ce livre.")
    if len(user.active_loans) >= current_app.config["MAX_ACTIVE_LOANS"]:
        raise BusinessError(
            f"Limite atteinte : {current_app.config['MAX_ACTIVE_LOANS']} emprunts simultanés maximum."
        )
    loan = Loan(user=user, book=book, borrowed_at=datetime.utcnow(), due_at=Loan.default_due_date())
    db.session.add(loan)
    db.session.commit()
    return loan


def return_loan(loan):
    if loan.returned_at is not None:
        raise BusinessError("Cet emprunt a déjà été rendu.")
    loan.returned_at = datetime.utcnow()
    db.session.commit()
    return loan


def compute_stats(months=6):
    now = datetime.utcnow()
    loans = Loan.query.all()

    status_counts = Counter(l.status for l in loans)
    active = status_counts["en_cours"] + status_counts["en_retard"]
    total_copies = db.session.query(func.coalesce(func.sum(Book.copies), 0)).scalar()

    per_month = OrderedDict()
    y, m = now.year, now.month
    keys = []
    for _ in range(months):
        keys.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    for y, m in reversed(keys):
        per_month[(y, m)] = {"label": f"{MONTHS_FR[m - 1]} {str(y)[2:]}", "borrowed": 0, "returned": 0}
    for l in loans:
        k = (l.borrowed_at.year, l.borrowed_at.month)
        if k in per_month:
            per_month[k]["borrowed"] += 1
        if l.returned_at:
            k = (l.returned_at.year, l.returned_at.month)
            if k in per_month:
                per_month[k]["returned"] += 1

    categories = []
    for c in Category.query.order_by(Category.name).all():
        categories.append({
            "name": c.name,
            "color": c.color,
            "books": len(c.books),
            "loans": sum(len(b.loans) for b in c.books),
        })

    top_rows = (
        db.session.query(Book, func.count(Loan.id).label("n"))
        .join(Loan, Loan.book_id == Book.id)
        .group_by(Book.id)
        .order_by(func.count(Loan.id).desc(), Book.title)
        .limit(5)
        .all()
    )
    top_books = [{"id": b.id, "title": b.title, "author": b.author, "loans": n} for b, n in top_rows]

    roles = [{"name": r.label or r.name, "count": r.users.count()} for r in Role.query.order_by(Role.id).all()]

    occupancy = round(active * 100 / total_copies, 1) if total_copies else 0.0
    returned = [l for l in loans if l.returned_at]
    on_time = sum(1 for l in returned if l.returned_at <= l.due_at)
    on_time_rate = round(on_time * 100 / len(returned), 1) if returned else 100.0

    new_members = User.query.filter(User.created_at >= now - timedelta(days=30)).count()

    return {
        "generated_at": now.isoformat(timespec="seconds"),
        "kpis": {
            "books": Book.query.count(),
            "copies": int(total_copies),
            "members": User.query.count(),
            "new_members_30d": new_members,
            "active_loans": active,
            "overdue_loans": status_counts["en_retard"],
            "returned_loans": status_counts["rendu"],
            "total_loans": len(loans),
            "occupancy_rate": occupancy,
            "on_time_rate": on_time_rate,
        },
        "loans_by_status": {
            "en_cours": status_counts["en_cours"],
            "en_retard": status_counts["en_retard"],
            "rendu": status_counts["rendu"],
        },
        "loans_per_month": list(per_month.values()),
        "categories": categories,
        "top_books": top_books,
        "roles": roles,
    }
