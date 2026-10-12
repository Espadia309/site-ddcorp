from flask import *
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
from markupsafe import escape
import firebase_admin, os, json, hmac, io, re
from functools import lru_cache
from PIL import Image, ImageOps
import markdown as markdown_lib
from datetime import timezone
from zoneinfo import ZoneInfo
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Increment

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

#max size of a request
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

csrf = CSRFProtect(app)

# firebase stuff for number of views and posts
cred_json = os.environ.get("FIREBASE_CREDENTIALS")
if cred_json:
    cred = credentials.Certificate(json.loads(cred_json))
else:
    cred = credentials.Certificate("firebase_service_account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

#views stuff function whatever kill me please
def increment_views():
    ref = db.collection("site_stats").document("main")
    ref.set(
        {"views": Increment(1)},
        merge=True
    )

def get_views():
    ref = db.collection("site_stats").document("main")
    doc = ref.get()
    if doc.exists:
        return doc.to_dict().get("views", 0)
    return 0

def reset_views():
    ref = db.collection("site_stats").document("main")
    ref.set(
        {"views": 0},
        merge=True
    )

#posts stuff (get_posts() returns a list and get_post(post_id) return a post by it's id)
def get_posts(limit=None):
    query = db.collection("posts").order_by("created_at", direction=firestore.Query.DESCENDING)
    if limit:
        query = query.limit(limit)
    docs = query.stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]

def get_post(post_id):
    doc = db.collection("posts").document(post_id).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None

#IMAGES STUFF IDK IF IT WORKS THO SO FUCK IT
ALLOWED_FORMATS = ["jpg", "jpeg", "png", "gif", "webp"]
MAX_IMAGES_PER_SUBMIT = 8
MAX_IMAGE_BYTES = 900_000
Image.MAX_IMAGE_PIXELS = 60_000_000
 
def process_image(file_storage):
    """En gros ça prends l'image ça la traite pour qu'elle soit plus lègère et boom kaboom"""
    im = Image.open(file_storage.stream)
    im.load()
    im = ImageOps.exif_transpose(im)
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        im = im.convert("RGBA")
    else:
        im = im.convert("RGB")
    for quality, max_side in ((82, 1600), (72, 1400), (60, 1200), (50, 1000)):
        im.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=quality, method=4)
        if buf.tell() <= MAX_IMAGE_BYTES:
            return buf.getvalue()
    raise ValueError("image trop lourde")
 
def delete_images(image_ids):
    for image_id in image_ids:
        try:
            db.collection("images").document(image_id).delete()
        except Exception as e:
            print(f"Erreur suppression image {image_id}: {e}")
    load_image.cache_clear()
 
def store_images(files):
    files = [f for f in (files or []) if f and f.filename]
    if len(files) > MAX_IMAGES_PER_SUBMIT:
        return [], f"Maximum {MAX_IMAGES_PER_SUBMIT} images à la fois."
    saved = []
    try:
        for f in files:
            data = process_image(f)
            _, ref = db.collection("images").add({
                "data": data,
                "content_type": "image/webp",
                "created_at": firestore.SERVER_TIMESTAMP,
            })
            saved.append(ref.id)
    except Exception as e:
        print(f"Erreur enregistrement image: {e}")
        delete_images(saved)
        return [], "Impossible d'enregistrer les images (jpg, png, gif ou webp valides uniquement)."
    return saved, None
 
@lru_cache(maxsize=64)
def load_image(image_id):
    """Images never change once saved, so keeping the most recent ones in
    memory saves a lot of Firestore reads."""
    doc = db.collection("images").document(image_id).get()
    if not doc.exists:
        return None
    d = doc.to_dict()
    return d["data"], d.get("content_type", "image/webp")

#Firebase's time is UTC so we convert it to french time basically (for the timing of the post)
try:
    PARIS = ZoneInfo("Europe/Paris")
except Exception:
    PARIS = timezone.utc

@app.template_filter("paris")
def paris_filter(dt, fmt="%d/%m/%Y à %Hh%M"):
    if dt is None:
        return ""
    return dt.astimezone(PARIS).strftime(fmt)

@app.template_filter("markdown")
def markdown_filter(text):
    return markdown_lib.markdown(text, extensions=["nl2br", "fenced_code", "sane_lists"])

# login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser("admin")
    return None

# login form for the admin page
class LoginForm(FlaskForm):
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField("Connexion") 

#New post form
class NewPost(FlaskForm):
    title = StringField("Titre", validators=[DataRequired()])
    content = TextAreaField("Contenu", validators=[DataRequired()])
    images = MultipleFileField("Images (plusieurs possibles)",
                               validators=[FileAllowed(ALLOWED_FORMATS, "Images uniquement (jpg, png, gif, webp).")])
    submit = SubmitField("Poster", )

@app.route("/")
def home():
    increment_views()
    return render_template("home.html",title="Bienvenue") 

@app.route("/equipe")
def equipe():
    return render_template("equipe.html", title="Équipe")

@app.route("/récompenses")
def recompenses():
    return render_template("recompenses.html", title="Récompenses")

@app.route("/projet")
def projet():
    return render_template("projet.html", title="Projets")

@app.route("/robot")
def robot():
    return render_template("robot.html", title="Robot Game")

@app.route("/actus")
def actus():
    return render_template("actus.html", title="Actualités", posts=get_posts(limit=20))

@app.route("/projet/vestige")
def vestige():
    return render_template("vestige.html", title="Vestige")

@app.route("/projet/hydrache")
def hydrache():
    return render_template("hydrache.html", title="Hydra'che")

@app.route("/contact")
def formulaire():
    return render_template("formulaire.html", title="Contact")

@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    return render_template("admin.html", title="Dashboard Admin", posts=get_posts())

#idfk kill me pwetty pwease
@app.route("/img/<image_id>")
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

@app.route("/admin/post/guide")
@login_required
def markdown():
    return render_template("markdown.html", title="Guide")

@app.route("/admin/post/new", methods=["GET", "POST"])
@login_required
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
                    "images": image_ids,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "updated_at": firestore.SERVER_TIMESTAMP,
                })
            except Exception as e:
                print(f"Erreur création du post: {e}")
                delete_images(image_ids)
                error = "Erreur lors de l'enregistrement du post, réessaie."
            else:
                return redirect(url_for("admin"))
    return render_template("post_form.html", title="Nouvelle Actu", form=form, error=error, post_images=[])

@app.route("/admin/post/<post_id>/edit", methods=["GET", "POST"])
@login_required
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
                "images": keep + new_ids,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            delete_images(removed)
            return redirect(url_for("admin"))
    if request.method == "GET":
        form.title.data = post["title"]
        form.content.data = post["content"]
    return render_template("post_form.html", title="Modifier l'actu", form=form, error=error, post_images=existing)

@app.route("/admin/post/<post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = get_post(post_id)
    if post is not None:
        db.collection("posts").document(post_id).delete()
        delete_images(post.get("images", []))
    return redirect(url_for("admin"))

@app.route("/admin/reset_views", methods=["GET","POST"])
@login_required
def reset():
    reset_views()
    return redirect(url_for("admin"))

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    password = None
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        form.password.data = ""
        if password == os.environ.get("PASSWORD"):
            user = AdminUser("admin")
            login_user(user)
            return redirect(url_for("admin"))

        return render_template("login.html",
                               title="Connexion",
                               form=form,
                               error="Mot de passe incorrect.")

    return render_template("login.html",
                           title = "Connexion",
                           password = password,
                           form = form)

@app.route("/admin/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title="Page Introuvable"), 404

@app.errorhandler(413)
def too_large(e):
    return render_template("404.html", title="Fichiers trop lourds"), 413

@app.context_processor
def inject_views():
    return {"views": get_views()}

if __name__ == "__main__":
    app.run()
