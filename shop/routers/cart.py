from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from .. import schemas, database, oauth2, models
from ..repositories import cart

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)
get_db = database.get_db


@router.get('', response_model=schemas.ShowCart)
def get_my_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return cart.get_cart(current_user.id, db)


@router.put('/item', response_model=schemas.ShowCart)
def upsert_cart_item(
    request: schemas.CartItemUpsert,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Set quantity for a product. Send quantity=0 to remove."""
    return cart.upsert_item(current_user.id, request.product_id, request.quantity, db)


@router.delete('/item/{product_id}', response_model=schemas.ShowCart)
def remove_cart_item(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return cart.remove_item(current_user.id, product_id, db)


@router.delete('', response_model=schemas.ShowCart)
def clear_my_cart(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    return cart.clear_cart(current_user.id, db)