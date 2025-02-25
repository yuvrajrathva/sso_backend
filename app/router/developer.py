from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.utils import authenticate_user, create_access_token, create_refresh_token, create_session, verify_session, get_user_by_id, decode_token, JWTBearer, get_current_user, decode_refresh_token
from app.schemas import DeveloperLoginSchema, GetDeveloperDetailsSchema, GetDeveloperKeysSchema, GetAllScopesSchema
from app.models import User, ServiceProvider, Scope, ClientScope
from app.database import get_db
from typing import List

router = APIRouter()

@router.post("/login/")
def login_endpoint(
    user: DeveloperLoginSchema,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, user.email, user.password)
    if not user:
        raise HTTPException(status_code=400, detail='Invalid credentials')
    
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/get-user/", response_model=GetDeveloperDetailsSchema)
def get_user_endpoint(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get("/keys/", response_model=List[GetDeveloperKeysSchema])
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

        service_provider_data = {
            **service_provider.__dict__,
            "scopes": scope_strings       
        }
        service_providers_with_scopes.append(service_provider_data)

    return service_providers_with_scopes


@router.get("/available-scopes/", response_model=List[GetAllScopesSchema])
def get_available_scopes(db: Session = Depends(get_db)):
    scopes = db.query(Scope).all()
    return scopes

@router.delete("/delete-service-providers/")
def delete_service_providers(
    service_provider_ids: List[int],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service_providers = db.query(ServiceProvider).filter(
        ServiceProvider.id.in_(service_provider_ids),
        ServiceProvider.developer_id == current_user.id
    ).all()

    if not service_providers:
        raise HTTPException(status_code=404, detail="No matching service providers found")

    for service_provider in service_providers:
        db.delete(service_provider)

    db.commit()
    return JSONResponse(status_code=200, content={"message": f"{len(service_providers)} service providers deleted"})
