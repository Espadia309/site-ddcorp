import io
from functools import lru_cache

from firebase_admin import firestore
from google.cloud.firestore_v1 import Increment
from PIL import Image, ImageOps

from extensions import db

try:  # récent : where(filter=FieldFilter(...)) ; ancien : where(champ, op, valeur)
    from google.cloud.firestore_v1.base_query import FieldFilter
except ImportError:  # pragma: no cover
    FieldFilter = None

# ---------- vues ----------

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


# ---------- posts ----------
# get_posts() renvoie une liste, get_post(post_id) renvoie un post grâce à son id
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


# ---------- images ----------
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


# ---------- utilisateurs ----------
def _where(query, field, op, value):
    if FieldFilter is not None:
        return query.where(filter=FieldFilter(field, op, value))
    return query.where(field, op, value)


def get_user(user_id):
    if not user_id:
        return None
    doc = db.collection("users").document(user_id).get()
    if doc.exists:
        return {"id": doc.id, **doc.to_dict()}
    return None


def get_user_by_username(username):
    query = _where(db.collection("users"), "username_lower", "==", username.strip().lower()).limit(1)
    for doc in query.stream():
        return {"id": doc.id, **doc.to_dict()}
    return None


def username_taken(username, exclude_id=None):
    found = get_user_by_username(username)
    return found is not None and found["id"] != exclude_id


def users_exist():
    return any(True for _ in db.collection("users").limit(1).stream())


def list_users():
    docs = db.collection("users").order_by("username_lower").stream()
    return [{"id": d.id, **d.to_dict()} for d in docs]


def create_user(username, password_hash, role="member", must_change_password=False):
    username = username.strip()
    _, ref = db.collection("users").add({
        "username": username,
        "username_lower": username.lower(),
        "password_hash": password_hash,
        "role": role,
        "must_change_password": must_change_password,
        "created_at": firestore.SERVER_TIMESTAMP,
    })
    return ref.id


def update_user(user_id, **fields):
    db.collection("users").document(user_id).update(fields)


def delete_user(user_id):
    db.collection("users").document(user_id).delete()
