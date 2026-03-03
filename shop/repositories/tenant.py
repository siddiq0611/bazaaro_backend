from sqlalchemy.orm import Session
from .. import models, schemas
from fastapi import HTTPException, status
from ..keycloak_config import user_has_realm_role

def create_tenant(request: schemas.Tenant, db: Session):
    existing_tenant = db.query(models.Tenant).filter(models.Tenant.domain==request.domain).first()
    if existing_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Domain already exists")
    
    user = db.query(models.User).filter(models.User.id == request.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {request.user_id} not found"
        )
    # 🔍 Check if user has tenant role in Keycloak
    if not user_has_realm_role(user.keycloak_id, "tenant"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have tenant role in Keycloak"
        )
    user_tenant = db.query(models.Tenant).filter(models.Tenant.user_id==request.user_id).first()
    if user_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"User already has a tenant: {user_tenant.brand_name}")
    
    new_tenant=models.Tenant(brand_name=request.brand_name, domain=request.domain, user_id=request.user_id)
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return new_tenant

def get_all_tenants(db: Session):
    tenants=db.query(models.Tenant).all()
    return tenants

def get_tenant(id: int, db: Session):
    tenant=db.query(models.Tenant).filter(models.Tenant.id==id).first()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with id {id} not found")
    return tenant

def delete_tenant(id: int, db: Session):
    tenant=db.query(models.Tenant).filter(models.Tenant.id==id)
    if not tenant.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Tenant with id {id} not found")
    tenant.delete(synchronize_session=False)
    db.commit()
    return 'done'