from .. import models
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

def get_user(id: int, db: Session):
    user=db.query(models.User).filter(models.User.id==id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id {id} is not available")
    return user

def get_all_users(db: Session):
    return db.query(models.User).all()