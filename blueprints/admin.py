import secrets

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, url_for)
from flask_login import current_user
from firebase_admin import firestore
from werkzeug.security import generate_password_hash

from blueprints.auth import admin_required
from data import (create_user, delete_images, delete_user, get_post,
                  get_posts, get_user, list_users, reset_views, store_images,
                  update_user, username_taken)
from extensions import db
from forms import NewPost, NewUserForm

bp = Blueprint("admin", __name__)


@bp.route("/admin")
@admin_required
def dashboard():
    return render_template("admin.html", title="Dashboard Admin", posts=get_posts())


@bp.route("/admin/post/guide")
@admin_required
def guide():
    return render_template("markdown.html", title="Guide")


@bp.route("/admin/post/new", methods=["GET", "POST"])
@admin_required
def new_post():
    form = NewPost()
    error = None
    if form.validate_on_submit():
        image_ids, error = store_images(form.images.data)
        if error is None:
            try:
                db.collection("posts").add({
                    "title": form.title.data.strip(),
                    "content": form.content.data.strip(),
                    "title_en": form.title_en.data or "",
                    "content_en": (form.content_en.data or "").strip(),
                    "images": image_ids,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                })
            except Exception as e:
                print(f"Erreur création du post: {e}")
                delete_images(image_ids)
                error = "Erreur lors de l'enregistrement du post, réessaie."
            else:
                return redirect(url_for("admin.dashboard"))
    return render_template("post_form.html", title="Nouvelle Actu", form=form, error=error, post_images=[])


@bp.route("/admin/post/<post_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_post(post_id):
    post = get_post(post_id)
    if post is None:
        abort(404)
    existing = post.get("images", [])
    form = NewPost()
    form.submit.label.text = "Enregistrer"
    error = None
    if form.validate_on_submit():
        # only images that really belong to this post can be removed
        remove_ids = set(request.form.getlist("remove_images"))
        keep = [i for i in existing if i not in remove_ids]
        removed = [i for i in existing if i in remove_ids]
        new_ids, error = store_images(form.images.data)
        if error is None:
            db.collection("posts").document(post_id).update({
                "title": form.title.data.strip(),
                "content": form.content.data.strip(),
                "title_en": form.title_en.data or "",
                "content_en": (form.content_en.data or "").strip(),
                "images": keep + new_ids,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            delete_images(removed)
            return redirect(url_for("admin.dashboard"))
    if request.method == "GET":
        form.title.data = post["title"]
        form.content.data = post["content"]
        form.title_en.data = post.get("title_en", "")
        form.content_en.data = post.get("content_en", "")
    return render_template("post_form.html", title="Modifier l'actu", form=form, error=error, post_images=existing)


@bp.route("/admin/post/<post_id>/delete", methods=["POST"])
@admin_required
def delete_post(post_id):
    post = get_post(post_id)
    if post is not None:
        db.collection("posts").document(post_id).delete()
        delete_images(post.get("images", []))
    return redirect(url_for("admin.dashboard"))


@bp.route("/admin/reset_views", methods=["POST"])
@admin_required
def reset():
    reset_views()
    return redirect(url_for("admin.dashboard"))


# ---------- gestion des comptes ----------

@bp.route("/admin/users", methods=["GET", "POST"])
@admin_required
def users():
    form = NewUserForm()
    if form.validate_on_submit():
        username = form.username.data
        if username_taken(username):
            form.username.errors.append("Cet identifiant est déjà utilisé.")
        else:
            temp_password = secrets.token_urlsafe(9)
            create_user(username, generate_password_hash(temp_password),
                        role=form.role.data, must_change_password=True)
            flash(f"Compte « {username} » créé. Mot de passe temporaire : {temp_password} "
                  "(note-le maintenant, il ne sera plus affiché).", "success")
            return redirect(url_for("admin.users"))
    return render_template("admin_users.html", title="Comptes", form=form, users=list_users())


@bp.route("/admin/users/<user_id>/reset-password", methods=["POST"])
@admin_required
def reset_user_password(user_id):
    target = get_user(user_id)
    if target is None:
        abort(404)
    if target["id"] == current_user.id:
        flash("Pour ton propre mot de passe, utilise la page « Mon compte ».", "error")
        return redirect(url_for("admin.users"))
    temp_password = secrets.token_urlsafe(9)
    update_user(user_id, password_hash=generate_password_hash(temp_password), must_change_password=True)
    flash(f"Nouveau mot de passe temporaire pour « {target['username']} » : {temp_password} "
          "(note-le maintenant, il ne sera plus affiché).", "success")
    return redirect(url_for("admin.users"))


@bp.route("/admin/users/<user_id>/delete", methods=["POST"])
@admin_required
def delete_account(user_id):
    target = get_user(user_id)
    if target is None:
        abort(404)
    if target["id"] == current_user.id:
        flash("Tu ne peux pas supprimer ton propre compte.", "error")
    else:
        delete_user(user_id)
        flash(f"Compte « {target['username']} » supprimé.", "success")
    return redirect(url_for("admin.users"))
