import random
from datetime import datetime, timedelta

import click

from .extensions import db
from .models import Book, Category, Loan, Role, User

CATEGORIES = [
    ("Roman", "#2563EB"), ("Science-fiction", "#7C3AED"), ("Informatique", "#0891B2"),
    ("Histoire", "#B45309"), ("Philosophie", "#BE185D"), ("Jeunesse", "#16A34A"),
]

BOOKS = [
    ("L'Étranger", "Albert Camus", 1942, "Roman", "9782070360024",
     "Meursault, employé de bureau à Alger, assiste à l'enterrement de sa mère sans manifester d'émotion…"),
    ("Le Petit Prince", "Antoine de Saint-Exupéry", 1943, "Jeunesse", "9782070612758",
     "Un aviateur tombé en panne dans le désert rencontre un petit prince venu d'une autre planète."),
    ("Les Misérables", "Victor Hugo", 1862, "Roman", "9782253096344",
     "Le destin de Jean Valjean, ancien forçat, dans la France du XIXe siècle."),
    ("Madame Bovary", "Gustave Flaubert", 1857, "Roman", "9782070413119",
     "Emma Bovary rêve d'une vie romanesque loin de la monotonie provinciale."),
    ("Germinal", "Émile Zola", 1885, "Roman", "9782253004226",
     "La grève des mineurs du Nord vue à travers les yeux d'Étienne Lantier."),
    ("Le Rouge et le Noir", "Stendhal", 1830, "Roman", "9782253006206",
     "L'ascension et la chute de Julien Sorel, jeune ambitieux sous la Restauration."),
    ("Dune", "Frank Herbert", 1965, "Science-fiction", "9782266320481",
     "Sur la planète désertique Arrakis, Paul Atréides affronte son destin."),
    ("Fondation", "Isaac Asimov", 1951, "Science-fiction", "9782070360536",
     "Hari Seldon prédit la chute de l'Empire galactique et fonde une communauté pour en abréger les ténèbres."),
    ("1984", "George Orwell", 1949, "Science-fiction", "9782070368228",
     "Winston Smith tente de résister à Big Brother dans un État totalitaire."),
    ("Le Meilleur des mondes", "Aldous Huxley", 1932, "Science-fiction", "9782266283038",
     "Une société où le bonheur est fabriqué en série."),
    ("Clean Code", "Robert C. Martin", 2008, "Informatique", "9780132350884",
     "Principes et bonnes pratiques pour écrire un code lisible et maintenable."),
    ("Flask Web Development", "Miguel Grinberg", 2018, "Informatique", "9781491991732",
     "Développer des applications web avec Python et le micro-framework Flask."),
    ("Apprendre à programmer avec Python 3", "Gérard Swinnen", 2012, "Informatique", "9782212134346",
     "Une initiation progressive à la programmation avec Python."),
    ("The Pragmatic Programmer", "Andrew Hunt & David Thomas", 1999, "Informatique", "9780201616224",
     "Conseils pratiques pour progresser dans le métier de développeur."),
    ("Design Patterns", "Erich Gamma et al.", 1994, "Informatique", "9780201633610",
     "Le catalogue de référence des patrons de conception orientés objet."),
    ("Sapiens", "Yuval Noah Harari", 2011, "Histoire", "9782226257017",
     "Une brève histoire de l'humanité, de la préhistoire à nos jours."),
    ("Histoire de Carthage", "Serge Lancel", 1992, "Histoire", "9782213028064",
     "Grandeur et chute de la cité punique fondée sur les côtes de l'actuelle Tunisie."),
    ("Les Rois maudits", "Maurice Druon", 1955, "Histoire", "9782253004011",
     "La malédiction des Templiers frappe la dynastie des Capétiens."),
    ("La Muqaddima", "Ibn Khaldoun", 1377, "Histoire", "9782742788859",
     "Introduction à l'histoire universelle par le penseur tunisien."),
    ("Le Mythe de Sisyphe", "Albert Camus", 1942, "Philosophie", "9782070322886",
     "Un essai sur l'absurde et la révolte."),
    ("Ainsi parlait Zarathoustra", "Friedrich Nietzsche", 1885, "Philosophie", "9782253005216",
     "Un poème philosophique sur le surhomme et l'éternel retour."),
    ("Discours de la méthode", "René Descartes", 1637, "Philosophie", "9782080712981",
     "Pour bien conduire sa raison et chercher la vérité dans les sciences."),
    ("Harry Potter à l'école des sorciers", "J. K. Rowling", 1997, "Jeunesse", "9782070584628",
     "Le jeune Harry découvre qu'il est un sorcier et entre à Poudlard."),
    ("Le Lion", "Joseph Kessel", 1958, "Jeunesse", "9782070367269",
     "Au Kenya, l'amitié d'une petite fille et d'un lion."),
]

MEMBERS = [
    ("sarra", "Sarra", "Ben Ali"), ("youssef", "Youssef", "Trabelsi"), ("ines", "Inès", "Gharbi"),
    ("amine", "Amine", "Jaziri"), ("lina", "Lina", "Mansouri"), ("omar", "Omar", "Khelifi"),
    ("nour", "Nour", "Bouazizi"), ("karim", "Karim", "Hamdi"),
]


def _user(um, username, email, password, first, last, roles, created_days_ago=0):
    user = User(username=username, email=email, password=um.hash_password(password),
                first_name=first, last_name=last, active=True,
                email_confirmed_at=datetime.utcnow(),
                created_at=datetime.utcnow() - timedelta(days=created_days_ago))
    user.roles = roles
    db.session.add(user)
    return user


def seed_database(app):
    um = app.user_manager
    rnd = random.Random(42)

    db.drop_all()
    db.create_all()

    admin_r = Role(name="admin", label="Administrateur")
    lib_r = Role(name="bibliothecaire", label="Bibliothécaire")
    mem_r = Role(name="membre", label="Membre")
    db.session.add_all([admin_r, lib_r, mem_r])

    _user(um, "admin", "admin@biblioflask.local", "Admin123", "Amira", "Haddad", [admin_r], 200)
    _user(um, "biblio", "biblio@biblioflask.local", "Biblio123", "Mehdi", "Saidi", [lib_r], 180)
    members = [_user(um, "membre", "membre@biblioflask.local", "Membre123", "Rania", "Chaabane", [mem_r], 150)]
    for i, (u, first, last) in enumerate(MEMBERS):
        members.append(_user(um, u, f"{u}@exemple.tn", "Membre123", first, last, [mem_r],
                             rnd.randint(0, 170) if i else 12))

    cats = {name: Category(name=name, color=color) for name, color in CATEGORIES}
    db.session.add_all(cats.values())

    books = []
    now = datetime.utcnow()
    for i, (title, author, year, cat, isbn, summary) in enumerate(BOOKS):
        b = Book(title=title, author=author, year=year, category=cats[cat], isbn=isbn, summary=summary,
                 copies=rnd.randint(2, 5), created_at=now - timedelta(days=len(BOOKS) - i))
        books.append(b)
    db.session.add_all(books)
    db.session.flush()

    for _ in range(95):
        user, book = rnd.choice(members), rnd.choice(books)
        start = now - timedelta(days=rnd.randint(1, 175), hours=rnd.randint(0, 23))
        due = start + timedelta(days=14)
        returned = None
        if start < now - timedelta(days=16) or rnd.random() < 0.35:
            returned = start + timedelta(days=rnd.randint(2, 18))
            if returned > now:
                returned = None
        if returned is None and (book.available <= 0 or len(user.active_loans) >= 3
                                 or any(l.book_id == book.id for l in user.active_loans)):
            continue
        db.session.add(Loan(user=user, book=book, borrowed_at=start, due_at=due, returned_at=returned))
        db.session.flush()

    db.session.commit()


def register_cli(app):
    @app.cli.command("seed")
    def seed():
        seed_database(app)
        click.echo("Base initialisée : admin/Admin123 · biblio/Biblio123 · membre/Membre123")
