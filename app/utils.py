from passlib.context import CryptContext
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta
from typing import Union
from app.config import Settings
from app.models import User

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


def authenticate_user(db, email: str, password: str):
    user = get_user(db, email)
    if not user:
        return False
    if not verify_password(password, user.password):
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
