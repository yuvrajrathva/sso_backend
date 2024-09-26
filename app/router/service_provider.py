from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List

from app.models import ServiceProvider
from app.schemas import ServiceProviderSchema
from app.config import Settings
from app.router.user import get_db

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