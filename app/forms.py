from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import IntegerField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp

from .extensions import covers


class BookForm(FlaskForm):
    title = StringField("Titre", validators=[DataRequired("Le titre est obligatoire."), Length(max=200)])
    author = StringField("Auteur", validators=[DataRequired("L'auteur est obligatoire."), Length(max=150)])
    isbn = StringField(
        "ISBN",
        validators=[Optional(), Regexp(r"^[0-9Xx-]{10,17}$", message="ISBN invalide (10 ou 13 chiffres).")],
    )
    year = IntegerField(
        "Année de parution",
        validators=[Optional(), NumberRange(min=1000, max=2100, message="Année entre 1000 et 2100.")],
    )
    category_id = SelectField("Catégorie", coerce=int, validators=[DataRequired("Choisissez une catégorie.")])
    copies = IntegerField(
        "Exemplaires",
        default=1,
        validators=[DataRequired("Indiquez le nombre d'exemplaires."), NumberRange(min=1, max=500)],
    )
    summary = TextAreaField("Résumé", validators=[Optional(), Length(max=3000)])
    cover = FileField(
        "Couverture (image)",
        validators=[FileAllowed(covers, "Formats acceptés : jpg, jpeg, png, gif, webp, bmp.")],
    )
    submit = SubmitField("Enregistrer")


class ConfirmForm(FlaskForm):
    submit = SubmitField("Confirmer")
