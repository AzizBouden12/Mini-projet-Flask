import os

from app import create_app
from app.cli import seed_database
from app.models import User

app = create_app()

with app.app_context():
    if User.query.count() == 0:
        seed_database(app)
        print("Base de démonstration créée (admin/Admin123, biblio/Biblio123, membre/Membre123)")

if __name__ == "__main__":
    use_ssl = os.environ.get("SSL") == "1"
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", 5000)),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
        ssl_context="adhoc" if use_ssl else None,
    )
