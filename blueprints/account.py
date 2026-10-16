from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user
from werkzeug.security import check_password_hash, generate_password_hash

from blueprints.auth import AuthUser
from data import get_user, update_user, username_taken
from forms import PasswordForm, UsernameForm

bp = Blueprint("account", __name__)

def _render(username_form=None, password_form=None):
    if username_form is None:
        username_form = UsernameForm()
        username_form.username.data = current_user.username
    if password_form is None:
        password_form = PasswordForm()
    return render_template("account.html", title="Mon compte",
                           username_form=username_form, password_form=password_form)

@bp.route("/compte")
@login_required
def account():
    return _render()

@bp.route("/compte/identifiant", methods=["POST"])
@login_required
def change_username():
    form = UsernameForm()
    if form.validate_on_submit():
        new_name = form.username.data
        if username_taken(new_name, exclude_id=current_user.id):
            form.username.errors.append("Cet identifiant est déjà utilisé.")
        else:
            update_user(current_user.id, username=new_name, username_lower=new_name.lower())
            flash("Identifiant mis à jour.", "success")
            return redirect(url_for("account.account"))
    return _render(username_form=form)

@bp.route("/compte/mot-de-passe", methods=["POST"])
@login_required
def change_password():
    form = PasswordForm()
    if form.validate_on_submit():
        user_id = current_user.id
        doc = get_user(user_id)
        if not check_password_hash(doc["password_hash"], form.current_password.data):
            form.current_password.errors.append("Mot de passe actuel incorrect.")
        elif check_password_hash(doc["password_hash"], form.new_password.data):
            form.new_password.errors.append("Le nouveau mot de passe doit être différent de l'ancien.")
        else:
            update_user(user_id,
                        password_hash=generate_password_hash(form.new_password.data),
                        must_change_password=False)
            # le hash a changé : on rouvre la session de cet appareil (les autres sont déconnectés)
            login_user(AuthUser(get_user(user_id)))
            flash("Mot de passe mis à jour.", "success")
            return redirect(url_for("account.account"))
    return _render(password_form=form)
