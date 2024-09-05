from sqlalchemy.orm import Session

from app.models import User, ServiceProvider
from app.schemas import UserSchema, ServiceProviderSchema
from app.utils import hash_password


def create_user(db: Session, user: UserSchema):
    hashed_password = hash_password(user.password)
    user = User(roll_no=user.roll_no, first_name=user.first_name, last_name=user.last_name, email=user.email, password=hashed_password, phone_number=user.phone_number, is_verified=user.is_verified)

    try:
        user.validate_email()
        user.validate_phone_number()
        user.validate_password()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_roll_no(db: Session, roll_no: int):
    return db.query(User).filter(User.roll_no == roll_no).first()

def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()