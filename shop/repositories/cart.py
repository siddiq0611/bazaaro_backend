from sqlalchemy.orm import Session
from .. import models
from fastapi import HTTPException, status


def get_or_create_cart(user_id: int, db: Session) -> models.Cart:
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        cart = models.Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart


def get_cart(user_id: int, db: Session):
    return get_or_create_cart(user_id, db)


def upsert_item(user_id: int, product_id: int, quantity: int, db: Session):
    """Add or update a cart item. quantity=0 removes it."""
    product = db.query(models.Product).filter(
        models.Product.id == product_id,
        models.Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    cart = get_or_create_cart(user_id, db)

    item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == cart.id,
        models.CartItem.product_id == product_id
    ).first()

    if quantity <= 0:
        if item:
            db.delete(item)
            db.commit()
        return get_cart(user_id, db)

    clamped_qty = min(quantity, product.available_quantity)

    if item:
        item.quantity = clamped_qty
    else:
        item = models.CartItem(cart_id=cart.id, product_id=product_id, quantity=clamped_qty)
        db.add(item)

    db.commit()
    db.refresh(cart)
    return cart


def remove_item(user_id: int, product_id: int, db: Session):
    cart = get_or_create_cart(user_id, db)
    item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == cart.id,
        models.CartItem.product_id == product_id
    ).first()
    if item:
        db.delete(item)
        db.commit()
    db.refresh(cart)
    return cart


def clear_cart(user_id: int, db: Session):
    cart = get_or_create_cart(user_id, db)
    db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
    db.commit()
    db.refresh(cart)
    return cart