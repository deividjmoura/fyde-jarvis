from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.user import User

from app.services.firebase import verify_firebase_token


def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):

    print("AUTH HEADER:", authorization)

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing"
        )

    try:
        scheme, token = authorization.split()

        print("SCHEME:", scheme)
        print("TOKEN RECEIVED:", token[:30])

        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme"
            )

        decoded_token = verify_firebase_token(token)

        print("DECODED TOKEN:", decoded_token)

        firebase_uid = decoded_token.get("uid")
        email = decoded_token.get("email")

        user = (
            db.query(User)
            .filter(User.firebase_uid == firebase_uid)
            .first()
        )

        if not user:
            user = User(
                email=email,
                firebase_uid=firebase_uid
            )

            db.add(user)
            db.commit()
            db.refresh(user)

        return user

    except Exception as e:
        print("AUTH ERROR:", str(e))

        raise HTTPException(
            status_code=401,
            detail=str(e)
        )