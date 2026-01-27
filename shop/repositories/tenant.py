from sqlalchemy.orm import Session
from .. import models, schemas
from fastapi import HTTPException, status

def create_tenant(request: schemas.Tenant, user_id: int, db: Session):
    existing_tenant = db.query(models.Tenant).filter(models.Tenant.domain==request.domain).first()
    if existing_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Domain already exists")
    
    user_tenant = db.query(models.Tenant).filter(models.Tenant.user_id==user_id).first()
    if user_tenant:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already has a tenant")
    
    new_tenant=models.Tenant(brand_name=request.brand_name, domain=request.domain, user_id=user_id)
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