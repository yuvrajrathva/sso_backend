from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
from urllib.parse import quote

from app.database import SessionLocal
from app.schemas import Token
from app.models import User, VerificationCode, UserSession, ServiceProvider
from app.schemas import UserSchema, VerifyCode, ResendCode, LoginSchema
from app.crud import create_user, get_all_users, resend_verification_code
from app.config import Settings
from app.utils import authenticate_user, verify_session

router = APIRouter()


def get_db():
    db = SessionLocal()
    try : 
        yield db
    finally:
        db.close()


@router.get("/", response_model=List[UserSchema])
def read_users_endpoint(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = get_all_users(db, skip=skip, limit=limit)
    return users


@router.post("/signup/")
def create_user_endpoint(user:UserSchema, db:Session=Depends(get_db)):
    db_user = db.query(User).filter((User.email == user.email) | (User.roll_no == user.roll_no)).first()
    if db_user:
        raise HTTPException(status_code=400, detail='User already registered')
    user = create_user(db, user)
    return user


@router.get("/verify-session/")
async def session_verification(
    response_type: str = Query(...),
    scope: str = Query(...),
    client_id: str = Query(...),
    state: str = Query(...),
    redirect_uri: str = Query(...),
    request: Request = Request,
    db: Session = Depends(get_db)
):
    session = verify_session(db, request)
    if not session:
        return RedirectResponse(f"{Settings().sso_client_url}/login?redirect_uri={quote(redirect_uri, safe='')}&client_id={client_id}&response_type={response_type}&state={state}&scope={quote(scope, safe='')}", status_code=303)
    
    service_provider = db.query(ServiceProvider).filter(ServiceProvider.client_id == client_id).first()
    if not service_provider:
        raise HTTPException(status_code=400, detail='Invalid client_id')

    if response_type != 'code':
        raise HTTPException(status_code=400, detail='Unsupported response_type')

    if service_provider.redirect_url != redirect_uri:
        raise HTTPException(status_code=400, detail='Invalid redirect_uri')

    redirect_url = f"{Settings().sso_client_url}/consent?response_type={response_type}&client_id={client_id}&state={state}&scope={quote(scope, safe='')}"

    response = RedirectResponse(redirect_url, status_code=302)

    return response


@router.post("/login/")
def login_endpoint(
    form_data: LoginSchema, db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(db, form_data.email, form_data.password, form_data.client_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_session = UserSession(email=user.email)
    db.add(user_session)
    db.commit()

    # redirect_url = f"{Settings().sso_client_url}/consent?response_type={form_data.response_type}&client_id={form_data.client_id}&state={form_data.state}&scope={quote(form_data.scope)}"

    # print("redirect_url:", redirect_url)
    response_message = {'response_type': form_data.response_type, 
                        'client_id': form_data.client_id, 
                        'state': form_data.state, 
                        'scope': form_data.scope}
    
    response = JSONResponse(content=response_message, status_code=200)
    response.set_cookie(key="session_id", value=user_session.session_id, httponly=True, secure=False)
    return response

@router.post("/logout")
def session_logout(request: Request, db: Session = Depends(get_db)):
    session_id = request.cookies.get("session_id")
    user_session = db.query(UserSession).filter(UserSession.session_id == session_id).first()
    if user_session:
        user_session.session_expiry = datetime.now()
        user_session.last_activity = datetime.now()
        user_session.is_active = False
        db.commit()
    # response.delete_cookie("session_id")

    return {"status": "logged out"}


@router.post("/verify-code/")
def verify_code(user_code: VerifyCode, db: Session = Depends(get_db)):
    verification_code = db.query(VerificationCode).filter(
        VerificationCode.email == user_code.email, 
        VerificationCode.code == user_code.code,
        VerificationCode.is_verified == False
    ).order_by(desc(VerificationCode.code_expiry)).first()

    if not verification_code:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    if verification_code.code_expiry < datetime.now():
        raise HTTPException(status_code=400, detail="Verification code has expired.")

    verification_code.is_verified = True
    # Should we delete all verification code with this email here? Because now user is verified.
    db.commit()

    user = db.query(User).filter(User.email == user_code.email).first()
    if user:
        user.is_verified = True
        db.commit()
        return {"message": "Email verified successfully."}

    raise HTTPException(status_code=400, detail="User not found.")


@router.post("/resend-verify-code/")
def resend_verify_code(user_email: ResendCode, db: Session = Depends(get_db)):
    user = resend_verification_code(db, user_email.email)
    return user
