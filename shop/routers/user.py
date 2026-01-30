from fastapi import APIRouter, Depends
from .. import schemas, database, oauth2, models
from sqlalchemy.orm import Session
from ..repositories import user

router = APIRouter(
    prefix="/user",
    tags=['User']
)
get_db = database.get_db

@router.get('/me', response_model=schemas.ShowUser)
def get_current_user_info(current_user: models.User = Depends(oauth2.get_current_user)):
    """Get current logged-in user info"""
    return current_user

@router.get('/{id}', response_model=schemas.ShowUser)
def get_user(
    id: int, 
    db: Session = Depends(get_db), 
    admin: models.User = Depends(oauth2.get_admin_user)
):
    """Get user by ID (admin only)"""
    return user.get_user(id, db)

@router.get(
    "/",
    response_model=list[schemas.ShowUser]
)
def get_all_users(
    db: Session = Depends(get_db),
    admin: models.User = Depends(oauth2.get_admin_user)
):
    """
    Get all users (admin only)
    """
    return user.get_all_users(db)