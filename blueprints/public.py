import re

from flask import Blueprint, Response, abort, render_template

from data import get_posts, increment_views, load_image
from i18n import _, render_localized

bp = Blueprint("public", __name__)


@bp.route("/")
def home():
    increment_views()
    return render_template("home.html", title=_("Bienvenue sur le site de la DD Corp !"))


# Pages longues : equipe.html (français) / equipe.en.html (anglais)
@bp.route("/equipe")
def equipe():
    return render_localized("equipe", title=_("Équipe"))


@bp.route("/récompenses")
def recompenses():
    return render_localized("recompenses", title=_("Récompenses"))


@bp.route("/projet")
def projet():
    return render_template("projet.html", title=_("Projets"))


@bp.route("/robot")
def robot():
    return render_localized("robot", title="Robot Game")


@bp.route("/actus")
def actus():
    return render_template("actus.html", title=_("Actualités"), posts=get_posts(limit=20))


@bp.route("/projet/vestige")
def vestige():
    return render_localized("vestige", title="Vestige")


@bp.route("/projet/hydrache")
def hydrache():
    return render_localized("hydrache", title="Hydra'che")


@bp.route("/contact")
def formulaire():
    return render_template("formulaire.html", title=_("Contact"))


# adresse appelée régulièrement par le service de « ping » (garde le site éveillé) :
# ne touche ni au compteur de vues ni à la base de données
@bp.route("/health")
def health():
    return "ok"


@bp.route("/img/<image_id>")
def serve_image(image_id):
    if not re.fullmatch(r"[A-Za-z0-9]{20}", image_id):
        abort(404)
    found = load_image(image_id)
    if found is None:
        abort(404)
    data, content_type = found
    resp = Response(data, mimetype=content_type)
    resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return resp
