from datetime import timezone
from zoneinfo import ZoneInfo

import markdown as markdown_lib

from i18n import get_lang

# Firestore est en UTC, on convertit en heure française pour l'affichage des posts
try:
    PARIS = ZoneInfo("Europe/Paris")
except Exception:
    PARIS = timezone.utc

EN_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def paris_filter(dt, fmt=None):
    """Sans format : date lisible dans la langue du visiteur. Avec un format : tel quel."""
    if dt is None:
        return ""
    local = dt.astimezone(PARIS)
    if fmt is None:
        if get_lang() == "en":
            return f"{local.day} {EN_MONTHS[local.month - 1]} {local.year}, {local:%H:%M}"
        fmt = "%d/%m/%Y à %Hh%M"
    return local.strftime(fmt)


def markdown_filter(text):
    return markdown_lib.markdown(text, extensions=["nl2br", "fenced_code", "sane_lists"])


def register_filters(app):
    app.add_template_filter(paris_filter, "paris")
    app.add_template_filter(markdown_filter, "markdown")
