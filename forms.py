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


# tâches de l'espace équipe
class TaskForm(FlaskForm):
    title = StringField("Titre", filters=[_strip], validators=[
        DataRequired("Donne un titre à la tâche."),
        Length(max=120, message="120 caractères maximum."),
    ])
    description = TextAreaField("Description (optionnelle)", filters=[_strip], validators=[
        Length(max=2000, message="2000 caractères maximum."),
    ])
    submit = SubmitField("Créer la tâche")


class MessageForm(FlaskForm):
    text = TextAreaField("Ajouter un message", filters=[_strip], validators=[
        DataRequired("Écris quelque chose avant d'envoyer."),
        Length(max=1000, message="1000 caractères maximum."),
    ])
    submit = SubmitField("Envoyer")


# création / modification d'un post
class NewPost(FlaskForm):
    title = StringField("Titre", validators=[DataRequired()])
    content = TextAreaField("Contenu", validators=[DataRequired()])
    title_en = StringField("Titre en anglais (optionnel)", filters=[_strip], validators=[
        Length(max=200, message="200 caractères maximum."),
    ])
    content_en = TextAreaField("Contenu en anglais (optionnel, Markdown possible)")
    images = MultipleFileField("Images (plusieurs possibles)",
                               validators=[FileAllowed(ALLOWED_FORMATS, "Images uniquement (jpg, png, gif, webp).")])
    submit = SubmitField("Poster")
