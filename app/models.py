from sqlalchemy import Column, Integer, String, Boolean
from .database import Base


class User(Base):
    __tablename__ = "users"

    roll_no = Column(String(11), primary_key=True, index=True)
    first_name = Column(String(20))
    last_name = Column(String(20))
    email = Column(String(50), unique=True)
    password = Column(String(50))
    mobile_no = Column(Integer)
    is_verified = Column(Boolean)


class ServiceProvider(Base):
    __tablename__ = "service_providers"

    client_id = Column(String(15), primary_key=True, index=True)
    name = Column(String(50))
    redirect_url = Column(String(100))
    is_verified = Column(Boolean)

