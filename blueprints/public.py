import re

from flask import Blueprint, Response, abort, render_template

from data import get_posts, increment_views, load_image

bp = Blueprint("public", __name__)


@bp.route("/")
def home():
    increment_views()
    return render_template("home.html", title="Bienvenue sur le site de la DD Corp !")


@bp.route("/equipe")
def equipe():
    return render_template("equipe.html", title="Équipe")


@bp.route("/récompenses")
def recompenses():
    return render_template("recompenses.html", title="Récompenses")


@bp.route("/projet")
def projet():
    return render_template("projet.html", title="Projets")


@bp.route("/robot")
def robot():
    return render_template("robot.html", title="Robot Game")


@bp.route("/actus")
def actus():
    return render_template("actus.html", title="Actualités", posts=get_posts(limit=20))


@bp.route("/projet/vestige")
def vestige():
    return render_template("vestige.html", title="Vestige")


@bp.route("/projet/hydrache")
def hydrache():
    return render_template("hydrache.html", title="Hydra'che")


@bp.route("/contact")
def formulaire():
    return render_template("formulaire.html", title="Contact")


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
