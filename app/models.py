from sqlalchemy import Column, Integer, String, Boolean
from .database import Base


class User(Base):
    __tablename__ = "users"

    roll_no = Column(String(11), unique=True)
    first_name = Column(String(20))
    last_name = Column(String(20))
    email = Column(String(50), primary_key=True, index=True)
    password = Column(String(100))
    mobile_no = Column(Integer)
    is_verified = Column(Boolean)


class ServiceProvider(Base):
    __tablename__ = "service_providers"

    client_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100))
    redirect_url = Column(String(100))
    is_verified = Column(Boolean)

