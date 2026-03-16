from sqlalchemy.orm import Session
from .. import models, schemas
from fastapi import HTTPException, status
from ..keycloak_config import swap_realm_role
import re 

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

    if not user.keycloak_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User has no linked Keycloak account"
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

        swap_realm_role(user.keycloak_id, remove_role="customer", add_role="tenant")

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

    swap_realm_role(user.keycloak_id, remove_role="customer", add_role="tenant")

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

    user = db.query(models.User).filter(
        models.User.id == tenant.user_id
    ).first()

    tenant.is_deleted = True

    db.query(models.Product).filter(
        models.Product.tenant_id == tenant.id,
        models.Product.is_deleted == False
    ).update({"is_deleted": True})

    db.commit()

    if user and user.keycloak_id:
        swap_realm_role(user.keycloak_id, remove_role="tenant", add_role="customer")

    return {"message": "Tenant and its products soft deleted"}


def create_tenant_request(request: schemas.TenantRequestCreate, db: Session, current_user: models.User):
    # Domain format validation
    if not re.match(r'^[a-z0-9.-]+$', request.domain):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain can only contain lowercase letters, numbers, hyphens, and dots"
        )

# Brand name format validation — was missing, add this
    if not re.match(r'^[a-zA-Z0-9\s\-]+$', request.brand_name.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand name can only contain letters, numbers, spaces, and hyphens"
        )

    # Brand name length
    if len(request.brand_name.strip()) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand name must be at least 2 characters"
        )

    if len(request.brand_name.strip()) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand name cannot exceed 50 characters"
        )

    # Brand name already taken by an active tenant
    brand_taken = db.query(models.Tenant).filter(
        models.Tenant.brand_name.ilike(request.brand_name.strip()),
        models.Tenant.is_deleted == False
    ).first()
    if brand_taken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This brand name is already taken"
        )

    # Brand name already in a pending request
    brand_requested = db.query(models.TenantRequest).filter(
        models.TenantRequest.brand_name.ilike(request.brand_name.strip()),
        models.TenantRequest.status == "pending"
    ).first()
    if brand_requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This brand name already has a pending request"
        )

    # User already has an active tenant
    existing_tenant = db.query(models.Tenant).filter(
        models.Tenant.user_id == current_user.id,
        models.Tenant.is_deleted == False
    ).first()
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an active tenant"
        )

    # User already has a pending request
    existing_request = db.query(models.TenantRequest).filter(
        models.TenantRequest.user_id == current_user.id,
        models.TenantRequest.status == "pending"
    ).first()
    if existing_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending request"
        )

    # Domain already taken by an active tenant
    domain_taken = db.query(models.Tenant).filter(
        models.Tenant.domain == request.domain,
        models.Tenant.is_deleted == False
    ).first()
    if domain_taken:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This domain is already taken"
        )

    # Domain already in a pending request
    domain_requested = db.query(models.TenantRequest).filter(
        models.TenantRequest.domain == request.domain,
        models.TenantRequest.status == "pending"
    ).first()
    if domain_requested:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This domain already has a pending request"
        )

    new_request = models.TenantRequest(
        user_id=current_user.id,
        brand_name=request.brand_name.strip(),
        domain=request.domain,
        status="pending"
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request


def get_my_tenant_request(db: Session, current_user: models.User):
    return db.query(models.TenantRequest).filter(
        models.TenantRequest.user_id == current_user.id
    ).order_by(models.TenantRequest.created_at.desc()).first()


def get_all_tenant_requests(db: Session):
    return db.query(models.TenantRequest).filter(
        models.TenantRequest.status == "pending"
    ).order_by(models.TenantRequest.created_at.desc()).all()


def accept_tenant_request(request_id: int, db: Session):
    req = db.query(models.TenantRequest).filter(
        models.TenantRequest.id == request_id
    ).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already processed"
        )

    # Race condition — user became a tenant between request and acceptance
    already_tenant = db.query(models.Tenant).filter(
        models.Tenant.user_id == req.user_id,
        models.Tenant.is_deleted == False
    ).first()
    if already_tenant:
        req.status = "declined"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a tenant — request auto-declined"
        )

    # Race condition — domain was taken between request and acceptance
    domain_taken = db.query(models.Tenant).filter(
        models.Tenant.domain == req.domain,
        models.Tenant.is_deleted == False
    ).first()
    if domain_taken:
        req.status = "declined"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain was taken before this request was accepted — request auto-declined"
        )

    # Race condition — brand name was taken between request and acceptance
    brand_taken = db.query(models.Tenant).filter(
        models.Tenant.brand_name.ilike(req.brand_name),
        models.Tenant.is_deleted == False
    ).first()
    if brand_taken:
        req.status = "declined"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand name was taken before this request was accepted — request auto-declined"
        )

    tenant_schema = schemas.Tenant(
        brand_name=req.brand_name,
        domain=req.domain,
        user_id=req.user_id
    )

    try:
        create_tenant(tenant_schema, db)
        req.status = "accepted"
        db.commit()
        db.refresh(req)
        return req
    except IntegrityError:
        db.rollback()
        req.status = "declined"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A conflict occurred while creating the tenant — request auto-declined"
        )


def decline_tenant_request(request_id: int, db: Session):
    req = db.query(models.TenantRequest).filter(
        models.TenantRequest.id == request_id
    ).first()
    if not req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )
    if req.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request already processed"
        )
    req.status = "declined"
    db.commit()
    db.refresh(req)
    return req