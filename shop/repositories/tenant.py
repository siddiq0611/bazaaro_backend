from sqlalchemy.orm import Session
from .. import models, schemas
from fastapi import HTTPException, status
from ..keycloak_config import user_has_realm_role


def create_tenant(request: schemas.Tenant, db: Session):

    existing_tenant = db.query(models.Tenant).filter(
        models.Tenant.domain == request.domain
    ).first()

    user = db.query(models.User).filter(
        models.User.id == request.user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {request.user_id} not found"
        )

    if not user_has_realm_role(user.keycloak_id, "tenant"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have tenant role in Keycloak"
        )

    if existing_tenant and not existing_tenant.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain already exists"
        )

    if existing_tenant and existing_tenant.is_deleted:
        user_tenant = db.query(models.Tenant).filter(
            models.Tenant.user_id == request.user_id,
            models.Tenant.is_deleted == False
        ).first()

        if user_tenant:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User already has a tenant: {user_tenant.brand_name}"
            )

        existing_tenant.is_deleted = False
        existing_tenant.brand_name = request.brand_name
        existing_tenant.user_id = request.user_id
        db.commit()
        db.refresh(existing_tenant)
        return existing_tenant

    user_tenant = db.query(models.Tenant).filter(
        models.Tenant.user_id == request.user_id,
        models.Tenant.is_deleted == False
    ).first()

    if user_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User already has a tenant: {user_tenant.brand_name}"
        )

    new_tenant = models.Tenant(
        brand_name=request.brand_name,
        domain=request.domain,
        user_id=request.user_id
    )

    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)

    return new_tenant


def get_all_tenants(db: Session):
    return db.query(models.Tenant).filter(
        models.Tenant.is_deleted == False
    ).all()


def get_tenant(id: int, db: Session):
    tenant = db.query(models.Tenant).filter(
        models.Tenant.id == id,
        models.Tenant.is_deleted == False
    ).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with id {id} not found"
        )
    return tenant


def delete_tenant(id: int, db: Session):
    tenant = db.query(models.Tenant).filter(
        models.Tenant.id == id,
        models.Tenant.is_deleted == False
    ).first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant with id {id} not found"
        )

    tenant.is_deleted = True

    db.query(models.Product).filter(
        models.Product.tenant_id == tenant.id,
        models.Product.is_deleted == False
    ).update({"is_deleted": True})

    db.commit()

    return {"message": "Tenant and its products soft deleted"}