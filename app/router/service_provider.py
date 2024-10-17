from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List
from urllib.parse import quote

from app.models import ServiceProvider
from app.schemas import ServiceProviderSchema, SessionSchema
from app.config import Settings
from app.router.user import get_db
from app.utils import generate_authorization_code, verify_session
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter()


@router.get("/", response_model=List[ServiceProviderSchema])
def read_service_providers(db: Session = Depends(get_db)):
    service_providers = db.query(ServiceProvider).all()
    return service_providers


@router.post("/create/")
def create_service_provider(service_provider: ServiceProviderSchema, db: Session = Depends(get_db)):
    db_service_provider = db.query(ServiceProvider).filter(
        (ServiceProvider.name == service_provider.name) |
        (ServiceProvider.redirect_url == service_provider.redirect_url)
    ).first()
    if db_service_provider:
        raise HTTPException(status_code=400, detail='Service Provider already registered')
    db_service_provider = ServiceProvider(**service_provider.dict(), session=db)
    db.add(db_service_provider)
    db.commit()
    db.refresh(db_service_provider)
    return db_service_provider


@router.post("/authorize/")
def authorize_service_provider(form_data: SessionSchema, request: Request = Request, db: Session = Depends(get_db)):
    session = verify_session(db, request)
    if not session:
        redirect_uri = f"{Settings().sso_client_url}/login?redirect_uri={quote(form_data.redirect_uri, safe='')}"
        redirect_uri += f"&client_id={form_data.client_id}&response_type={form_data.response_type}&state={form_data.state}&scope={quote(form_data.scope, safe='')}"

        print("Session not Valid. Redirecting to:", redirect_uri)
        return RedirectResponse(redirect_uri, status_code=303)
    

    service_provider = db.query(ServiceProvider).filter(ServiceProvider.client_id == form_data.client_id).first()
    if not service_provider:
        raise HTTPException(status_code=400, detail='Invalid client_id')

    if form_data.response_type != 'code':
        raise HTTPException(status_code=400, detail='Unsupported response_type')

    authorization_code = generate_authorization_code(form_data.client_id, form_data.redirect_uri, form_data.scope, form_data.state)

    if service_provider.redirect_url != form_data.redirect_uri:
        raise HTTPException(status_code=400, detail='Invalid redirect_uri')

    response_message = {
        'redirect_uri': form_data.redirect_uri,
        'code': authorization_code,
        'state': form_data.state
    }
    
    return JSONResponse(content=response_message, status_code=200)
