from pydantic import BaseModel
from typing import Optional
from fastapi import Request, Depends, Query
from datetime import datetime
from typing import List
from app.utils import JWTBearer


class UserSchema(BaseModel):
    roll_no: str
    first_name: str
    last_name: str
    email: str
    password: str
    phone_number: str


class ServiceProviderSchema(BaseModel):
    name: str
    developer_id: int
    redirect_url: str
    scope: List[int]


class GetServiceProviderDetailsSchema(BaseModel):
    id: int
    name: str
    created_at: datetime
    client_id: str
    client_secret: str
    redirect_url: str
    is_verified: bool
    scopes: List[str]


class LoginSchema(BaseModel):
    email: str
    password: str
    redirect_uri: str
    response_type: str
    client_id: str
    state: str
    scope: str


class SessionSchema(BaseModel):
    response_type: str
    client_id: str
    state: str
    redirect_uri: str
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


class DeveloperLoginSchema(BaseModel):
    email: str
    password: str


class GetServiceProvidersSchema(BaseModel):
    service_provider_id: int
    client_id: str
    client_secret: str
    name: str
    redirect_url: str
    is_verified: bool

class GetDeveloperDetailsSchema(BaseModel):
    id: int
    roll_no: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    is_verified: bool
