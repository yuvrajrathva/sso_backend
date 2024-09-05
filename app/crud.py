from sqlalchemy.orm import Session

from app.models import User, ServiceProvider
from app.schemas import UserSchema, ServiceProviderSchema
from app.utils import hash_password


def create_user(db: Session, user: UserSchema):
    hashed_password = hash_password(user.password)
    db_user = User(roll_no=user.roll_no, first_name=user.first_name, last_name=user.last_name, email=user.email, password=hashed_password, mobile_no=user.mobile_no, is_verified=user.is_verified)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()