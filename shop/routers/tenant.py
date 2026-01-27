from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, database, oauth2, models
from typing import List
from ..repositories import tenant

router = APIRouter(
    prefix="/tenant",
    tags=['Tenant']
)
get_db=database.get_db

@router.post('', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowTenant)
def create_tenant(request: schemas.Tenant, db: Session=Depends(get_db), admin: models.User=Depends(oauth2.get_admin_user)):
    user_id = admin.id
    return tenant.create_tenant(request, user_id, db)

@router.get('', response_model=List[schemas.ShowTenant])
def get_all_tenants(db: Session=Depends(get_db), admin: models.User=Depends(oauth2.get_admin_user)):
    return tenant.get_all_tenants(db)

@router.get('/{id}', response_model=schemas.ShowTenant)
def get_tenant(id: int, db: Session=Depends(get_db), current_user: models.User=Depends(oauth2.get_current_user)):
    return tenant.get_tenant(id, db)

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(id: int, db: Session=Depends(get_db), admin: models.User=Depends(oauth2.get_admin_user)):
    return tenant.delete_tenant(id, db)