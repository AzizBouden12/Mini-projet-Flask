from flask import render_template, request
from flask_user import roles_required

from ..models import Loan
from ..services import compute_stats
from . import bp

STAFF = ["admin", "bibliothecaire"]


def _filtered_loans(status):
    loans = Loan.query.order_by(Loan.borrowed_at.desc()).all()
    if status in Loan.STATUS_LABELS:
        loans = [l for l in loans if l.status == status]
    return loans


@bp.route("/")
@roles_required(STAFF)
def index():
    status = request.args.get("etat", "")
    loans = _filtered_loans(status)
    return render_template("dashboard/index.html", stats=compute_stats(), loans=loans,
                           status=status, labels=Loan.STATUS_LABELS)
