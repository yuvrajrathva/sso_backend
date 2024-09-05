from fastapi import FastAPI, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
from functools import lru_cache
from app.models import User, ServiceProvider
from app.schemas import UserSchema, ServiceProviderSchema
from app.database import SessionLocal, engine, Base
from app.crud import create_user, get_all_users, get_user_by_roll_no
from app.config import Settings


Base.metadata.create_all(bind=engine)

app = FastAPI()

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
    db_user = get_user_by_roll_no(db, user.roll_no)
    if db_user:
        raise HTTPException(status_code=400, detail='User already registered')
    user = create_user(db, user)
    return user

