from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from . import database, models
from .keycloak_config import verify_keycloak_token, get_user_roles, check_role
from sqlalchemy.orm import Session

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(database.get_db)
):
    """Get current user from Keycloak token"""
    token = credentials.credentials
    
    token_info = verify_keycloak_token(token)
    
    email = token_info.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not found in token"
        )
    
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        roles = get_user_roles(token_info)
        is_admin = "admin" in roles
        
        user = models.User(
            name=token_info.get("name", email.split("@")[0]),
            email=email,
            password="keycloak_managed", 
            is_admin=is_admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    roles = get_user_roles(token_info)
    user.is_admin = "admin" in roles
    
    return user

def get_admin_user(current_user: models.User = Depends(get_current_user)):
    """Verify user has admin role"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action"
        )
    return current_user

def get_tenant_user(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(database.get_db)
):
    """Verify user has tenant role and get tenant info"""
    tenant = db.query(models.Tenant).filter(models.Tenant.user_id == current_user.id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant users can perform this action"
        )
    return {"user": current_user, "tenant": tenant}