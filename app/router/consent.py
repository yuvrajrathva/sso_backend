from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UserConsent, ServiceProvider, Scope
from app.schemas import GetUserConsentResponseSchema, UserSchema

router = APIRouter()

@router.get("/consent/{user_id}", response_model=GetUserConsentResponseSchema)
def get_user_consent(user_id: int, db: Session = Depends(get_db)):
    user_consents = db.query(UserConsent).filter(UserConsent.user_id == user_id).all()
    
    if not user_consents:
        raise HTTPException(status_code=404, detail="No consent data found for this user")
    
    approved_services = {}
    for consent in user_consents:
        sp = db.query(ServiceProvider).filter(ServiceProvider.id == consent.service_provider_id).first()
        scope = db.query(Scope).filter(Scope.id == consent.scope_id).first()
        
        if sp.name not in approved_services:
            approved_services[sp.name] = []
        
        approved_services[sp.name].append(scope.scope)
    
    formatted_response = {
        "user_id": user_id,
        "approved_services": [{"service_provider": sp, "scopes": scopes} for sp, scopes in approved_services.items()]
    }
    
    return formatted_response

