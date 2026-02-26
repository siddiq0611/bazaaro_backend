from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from .. import models, schemas
from fastapi import HTTPException, status


def create_category(name: str, db: Session):
    new_category = models.Category(name=name)
    db.add(new_category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category already exists")
    db.refresh(new_category)
    return new_category


def get_all_categories(db: Session):
    return db.query(models.Category).all()


def create_product(request: schemas.Product, tenant_id: int, db: Session):
    category = db.query(models.Category).filter(models.Category.id == request.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    new_product = models.Product(
        name=request.name,
        description=request.description,
        price=request.price,
        available_quantity=request.available_quantity,
        category_id=request.category_id,
        tenant_id=tenant_id
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def get_all_products(db: Session, category_id: int = None, search: str = None):
    query = db.query(models.Product).filter(models.Product.is_deleted == False)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if search:
        query = query.filter(or_(
            models.Product.name.contains(search),
            models.Product.description.contains(search)
        ))
    return query.all()


def get_tenant_products(tenant_id: int, db: Session):
    return db.query(models.Product).filter(
        models.Product.tenant_id == tenant_id,
        models.Product.is_deleted == False
    ).all()


def get_product(id: int, db: Session):
    product = db.query(models.Product).filter(
        models.Product.id == id,
        models.Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {id} is not available")
    return product


def update_product(id: int, request: schemas.ProductUpdate, tenant_id: int, db: Session):
    product = db.query(models.Product).filter(
        models.Product.id == id,
        models.Product.tenant_id == tenant_id,
        models.Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {id} not found or not owned by tenant")
    update_data = request.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete_product(id: int, tenant_id: int, db: Session):
    product = db.query(models.Product).filter(
        models.Product.id == id,
        models.Product.tenant_id == tenant_id,
        models.Product.is_deleted == False
    ).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {id} not found or not owned by tenant")
    product.is_deleted = True
    product.available_quantity = 0
    db.commit()
    return 'done'