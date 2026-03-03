from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from . import database, models
from .keycloak_config import verify_keycloak_token, get_user_roles
from sqlalchemy.orm import Session

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(database.get_db)
):
    token = credentials.credentials
    token_info = verify_keycloak_token(token)

    email = token_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not found in token"
        )

    keycloak_id = token_info.get("sub")

    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        user = models.User(
            name=token_info.get("name", email.split("@")[0]),
            email=email,
            password="keycloak_managed",
            keycloak_id=keycloak_id
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.keycloak_id = keycloak_id
        db.commit()

    return user

def get_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials
    token_info = verify_keycloak_token(token)

    roles = get_user_roles(token_info)

    if "admin" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action"
        )

    return token_info

def get_tenant_user(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    tenant = db.query(models.Tenant).filter(models.Tenant.user_id == current_user.id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant users can perform this action"
        )
    return {"user": current_user, "tenant": tenant}