from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from .. import schemas, oauth2, database, models
from ..keycloak_config import keycloak_openid, verify_keycloak_token, get_user_roles

router = APIRouter(
    tags=["Authentication"]
)

@router.post('/login', response_model=schemas.Token)
def login(
    username: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(database.get_db)
):
    """Login using Keycloak"""
    try:
        # 1. Get token from Keycloak
        token = keycloak_openid.token(username, password)
        
        # 2. Sync user to database immediately if they don't exist
        access_token = token['access_token']
        # Verify/decode locally to get user info (email, roles, etc.)
        token_info = verify_keycloak_token(access_token)
        
        email = token_info.get("email")
        if email:
            user = db.query(models.User).filter(models.User.email == email).first()
            
            # Create user if not found
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
        
        return {
            "access_token": token['access_token'],
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

@router.post('/logout')
def logout(current_user = Depends(oauth2.get_current_user)):
    """Logout - just remove the token from client side"""
    return {
        "message": "Successfully logged out. Please remove your access token."
    }