import json

import firebase_admin

from firebase_admin import auth
from firebase_admin import credentials

from app.core.config import settings


firebase_credentials = json.loads(
    settings.FIREBASE_CREDENTIALS
)

cred = credentials.Certificate(
    firebase_credentials
)

if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)


def verify_firebase_token(token: str):
    """
    Verifica token JWT do Firebase
    """

    decoded_token = auth.verify_id_token(token)

    return decoded_token