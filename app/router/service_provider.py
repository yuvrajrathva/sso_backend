from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List
from urllib.parse import quote

from app.models import ServiceProvider, User, ClientScope, Scope
from app.schemas import ServiceProviderSchema, SessionSchema, GetServiceProviderDetailsSchema
from app.config import Settings
from app.database import get_db
from app.utils import generate_authorization_code, verify_session, get_current_user
from fastapi.responses import RedirectResponse, JSONResponse

router = APIRouter()


@router.get("/credentials", response_model=List[GetServiceProviderDetailsSchema])
def read_service_providers(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    service_providers = db.query(ServiceProvider).filter(ServiceProvider.developer_id == current_user.id).order_by(ServiceProvider.created_at).all()
    service_providers_with_scopes = []

    for service_provider in service_providers:
        client_scopes = (
            db.query(Scope.scope)
            .join(ClientScope, ClientScope.scope_id == Scope.id)
            .filter(ClientScope.service_provider_id == service_provider.id)
            .all()
        )

        scope_strings = [scope.scope for scope in client_scopes]
        print("Scopes:", scope_strings)

        service_provider_data = {
            **service_provider.__dict__,
            "scopes": scope_strings       
        }
        service_providers_with_scopes.append(service_provider_data)

    return service_providers_with_scopes


@router.post("/create/")
def create_service_provider(service_provider: ServiceProviderSchema, db: Session = Depends(get_db)):
    db_service_provider = db.query(ServiceProvider).filter(
        (ServiceProvider.name == service_provider.name) |
        (ServiceProvider.redirect_url == service_provider.redirect_url)
    ).first()
    if db_service_provider:
        raise HTTPException(status_code=400, detail='Service Provider already registered')
    db_service_provider = ServiceProvider(
        name=service_provider.name,
        developer_id=service_provider.developer_id,
        redirect_url=service_provider.redirect_url,
    )
    db.add(db_service_provider)
    db.commit()
    db.refresh(db_service_provider)

    for scopeId in service_provider.scope:
        db_client_scope = ClientScope(service_provider_id=db_service_provider.id, scope_id=scopeId)
        db.add(db_client_scope)
    db.commit()

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
