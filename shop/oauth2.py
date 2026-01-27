from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from . import token, database, models
from sqlalchemy.orm import Session

oauth2_scheme=OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(data: str= Depends(oauth2_scheme), db: Session=Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = token.verify_token(data, credentials_exception)
    user = db.query(models.User).filter(models.User.email==token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

def get_admin_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can perform this action"
        )
    return current_user

def get_tenant_user(current_user: models.User = Depends(get_current_user), db: Session=Depends(database.get_db)):
    tenant = db.query(models.Tenant).filter(models.Tenant.user_id==current_user.id).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant users can perform this action"
        )
    return {"user": current_user, "tenant": tenant}