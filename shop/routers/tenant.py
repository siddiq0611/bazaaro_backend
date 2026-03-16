from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, database, oauth2, models
from typing import List, Optional
from ..repositories import tenant

router = APIRouter(
    prefix="/tenant",
    tags=['Tenant']
)
get_db=database.get_db

@router.post('/request', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowTenantRequest)
def apply_for_tenant(request: schemas.TenantRequestCreate, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    return tenant.create_tenant_request(request, db, current_user)


@router.get('/request/me', response_model=Optional[schemas.ShowTenantRequest])
def get_my_request(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    return tenant.get_my_tenant_request(db, current_user)


@router.get('/requests', response_model=List[schemas.ShowTenantRequest])
def get_all_requests(db: Session = Depends(get_db), admin: models.User = Depends(oauth2.get_admin_user)):
    return tenant.get_all_tenant_requests(db)


@router.put('/request/{request_id}/accept', response_model=schemas.ShowTenantRequest)
def accept_request(request_id: int, db: Session = Depends(get_db), admin: models.User = Depends(oauth2.get_admin_user)):
    return tenant.accept_tenant_request(request_id, db)


@router.put('/request/{request_id}/decline', response_model=schemas.ShowTenantRequest)
def decline_request(request_id: int, db: Session = Depends(get_db), admin: models.User = Depends(oauth2.get_admin_user)):
    return tenant.decline_tenant_request(request_id, db)

@router.post('', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowTenant)
def create_tenant(request: schemas.Tenant, db: Session=Depends(get_db), admin: models.User=Depends(oauth2.get_admin_user)):
    return tenant.create_tenant(request, db)

@router.get('', response_model=List[schemas.ShowTenant])
def get_all_tenants(db: Session=Depends(get_db), admin: models.User=Depends(oauth2.get_admin_user)):
    return tenant.get_all_tenants(db)

@router.get('/{id}', response_model=schemas.ShowTenant)
def get_tenant(id: int, db: Session=Depends(get_db), current_user: models.User=Depends(oauth2.get_current_user)):
    return tenant.get_tenant(id, db)

@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_tenant(id: int, db: Session=Depends(get_db), admin: models.User=Depends(oauth2.get_admin_user)):
    return tenant.delete_tenant(id, db)