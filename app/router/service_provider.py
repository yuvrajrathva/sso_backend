from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List

from app.models import ServiceProvider
from app.schemas import ServiceProviderSchema
from app.config import Settings
from app.router.user import get_db
from app.utils import generate_authorization_code
from fastapi.responses import RedirectResponse

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


@router.get("/authorize/")
def authorize_service_provider(response_type: str, scope: str, client_id: str, state: str, redirect_uri: str, db: Session = Depends(get_db)):
    service_provider = db.query(ServiceProvider).filter(ServiceProvider.client_id == client_id).first()
    if not service_provider:
        raise HTTPException(status_code=400, detail='Invalid client_id')

    if response_type != 'code':
        raise HTTPException(status_code=400, detail='Unsupported response_type')

    authorization_code = generate_authorization_code(client_id, redirect_uri, scope, state)

    if service_provider.redirect_url != redirect_uri:
        raise HTTPException(status_code=400, detail='Invalid redirect_uri')

    # Redirect to the redirect_uri with the authorization code
    redirect_url = f"{redirect_uri}?code={authorization_code}&state={state}"
    return RedirectResponse(url=redirect_url, status_code=302)
