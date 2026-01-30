from sqlalchemy.orm import Session
from .. import models, schemas
from fastapi import HTTPException, status

def add_favorite(product_id: int, user_id: int, db: Session):
    """Add product to user's favorites"""
    
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    
    existing_favorite = db.query(models.FavoriteProduct).filter(
        models.FavoriteProduct.user_id == user_id,
        models.FavoriteProduct.product_id == product_id
    ).first()
    
    if existing_favorite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product already in favorites"
        )
    
    new_favorite = models.FavoriteProduct(
        user_id=user_id,
        product_id=product_id
    )
    db.add(new_favorite)
    db.commit()
    db.refresh(new_favorite)
    return new_favorite

def remove_favorite(product_id: int, user_id: int, db: Session):
    """Remove product from user's favorites"""
    
    favorite = db.query(models.FavoriteProduct).filter(
        models.FavoriteProduct.user_id == user_id,
        models.FavoriteProduct.product_id == product_id
    ).first()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found in favorites"
        )
    
    db.delete(favorite)
    db.commit()
    return {"message": "Product removed from favorites"}

def get_user_favorites(user_id: int, db: Session):
    """Get all favorite products for a user"""
    
    favorites = db.query(models.FavoriteProduct).filter(
        models.FavoriteProduct.user_id == user_id
    ).all()
    
    return favorites