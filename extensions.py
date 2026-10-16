
import json
import os

import firebase_admin
from dotenv import load_dotenv
from firebase_admin import credentials, firestore
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# chargé ici pour que les variables du .env existent avant la lecture ci-dessous
load_dotenv()

csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.login_view = "auth.login"

# Firebase (vues, posts, images)
cred_json = os.environ.get("FIREBASE_CREDENTIALS")
if cred_json:
    cred = credentials.Certificate(json.loads(cred_json))
else:
    cred = credentials.Certificate("firebase_service_account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()
