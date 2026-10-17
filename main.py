import os

from flask import Flask, render_template

# extensions doit rester le premier import local : il charge le .env
from extensions import csrf, login_manager
from data import get_views
import i18n
from i18n import _
from filters import register_filters
from blueprints.public import bp as public_bp
from blueprints.admin import bp as admin_bp
from blueprints.auth import bp as auth_bp
from blueprints.account import bp as account_bp
from blueprints.team import bp as team_bp

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# taille maximale d'une requête
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

# cookies de session : COOKIE_SECURE=1 en production (https), à laisser vide en local (http)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = os.environ.get("COOKIE_SECURE") == "1"

csrf.init_app(app)
login_manager.init_app(app)
register_filters(app)
i18n.init_app(app)

app.register_blueprint(public_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(account_bp)
app.register_blueprint(team_bp)


@app.errorhandler(403)
def forbidden(e):
    return render_template("404.html", title=_("Accès refusé"),
                           message=_("Tu n'as pas la permission d'accéder à cette page.")), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title=_("Page Introuvable")), 404


@app.errorhandler(413)
def too_large(e):
    return render_template("404.html", title=_("Fichiers trop lourds"),
                           message=_("Les fichiers envoyés sont trop lourds (32 Mo maximum au total). Reviens en arrière et réessaie avec moins d'images ou des images plus légères.")), 413


@app.context_processor
def inject_views():
    return {"views": get_views()}


if __name__ == "__main__":
    app.run()
