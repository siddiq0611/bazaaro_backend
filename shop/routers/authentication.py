# from fastapi import APIRouter, Depends, HTTPException, status
# from .. import database, models, token
# from sqlalchemy.orm import Session
# from ..hashing import Hash
# from fastapi.security import OAuth2PasswordRequestForm

# router=APIRouter(
#     tags=["Authentication"]
# )

# @router.post('/login')
# def login(request: OAuth2PasswordRequestForm=Depends(), db: Session=Depends(database.get_db)):
#     user= db.query(models.User).filter(models.User.email==request.username).first()
#     if not user:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invalid Credentials")
#     if not Hash.verify(user.password, request.password):
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Incorrect Password")
#     access_token = token.create_access_token(data={"sub": user.email})
#     return {"access_token": access_token, "token_type": "bearer"}

from fastapi import APIRouter, Depends, HTTPException, status, Form
from .. import schemas, oauth2
from ..keycloak_config import keycloak_openid

router = APIRouter(
    tags=["Authentication"]
)

@router.post('/login', response_model=schemas.Token)
def login(username: str = Form(...), password: str = Form(...)):
    """Login using Keycloak"""
    try:
        token = keycloak_openid.token(username, password)
        
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