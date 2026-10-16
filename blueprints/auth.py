import hashlib
import hmac
import os
from functools import wraps
from urllib.parse import urlparse

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import (UserMixin, current_user, login_required, login_user,
                         logout_user)
from werkzeug.security import check_password_hash, generate_password_hash

from data import create_user, get_user, get_user_by_username, users_exist
from extensions import login_manager
from forms import LoginForm

bp = Blueprint("auth", __name__)

# Vérifié aussi quand l'identifiant n'existe pas : le temps de réponse ne révèle
# pas quels identifiants sont valides.
DUMMY_HASH = generate_password_hash("mot-de-passe-factice")

class AuthUser(UserMixin):
    def __init__(self, doc):
        self.id = doc["id"]
        self.username = doc["username"]
        self.role = doc.get("role", "member")
        self.password_hash = doc["password_hash"]
        self.must_change_password = doc.get("must_change_password", False)

    @property
    def is_admin(self):
        return self.role == "admin"

    def get_id(self):
        # id + empreinte du hash : changer de mot de passe invalide les autres sessions
        fingerprint = hashlib.sha256(self.password_hash.encode()).hexdigest()[:16]
        return f"{self.id}.{fingerprint}"

@login_manager.user_loader
def load_user(session_id):
    user_id = session_id.partition(".")[0]
    doc = get_user(user_id)
    if doc is None:
        return None
    user = AuthUser(doc)
    return user if user.get_id() == session_id else None

def admin_required(view):
    """Connecté ET admin. @login_required seul laisserait entrer les membres."""
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)
    return login_required(wrapper)

def _safe_next(target):
    """N'accepte que des chemins relatifs du site (évite les redirections vers l'extérieur)."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\" in target:
        return None
    parsed = urlparse(target)
    return None if parsed.scheme or parsed.netloc else target

def _authenticate(username, password):
    doc = get_user_by_username(username)
    if doc is not None:
        if check_password_hash(doc["password_hash"], password):
            return AuthUser(doc)
        return None
    check_password_hash(DUMMY_HASH, password)

    # Premier lancement : aucun compte en base, on crée l'admin à partir de la
    # variable d'environnement PASSWORD (identifiant « admin »).
    if not users_exist():
        expected = os.environ.get("PASSWORD")
        if (expected and username.lower() == "admin"
                and hmac.compare_digest(password.encode(), expected.encode())):
            new_id = create_user("admin", generate_password_hash(password), role="admin")
            return AuthUser(get_user(new_id))
    return None

@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("team.dashboard"))
    form = LoginForm()
    error = None
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        form.password.data = ""
        user = _authenticate(username, password)
        if user is not None:
            login_user(user)
            return redirect(_safe_next(request.args.get("next")) or url_for("team.dashboard"))
        error = "Identifiant ou mot de passe incorrect."
    return render_template("login.html", title="Connexion", form=form, error=error)

@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

# Pages accessibles même quand le compte doit d'abord changer son mot de passe.
# On les teste AVANT de toucher à current_user : les fichiers statiques et les images
# ne déclenchent ainsi aucune lecture Firestore.
_EXEMPT = {None, "static", "public.serve_image", "account.account",
           "account.change_password", "auth.logout"}

@bp.before_app_request
def force_password_change():
    if request.endpoint in _EXEMPT:
        return None
    if current_user.is_authenticated and current_user.must_change_password:
        flash("Choisis un nouveau mot de passe pour continuer.", "error")
        return redirect(url_for("account.account"))
    return None
