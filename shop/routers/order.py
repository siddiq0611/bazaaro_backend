from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, database, oauth2, models
from typing import List
from ..repositories import order

router = APIRouter(
    prefix="/order",
    tags=['Order']
)
get_db=database.get_db

@router.post('', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowOrder)
def create_order(request: schemas.OrderCreate, db: Session=Depends(get_db), current_user: models.User=Depends(oauth2.get_current_user)):
    return order.create_order(request, current_user.id, db)

@router.get('', response_model=List[schemas.ShowOrder])
def get_my_orders(db: Session=Depends(get_db), current_user: models.User=Depends(oauth2.get_current_user)):
    return order.get_user_orders(current_user.id, db)

# @router.get('/{id}', response_model=schemas.ShowOrder)
# def get_order(id: int, db: Session=Depends(get_db), current_user: models.User=Depends(oauth2.get_current_user)):
#     return order.get_order(id, current_user.id, db)