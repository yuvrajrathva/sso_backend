from pydantic import BaseModel
from typing import Optional
from fastapi import Request


class UserSchema(BaseModel):
    roll_no: str
    first_name: str
    last_name: str
    email: str
    password: str
    phone_number: str


class ServiceProviderSchema(BaseModel):
    client_id: str
    name: str
    redirect_url: str
    
class LoginSchema(BaseModel):
    email: str
    password: str
    redirect_uri: str
    response_type: str
    client_id: str
    state: str
    scope: str


class Token(BaseModel):
    access_token: str
    token_type: str
    redirect_uri: str


class VerifyCode(BaseModel):
    email: str
    code: str


class ResendCode(BaseModel):
    email: str
