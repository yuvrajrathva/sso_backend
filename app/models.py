from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from .database import Base
import re
import random
import string

class User(Base):
    __tablename__ = "users"

    roll_no = Column(String(11), unique=True)
    first_name = Column(String(20))
    last_name = Column(String(20))
    email = Column(String(50), primary_key=True, index=True)
    password = Column(String(100))
    phone_number = Column(String(10))
    is_verified = Column(Boolean, default=False)

    def validate_email(self):
        if not re.match(r"^[^@]+@iitj\.ac\.in$", self.email):
            raise ValueError("Invalid email format")
        return True
    
    def validate_phone_number(self):
        if not re.match(r"^[6-9]\d{9}$", self.phone_number):
            raise ValueError("Invalid phone number format")
        return True

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
        return True


class ServiceProvider(Base):
    __tablename__ = "service_providers"

    client_id = Column(String(50), primary_key=True, index=True)
    client_secret = Column(String(100), unique=True) 
    name = Column(String(100))
    redirect_url = Column(String(200))
    is_verified = Column(Boolean, default=False)

    def __init__(self, session=None, **kwargs):
        super().__init__(**kwargs)
        if not self.client_id:
            self.client_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
            
            # Use a session to query the database
            session = kwargs.get('session')
            if session:
                while session.query(self.__class__).filter_by(client_id=self.client_id).first() is not None:
                    self.client_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))

        # generate a random client secret
        if not self.client_secret:
            self.client_secret = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))

            session = kwargs.get('session')
            if session:
                while session.query(self.__class__).filter_by(client_secret=self.client_secret).first() is not None:
                    self.client_secret = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


class VerificationCode(Base):
    __tablename__ = "verification_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(50), ForeignKey("users.email"), nullable=False)
    code = Column(String(6), nullable=False)
    code_expiry = Column(DateTime, nullable=False)
    is_verified = Column(Boolean, default=False)

class UserSession(Base):
    __tablename__ = "user_sessions"

    session_id = Column(String(6), primary_key=True, nullable=False)
    email = Column(String(50), ForeignKey("users.email"), nullable=False)
    session_expiry = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, nullable=False)
    session_created = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
