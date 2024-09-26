from pydantic import BaseModel
from typing import Optional


class UserSchema(BaseModel):
    roll_no: str
    first_name: str
    last_name: str
    email: str
    password: str
    phone_number: str


class ServiceProviderSchema(BaseModel):
    name: str
    redirect_url: str
    

class Token(BaseModel):
    access_token: str
    token_type: str


class VerifyCode(BaseModel):
    email: str
    code: str


class ResendCode(BaseModel):
    email: str
