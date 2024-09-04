from pydantic import BaseModel
from typing import Optional


class UserSchema(BaseModel):
    roll_no: str
    first_name: str
    last_name: str
    email: str
    password: str
    mobile_no: Optional[int] = None 
    is_verified: bool

    class Config:
        orm_mode = True


class ServiceProviderSchema(BaseModel):
    client_id: str
    name: str
    redirect_url: str
    redirect_url: str

    class Config:
        orm_mode = True