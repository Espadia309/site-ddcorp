from datetime import datetime, timezone

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user, login_required

from data import (TASK_STATUSES, add_message, create_task, delete_task,
                  edit_task, get_task, list_messages, list_tasks, list_users,
                  set_task_status)
from filters import PARIS
from forms import MessageForm, TaskForm
from team_config import COMPETITIONS

bp = Blueprint("team", __name__)

EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
DONE_VISIBLE = 10  # nombre de tâches « Fait » affichées par défaut

def _names():
    """id -> nom actuel : si quelqu'un change d'identifiant, ses tâches suivent."""
    return {u["id"]: u["username"] for u in list_users()}

def _get_task(task_id):
    task = get_task(task_id)
    if task is None:
        abort(404)
    return task

def _can_delete(task):
    return current_user.is_admin or task.get("created_by") == current_user.id

def _upcoming():
    now = datetime.now(PARIS)
    items = []
    for name, when in COMPETITIONS:
        if when.tzinfo is None:
            when = when.replace(tzinfo=PARIS)
        if when > now:
            items.append((name, when))
    return sorted(items, key=lambda item: item[1])

def _countdown(name, when):
    seconds = max(0, int((when - datetime.now(PARIS)).total_seconds()))
    days, rest = divmod(seconds, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    return {"name": name, "iso": when.isoformat(), "date": when,
            "days": days, "hours": hours, "minutes": minutes, "seconds": secs}

@bp.route("/espace-equipe")
@login_required
def dashboard():
    upcoming = _upcoming()
    countdown = _countdown(*upcoming[0]) if upcoming else None

    by_status = {status: [] for status in TASK_STATUSES}
    for task in list_tasks():
        by_status.get(task.get("status"), by_status["a_faire"]).append(task)
    counts = {status: len(tasks) for status, tasks in by_status.items()}

    by_status["fait"].sort(key=lambda t: t.get("updated_at") or EPOCH, reverse=True)
    hidden_done = 0
    if request.args.get("all") != "1" and len(by_status["fait"]) > DONE_VISIBLE:
        hidden_done = len(by_status["fait"]) - DONE_VISIBLE
        by_status["fait"] = by_status["fait"][:DONE_VISIBLE]

    return render_template("team.html", title="Espace équipe",
                           countdown=countdown, later=upcoming[1:4],
                           by_status=by_status, counts=counts, hidden_done=hidden_done,
                           statuses=TASK_STATUSES, names=_names())

@bp.route("/espace-equipe/taches/nouvelle", methods=["GET", "POST"])
@login_required
def new_task():
    form = TaskForm()
    if form.validate_on_submit():
        task_id = create_task(form.title.data, form.description.data, current_user)
        flash("Tâche créée.", "success")
        return redirect(url_for("team.task_detail", task_id=task_id))
    return render_template("task_form.html", title="Nouvelle tâche", form=form,
                           back_url=url_for("team.dashboard"))

@bp.route("/espace-equipe/taches/<task_id>", methods=["GET", "POST"])
@login_required
def task_detail(task_id):
    task = _get_task(task_id)
    form = MessageForm()
    if form.validate_on_submit():
        add_message(task_id, current_user, form.text.data)
        return redirect(url_for("team.task_detail", task_id=task_id, _anchor="messages"))
    return render_template("task.html", title=task["title"], task=task,
                           messages=list_messages(task_id), form=form,
                           statuses=TASK_STATUSES, names=_names(),
                           can_delete=_can_delete(task))

@bp.route("/espace-equipe/taches/<task_id>/modifier", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = _get_task(task_id)
    detail_url = url_for("team.task_detail", task_id=task_id)
    form = TaskForm()
    form.submit.label.text = "Enregistrer"
    if form.validate_on_submit():
        if (form.title.data, form.description.data) != (task["title"], task.get("description", "")):
            edit_task(task_id, current_user, form.title.data, form.description.data)
            flash("Tâche modifiée.", "success")
        return redirect(detail_url)
    if request.method == "GET":
        form.title.data = task["title"]
        form.description.data = task.get("description", "")
    return render_template("task_form.html", title="Modifier la tâche", form=form, back_url=detail_url)

@bp.route("/espace-equipe/taches/<task_id>/statut", methods=["POST"])
@login_required
def set_status(task_id):
    status = request.form.get("status")
    if status not in TASK_STATUSES:
        abort(400)
    task = _get_task(task_id)
    if task.get("status") != status:
        set_task_status(task_id, current_user, status)
    if request.form.get("back") == "detail":
        return redirect(url_for("team.task_detail", task_id=task_id))
    return redirect(url_for("team.dashboard"))

@bp.route("/espace-equipe/taches/<task_id>/supprimer", methods=["POST"])
@login_required
def remove(task_id):
    task = _get_task(task_id)
    if not _can_delete(task):
        abort(403)
    delete_task(task_id)
    flash("Tâche supprimée.", "success")
    return redirect(url_for("team.dashboard"))
