from __future__ import print_function
import time
from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
from functools import lru_cache
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from dotenv import load_dotenv
import os
import random
from datetime import datetime

from app.schemas import Token
from app.models import User, ServiceProvider, VerificationCode
from app.schemas import UserSchema, ServiceProviderSchema
from app.database import SessionLocal, engine, Base
from app.crud import create_user, get_all_users
from app.config import Settings
from app.utils import authenticate_user, create_access_token, get_user


Base.metadata.create_all(bind=engine)
app = FastAPI()

load_dotenv()

def get_db():
    db = SessionLocal()
    try : 
        yield db
    finally:
        db.close()

@lru_cache
def get_settings():
    return Settings()


@app.get("/", response_model=List[UserSchema])
def read_users_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_all_users(db, skip=skip, limit=limit)
    return users

@app.post("/signup/")
def create_user_endpoint(user:UserSchema, db:Session=Depends(get_db)):
    db_user = get_user(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail='User already registered')
    user = create_user(db, user)
    return user


@app.post("/token")
async def login_endpoint(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=Settings().access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.post("/verify-otp/")
def verify_otp(email: str, otp: str, db: Session = Depends(get_db)):
    verification_code = db.query(VerificationCode).filter(
        VerificationCode.email == email, 
        VerificationCode.code == otp,
        VerificationCode.is_verified == False
    ).first()

    if not verification_code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    if verification_code.code_expiry < datetime.now():
        raise HTTPException(status_code=400, detail="Verification code has expired.")

    verification_code.is_verified = True
    db.commit()

    user = db.query(User).filter(User.email == email).first()
    if user:
        user.is_verified = True
        db.commit()
        return {"message": "Email verified successfully."}

    raise HTTPException(status_code=400, detail="User not found.")
