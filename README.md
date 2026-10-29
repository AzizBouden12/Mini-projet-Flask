# BiblioFlask — Mini-projet Flask (INGTA2-S1)

Application web de **gestion de bibliothèque** développée avec le framework **Flask** :
catalogue de livres, emprunts, comptes utilisateurs avec rôles, API REST,
téléversement de fichiers, interface d'administration et tableau de bord statistique.

> Module : Développement web avec Python · Enseignant : Mohamed Faouzi HMIDA

---

## 1. Installation et lancement

Prérequis : **Python 3.10+**

```bash
# 1. Environnement virtuel
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux / macOS

# 2. Dépendances
pip install -r requirements.txt

# 3. Lancement (la base de démonstration est créée automatiquement au 1er démarrage)
python run.py
```

Ouvrir **http://127.0.0.1:5000**

| Rôle            | Identifiant | Mot de passe |
|-----------------|-------------|--------------|
| Administrateur  | `admin`     | `Admin123`   |
| Bibliothécaire  | `biblio`    | `Biblio123`  |
| Membre          | `membre`    | `Membre123`  |

Réinitialiser la base :

```bash
flask --app run seed            # réinitialise la base de démonstration
```

Lancement en **HTTPS** (certificat auto-signé) : `set SSL=1` (Windows) ou `export SSL=1`, puis `python run.py`
→ https://127.0.0.1:5000. Ajouter `FORCE_HTTPS=1` pour rediriger HTTP vers HTTPS et activer cookies `Secure` + HSTS.

---

## 2. Correspondance avec l'énoncé

| Exigence | Réalisation | Fichiers |
|---|---|---|
| **API REST** pour accéder aux données | API JSON v1 : livres (CRUD complet), catégories, emprunts, statistiques, jetons | `app/api/routes.py` |
| **Fichiers statiques** | CSS, JS, logo SVG servis depuis `app/static` via `url_for('static', …)` ; favicon servi avec `send_from_directory` ; fichiers téléversés servis par Flask-Uploads (`/_uploads/…`) | `app/static/`, `app/main/routes.py` |
| **Rendus de modèles Jinja2** | Héritage (`base.html`), macros (`_macros.html`), filtres personnalisés (`date_fr`, `fr`, `plural`), `context_processor`, boucles/conditions, `tojson`, surcharge des templates Flask-User et Flask-Admin | `app/templates/`, `app/__init__.py` |
| **Émissions de redirections** | Post/Redirect/Get après chaque formulaire, `302` (`/accueil`), `301` permanente (`/catalog`, `/books`), `303` (`/isbn/<isbn>`), redirection vers la connexion avec `?next=`, HTTP → HTTPS | `app/main/routes.py`, `app/security.py` |
| **Téléchargements de fichiers avec Flask-Uploads** | `UploadSet` des couvertures de livres (images) : liste blanche d'extensions, nom aléatoire (uuid), limite 5 Mo (erreur 413). Upload depuis le site, l'API (multipart) et Flask-Admin | `app/extensions.py`, `app/services.py`, `app/forms.py` |
| **Sécurité des échanges HTTP** | En-têtes CSP avec nonce, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, HSTS, `Cache-Control: no-store` sur l'API ; cookies HttpOnly / SameSite / Secure ; HTTPS (TLS) | `app/security.py`, `config.py`, `run.py` |
| **Plusieurs modes de sécurisation** | 1) session Flask-Login/Flask-User 2) rôles (RBAC) 3) CSRF Flask-WTF 4) HTTP Basic 5) jeton Bearer signé et expirant 6) en-têtes HTTP 7) HTTPS + HSTS | `app/security.py` |
| **Sessions avec Flask-Login et Flask-User** | Inscription, connexion, déconnexion, changement de mot de passe, mots de passe hachés bcrypt, `@login_required` | `app/__init__.py`, `app/models.py`, `app/templates/flask_user/` |
| **Rôles + Flask-Admin** | Rôles `admin`, `bibliothecaire`, `membre` (`@roles_required`). Flask-Admin : livres (avec upload), catégories, emprunts (badges d'état), utilisateurs (hachage du mot de passe), rôles — accès filtré par rôle, formulaires protégés par CSRF, interface en français | `app/admin.py` |
| **Dashboard ergonomique avec statistiques et états** | Indicateurs clés, courbe emprunts/retours par mois, anneau des états, barres par catégorie, top 5, comptes par rôle, liste des emprunts filtrable par état | `app/dashboard/`, `app/static/js/dashboard.js` |

---

## 3. Structure du projet

```
mini-projet-flask/
├── run.py                  # point d'entrée (HTTP ou HTTPS)
├── config.py               # configuration (sécurité, uploads, Flask-User…)
├── requirements.txt
├── app/
│   ├── __init__.py         # fabrique create_app : extensions, blueprints, filtres, erreurs
│   ├── extensions.py       # SQLAlchemy, CSRF, Mail, UploadSets Flask-Uploads
│   ├── models.py           # User, Role, UserRoles, Category, Book, Loan
│   ├── security.py         # en-têtes HTTP, HTTPS, Basic, Bearer, rôles API
│   ├── services.py         # logique métier : emprunts, uploads, statistiques
│   ├── forms.py            # formulaires Flask-WTF (CSRF + validation des fichiers)
│   ├── admin.py            # Flask-Admin sécurisé par rôles
│   ├── i18n.py             # traduction française des messages Flask-User
│   ├── cli.py              # commande flask seed
│   ├── main/               # pages HTML (accueil, catalogue, livres, redirections)
│   ├── api/                # API REST /api/v1
│   ├── dashboard/          # tableau de bord
│   ├── templates/          # gabarits Jinja2
│   └── static/             # css/style.css, js/app.js, js/dashboard.js, img/logo.svg
└── instance/               # base SQLite + fichiers téléversés (créé au lancement)
```

---

## 4. Exemples d'appels à l'API

```bash
# Jeton (HTTP Basic -> Bearer)
curl -X POST -u biblio:Biblio123 http://127.0.0.1:5000/api/v1/auth/token

# Liste publique paginée
curl "http://127.0.0.1:5000/api/v1/books?q=camus&page=1"

# Création (rôle bibliothécaire requis)
curl -X POST http://127.0.0.1:5000/api/v1/books -H "Authorization: Bearer <jeton>" \
     -H "Content-Type: application/json" -d "{\"title\":\"Le Horla\",\"author\":\"Maupassant\",\"category_id\":1}"

# Téléversement d'une couverture
curl -X POST http://127.0.0.1:5000/api/v1/books/1/cover -H "Authorization: Bearer <jeton>" -F "file=@couverture.jpg"

# Emprunts en retard
curl -u admin:Admin123 "http://127.0.0.1:5000/api/v1/loans?status=en_retard"
```

---

## 5. Remarques techniques

- **Flask-User 1.0.2.2** n'est plus maintenu (ses versions sont retirées de PyPI) : il est installé en
  version épinglée et reste compatible avec Flask 3. `bcrypt` est épinglé en 4.0.1 pour `passlib`.
- **Flask-Reuploaded** est le fork maintenu de Flask-Uploads (même module `flask_uploads`), l'original
  étant incompatible avec Werkzeug ≥ 1.0.
- Le cookie de session n'est accepté par l'API **qu'en lecture** : toute écriture exige un en-tête
  `Authorization`, ce qui protège l'API contre les attaques CSRF sans jeton de formulaire.
- En production : définir `SECRET_KEY`, activer `FORCE_HTTPS=1` et utiliser un serveur WSGI (gunicorn, waitress).
