from datetime import timezone
from zoneinfo import ZoneInfo

import markdown as markdown_lib

# Firestore est en UTC, on convertit en heure française pour l'affichage des posts
try:
    PARIS = ZoneInfo("Europe/Paris")
except Exception:
    PARIS = timezone.utc


def paris_filter(dt, fmt="%d/%m/%Y à %Hh%M"):
    if dt is None:
        return ""
    return dt.astimezone(PARIS).strftime(fmt)


def markdown_filter(text):
    return markdown_lib.markdown(text, extensions=["nl2br", "fenced_code", "sane_lists"])


def register_filters(app):
    app.add_template_filter(paris_filter, "paris")
    app.add_template_filter(markdown_filter, "markdown")
