from flask import current_app, g, render_template, request
from markupsafe import Markup

from translations import EN

SUPPORTED = ("fr", "en")
DEFAULT = "fr"
COOKIE = "lang"
ONE_YEAR = 365 * 24 * 3600


def get_lang():
    return g.get("lang", DEFAULT)


def _(text, **values):
    """Traduit un texte écrit en français. Les {variables} sont remplacées, et les valeurs
    qui ne sont pas du HTML de confiance (Markup) sont protégées automatiquement."""
    if get_lang() == "en":
        text = EN.get(text, text)
    if values:
        return Markup(text).format(**values)
    return text


def render_localized(name, **context):
    """Rend « name.<langue>.html » s'il existe, sinon « name.html » (français)."""
    return render_template([f"{name}.{get_lang()}.html", f"{name}.html"], **context)


def _select_language():
    requested = request.args.get("lang")
    if requested in SUPPORTED:
        g.lang = requested
        g.remember_lang = True
        return
    saved = request.cookies.get(COOKIE)
    if saved in SUPPORTED:
        g.lang = saved
        return
    g.lang = request.accept_languages.best_match(SUPPORTED) or DEFAULT


def _remember_language(response):
    if g.get("remember_lang"):
        response.set_cookie(COOKIE, g.lang, max_age=ONE_YEAR, samesite="Lax",
                            secure=current_app.config.get("SESSION_COOKIE_SECURE", False))
    return response


def init_app(app):
    app.before_request(_select_language)
    app.after_request(_remember_language)
    app.context_processor(lambda: {"_": _, "lang": get_lang()})
