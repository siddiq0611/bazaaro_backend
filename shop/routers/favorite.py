from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, database, oauth2, models
from typing import List
from ..repositories import favorite

router = APIRouter(
    prefix="/favorite",
    tags=['Favorites']
)
get_db = database.get_db

@router.post('', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowFavoriteProduct)
def add_to_favorites(
    request: schemas.FavoriteProductCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Mark a product as favorite"""
    return favorite.add_favorite(request.product_id, current_user.id, db)

@router.delete('/{product_id}', status_code=status.HTTP_200_OK)
def remove_from_favorites(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Unmark a product from favorites"""
    return favorite.remove_favorite(product_id, current_user.id, db)

@router.get('', response_model=List[schemas.ShowFavoriteProduct])
def get_my_favorites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Get all favorite products for current user"""
    return favorite.get_user_favorites(current_user.id, db)