import firebase_admin

from firebase_admin import credentials
from firebase_admin import auth


cred = credentials.Certificate(
    "app/core/firebase_credentials.json"
)

firebase_admin.initialize_app(cred)


def verify_firebase_token(token: str):
    """
    Verifica token JWT do Firebase
    """

    decoded_token = auth.verify_id_token(token)

    return decoded_token