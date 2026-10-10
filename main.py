from flask import *
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, SubmitField, PasswordField, TextAreaField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
from markupsafe import escape
import firebase_admin, os, json, hmac
import markdown as markdown_lib
from datetime import timezone
from zoneinfo import ZoneInfo
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Increment


load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

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

#posts stuff (get_posts() returns a list and get_post(post_id) return a post by it's id)
def get_posts():
    docs = (db.collection("posts")
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .stream())
    return [{"id": d.id, **d.to_dict()} for d in docs]
 
def get_post(post_id):
    doc = db.collection("posts").document(post_id).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None

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
    return render_template("actus.html", title="Actualités", posts=get_posts())

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

@app.route("/admin/post/guide")
@login_required
def markdown():
    return render_template("markdown.html", title="Guide")

@app.route("/admin/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = NewPost()
    if form.validate_on_submit():
        db.collection("posts").add({
            "title": form.title.data.strip(),
            "content": form.content.data.strip(),
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        return redirect(url_for("admin"))
    return render_template("post_form.html", title="Nouvelle Actu", form=form)

@app.route("/admin/post/<post_id>/edit", methods=["GET","POST"])
@login_required
def edit_post(post_id):
    post = get_post(post_id)
    if post is None:
        abort(404)
    form = NewPost()
    form.submit.label.text = "Enregister"
    if form.validate_on_submit():
        db.collection("posts").document(post_id).update({
            "title": form.title.data.strip(),
            "content": form.content.data.strip(),
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
        return redirect(url_for("admin"))
    if request.method == "GET":
        form.title.data = post["title"]
        form.content.data = post["content"]
    return render_template("post_form.html", title="Modifier l'actu", form=form)

@app.route("/admin/post/<post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    db.collection("posts").document(post_id).delete()
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

@app.context_processor
def inject_views():
    return {"views": get_views()}

if __name__ == "__main__":
    app.run()
