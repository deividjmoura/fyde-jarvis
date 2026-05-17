def verify_firebase_token(token: str):
    decoded_token = auth.verify_id_token(token)

    print("DECODED:", decoded_token)

    return decoded_token

    print("BACKEND PROJECT:", firebase_credentials.get("project_id"))