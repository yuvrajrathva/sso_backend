import random
from passlib.context import CryptContext
import jwt
from fastapi import HTTPException, Request
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
from typing import Union
from app.config import Settings
from app.models import User, Session, ServiceProvider

import random
import string

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY=Settings().secret_key
ALGORITHM=Settings().algorithm
ACCESS_TOKEN_EXPIRE_MINUTES=Settings().access_token_expire_minutes


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)


def get_user(db, email: str):
    print(db)
    user = db.query(User).filter(User.email == email).first()
    print("user:", user)
    return user


def authenticate_user(db, email: str, password: str, client_id: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    if client_id:
        service_provider = db.query(ServiceProvider).filter(ServiceProvider.client_id == client_id).first()
        if not service_provider:
            return False
        if not service_provider.is_verified:
            return False            
    return user


def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def generate_authorization_code(client_id: str, redirect_uri: str, scope: str, state: str):
    authorization_code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=15))
    return authorization_code


def create_session(db, email: str):
    session_id = str(random.randint(100000, 999999))
    session = Session(email=email, session_id=session_id, session_created=datetime.now(), session_expiry=datetime.now() + timedelta(minutes=15), last_activity=datetime.now())
    db.add(session)
    db.commit()

    return session_id


"""verify that user has a valid session"""
def get_auth_user(request: Request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401)

    session = db.query(Session).filter(Session.session_id == session_id).first()
    if not session or session.session_expiry < datetime.now() or not session.is_active:
        raise HTTPException(status_code=403)
    return True