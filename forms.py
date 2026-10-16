from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import (PasswordField, SelectField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import DataRequired, EqualTo, Length, Regexp

from data import ALLOWED_FORMATS


def _strip(value):
    return value.strip() if isinstance(value, str) else value


def _username_field(label):
    return StringField(label, filters=[_strip], validators=[
        DataRequired("Choisis un identifiant."),
        Length(min=3, max=30, message="L'identifiant doit faire entre 3 et 30 caractères."),
        Regexp(r"^[A-Za-z0-9_.-]+$", message="Lettres, chiffres, point, tiret et underscore uniquement."),
    ])


# connexion (identifiant + mot de passe)
class LoginForm(FlaskForm):
    username = StringField("Identifiant", filters=[_strip], validators=[DataRequired()])
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField("Connexion")


# page « Mon compte »
class UsernameForm(FlaskForm):
    username = _username_field("Nouvel identifiant")
    submit_username = SubmitField("Changer l'identifiant")


class PasswordForm(FlaskForm):
    current_password = PasswordField("Mot de passe actuel", validators=[DataRequired()])
    new_password = PasswordField("Nouveau mot de passe", validators=[
        DataRequired(),
        Length(min=8, message="Le mot de passe doit faire au moins 8 caractères."),
    ])
    confirm = PasswordField("Confirmer le nouveau mot de passe", validators=[
        DataRequired(),
        EqualTo("new_password", message="Les deux mots de passe ne correspondent pas."),
    ])
    submit_password = SubmitField("Changer le mot de passe")


# création d'un compte par l'admin
class NewUserForm(FlaskForm):
    username = _username_field("Identifiant")
    role = SelectField("Rôle", choices=[("member", "Membre"), ("admin", "Admin")])
    submit = SubmitField("Créer le compte")


# création / modification d'un post
class NewPost(FlaskForm):
    title = StringField("Titre", validators=[DataRequired()])
    content = TextAreaField("Contenu", validators=[DataRequired()])
    images = MultipleFileField("Images (plusieurs possibles)",
                               validators=[FileAllowed(ALLOWED_FORMATS, "Images uniquement (jpg, png, gif, webp).")])
    submit = SubmitField("Poster")
