from __future__ import print_function
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
from dotenv import load_dotenv
from app.database import engine, Base
from app.config import Settings
from app.router import user

Base.metadata.create_all(bind=engine)
app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()

@lru_cache
def get_settings():
    return Settings()

app.include_router(user.router, prefix="/user", tags=["user"])


