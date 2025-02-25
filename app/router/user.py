from fastapi import APIRouter, Depends, HTTPException, status, Response, Request, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from typing_extensions import Annotated
from urllib.parse import quote

from app.schemas import Token, SessionSchema
from app.database import get_db
from app.models import User, VerificationCode, UserSession, ServiceProvider
from app.schemas import UserSchema, VerifyCode, ResendCode, LoginSchema
from app.crud import create_user, get_all_users, resend_verification_code
from app.config import Settings
from app.utils import authenticate_user, verify_session, verify_consent, generate_authorization_code, get_scopes_with_spaces, get_current_user, get_current_service_provider

router = APIRouter()


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


@router.post("/verify-session/")
async def session_verification(
    form_data: SessionSchema,
    request: Request = Request,
    db: Session = Depends(get_db)
):
    session = verify_session(db, request)
    print("Session:", session)
    if not session:
        return RedirectResponse(f"{Settings().sso_client_url}/login?redirect_url={quote(form_data.redirect_url, safe='')}&client_id={form_data.client_id}&response_type={form_data.response_type}&state={form_data.state}&scope={quote(form_data.scope, safe='')}", status_code=303)
    
    service_provider = db.query(ServiceProvider).filter(ServiceProvider.client_id == form_data.client_id).first()
    if not service_provider:
        raise HTTPException(status_code=400, detail='Invalid client_id')

    if form_data.response_type != 'code':
        raise HTTPException(status_code=400, detail='Unsupported response_type')

    if service_provider.redirect_url != form_data.redirect_url:
        raise HTTPException(status_code=400, detail='Invalid redirect_url')
    
    session_id = request.headers.get("session_id")
    session = db.query(UserSession).filter(UserSession.session_id == session_id).first()

    if verify_consent(db, form_data.client_id, session.user_id):
        authorization_code = generate_authorization_code(db, session.user_id, form_data.client_id)
        redirect_url = form_data.redirect_url + f"?auth_code={authorization_code}&state={form_data.state}"
    else :
        scope = get_scopes_with_spaces(service_provider.id, db)
        redirect_url = f"{Settings().sso_client_url}/consent?response_type={form_data.response_type}&client_id={form_data.client_id}&state={form_data.state}&scope={quote(scope, safe='')}&redirect_url={quote(form_data.redirect_url, safe='')}"

    response = RedirectResponse(redirect_url, status_code=302)

    return response


@router.post("/login/")
def login_endpoint(
    form_data: LoginSchema, db: Session = Depends(get_db)
) -> Token:
    user = authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    service_provider = db.query(ServiceProvider).filter(ServiceProvider.client_id == form_data.client_id).first()
    if not service_provider:
        raise HTTPException(status_code=400, detail='Invalid client_id')

    if service_provider.redirect_url != form_data.redirect_url:
        raise HTTPException(status_code=400, detail='Invalid redirect_url')

    user_session = UserSession(user_id=user.id)
    db.add(user_session)
    db.commit()

    if verify_consent(db, form_data.client_id, user.id):
        authorization_code = generate_authorization_code(db, user.id, form_data.client_id)
        redirect_url = form_data.redirect_url + f"?auth_code={authorization_code}&state={form_data.state}"
        return JSONResponse({"redirect_url": redirect_url, "session_id": user_session.session_id, "should_redirect": True})
    else :
        scopes = get_scopes_with_spaces(service_provider.id, db)
        response_message = {'response_type': 'code',
                            'client_id': service_provider.client_id, 
                            'state': form_data.state, 
                            'scope': scopes,
                            'redirect_url': service_provider.redirect_url,
                            'session_id': user_session.session_id,
                            "should_redirect": False}

        response = JSONResponse(content=response_message, status_code=200)
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


@router.get("/me/")
def read_users_me(current_user: User = Depends(get_current_user), current_service_provider: ServiceProvider = Depends(get_current_service_provider), db: Session = Depends(get_db)):
    scopes = get_scopes_with_spaces(current_service_provider.id, db).split(" ")
    response_message = {}
    for scope in scopes:
        if scope == "name":
            response_message["name"] = current_user.first_name + " " + current_user.last_name
        elif scope == "email":
            response_message["email"] = current_user.email
        elif scope == "roll_no":
            response_message["roll_no"] = current_user.roll_no
        elif scope == "phone":
            response_message["phone"] = current_user.phone_number
        elif scope == "profile":
            response_message["email"] = current_user.email
            response_message["name"] = current_user.first_name + " " + current_user.last_name
        elif scope == "openid":
            continue
        else:
            raise HTTPException(status_code=400, detail="Invalid scope")
    response = JSONResponse(content=response_message, status_code=200)
    return response