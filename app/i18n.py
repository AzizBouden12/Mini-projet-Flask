import re

_EXACT = {
    "You have signed in successfully.": "Connexion réussie. Bienvenue !",
    "You have signed out successfully.": "Vous êtes déconnecté. À bientôt !",
    "You have registered successfully.": "Votre compte a été créé avec succès.",
    "Your password has been changed successfully.": "Votre mot de passe a été modifié.",
    "Your account has not been enabled.": "Votre compte est désactivé. Contactez un administrateur.",
    "Incorrect Username/Email and/or Password": "Identifiant ou mot de passe incorrect.",
    "Incorrect Username and/or Password": "Identifiant ou mot de passe incorrect.",
    "Incorrect Email and/or Password": "E-mail ou mot de passe incorrect.",
    "Incorrect Password": "Mot de passe incorrect.",
    "Old Password is incorrect": "L'ancien mot de passe est incorrect.",
    "This Username is already in use. Please try another one.": "Ce nom d'utilisateur est déjà pris.",
    "This Email is already in use. Please try another one.": "Cette adresse e-mail est déjà utilisée.",
    "Invalid Email": "Adresse e-mail invalide.",
    "Email is required": "L'adresse e-mail est obligatoire.",
    "Username is required": "Le nom d'utilisateur est obligatoire.",
    "Username or Email is required": "Saisissez votre identifiant ou votre e-mail.",
    "Password is required": "Le mot de passe est obligatoire.",
    "New Password is required": "Le nouveau mot de passe est obligatoire.",
    "Old Password is required": "L'ancien mot de passe est obligatoire.",
    "Password and Retype Password did not match": "Les deux mots de passe ne correspondent pas.",
    "New Password and Retype Password did not match": "Les deux mots de passe ne correspondent pas.",
    "Password must have at least 6 characters with one lowercase letter, one uppercase letter and one number":
        "Le mot de passe doit contenir au moins 6 caractères dont une minuscule, une majuscule et un chiffre.",
    "Username must be at least 3 characters long": "Le nom d'utilisateur doit contenir au moins 3 caractères.",
    "Username may only contain letters, numbers, '-', '.' and '_'":
        "Le nom d'utilisateur ne peut contenir que des lettres, chiffres, « - », « . » et « _ ».",
    "The CSRF token is missing.": "Jeton CSRF manquant : rechargez la page.",
    "The CSRF token has expired.": "Le formulaire a expiré : rechargez la page.",
    "The CSRF token is invalid.": "Jeton CSRF invalide : rechargez la page.",
    "This field is required.": "Ce champ est obligatoire.",
}

_PATTERNS = [
    (re.compile(r"^You must be signed in to access '(.+)'\.$"),
     "Vous devez être connecté pour accéder à cette page."),
    (re.compile(r"^You do not have permission to access '(.+)'\.$"),
     "Vous n'avez pas les droits nécessaires pour accéder à « {0} »."),
]


def translate(message):
    text = str(message)
    if text in _EXACT:
        return _EXACT[text]
    for pattern, template in _PATTERNS:
        match = pattern.match(text)
        if match:
            return template.format(*match.groups())
    return text
