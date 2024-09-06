from fastapi import HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import os
import random
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

from app.models import User, ServiceProvider, VerificationCode
from app.schemas import UserSchema, ServiceProviderSchema
from app.utils import hash_password


def generate_verification_code():
    verification_code = ''
    for i in range(6):
        verification_code += str(random.randint(0,9))
    return verification_code

def send_verification_code(email: str, otp: str):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key["api-key"] = os.getenv("BREVO_API_KEY")
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))

    sender= {"name": "IITJ SSO", "email": "rathva.1@iitj.ac.in"}
    subject = "Verification code for IIT SSO"
    to = [{"email":email,"name":"New SSO User"}]
    html_content = f"<h1>Your verification code is: {otp}</h1>"
    reply_to = {"email":os.getenv("EMAIL"),"name":"SSO IITJ"}
    
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, reply_to=reply_to, html_content=html_content, sender=sender, subject=subject)

    try:
        api_response = api_instance.send_transac_email(send_smtp_email)
        print(api_response)
        return {"message":"Email sent successfully"}

    except ApiException as e:
        print("Exception when calling SMTPApi->send_transac_email: %s\n" % e)
        raise HTTPException(status_code=500, detail="Failed to send Verification Code email.")

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

    verification_code = generate_verification_code()
    verification_code = VerificationCode(email=user.email, code=verification_code, code_expiry=datetime.now() + timedelta(minutes=15), is_verified=False)
    db.add(verification_code)
    db.commit()

    send_verification_code(user.email, verification_code.code)

    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(User).offset(skip).limit(limit).all()