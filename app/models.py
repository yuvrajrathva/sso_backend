from sqlalchemy import Column, Integer, String, Boolean
from .database import Base
import re

class User(Base):
    __tablename__ = "users"

    roll_no = Column(String(11), unique=True)
    first_name = Column(String(20))
    last_name = Column(String(20))
    email = Column(String(50), primary_key=True, index=True)
    password = Column(String(100))
    phone_number = Column(String(10))
    is_verified = Column(Boolean)

    def validate_email(self):
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email) or not re.match(r"^[^@]+@iitj\.ac\.in$", self.email):
            raise ValueError("Invalid email format")
    
    def validate_phone_number(self):
        if not re.match(r"^\+?1?\d{9,15}$", self.phone_number):
            raise ValueError("Invalid phone number format")

    def validate_password(self):
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not any(char.isdigit() for char in self.password):
            raise ValueError("Password must contain at least one number")
        if not any(char.isupper() for char in self.password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in self.password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(not char.isalnum() for char in self.password):
            raise ValueError("Password must contain at least one special charater")


class ServiceProvider(Base):
    __tablename__ = "service_providers"

    client_id = Column(String(50), primary_key=True, index=True)
    name = Column(String(100))
    redirect_url = Column(String(100))
    is_verified = Column(Boolean)
