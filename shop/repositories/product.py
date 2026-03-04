import math
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from .. import models, schemas
from fastapi import HTTPException, status, UploadFile
from typing import Optional
import uuid, os, shutil

IMAGE_DIR = "static/images"


def _save_image(image: UploadFile) -> str:
    os.makedirs(IMAGE_DIR, exist_ok=True)
    ext = image.filename.rsplit(".", 1)[-1].lower() if image.filename else "jpg"
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(IMAGE_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(image.file, f)
    return f"/static/images/{filename}"


def _delete_image(image_url: Optional[str]):
    if not image_url:
        return
    filepath = image_url.lstrip("/")
    if os.path.exists(filepath):
        os.remove(filepath)


def _paginate(query, page: int, page_size: int) -> dict:
    """
    Helper: execute a query with offset/limit and return a PaginatedProducts-
    compatible dict.
    """
    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    page = max(1, min(page, total_pages))
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


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


def create_product(request: schemas.Product, image: Optional[UploadFile], tenant_id: int, db: Session):
    category = db.query(models.Category).filter(models.Category.id == request.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    image_url = _save_image(image) if image and image.filename else None

    new_product = models.Product(
        name=request.name,
        description=request.description,
        price=request.price,
        available_quantity=request.available_quantity,
        category_id=request.category_id,
        tenant_id=tenant_id,
        image_url=image_url,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product


def get_all_products(
    db: Session,
    category_id: int = None,
    search: str = None,
    page: int = 1,
    page_size: int = 12,
):
    query = db.query(models.Product).filter(models.Product.is_deleted == False)
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if search:
        query = query.filter(or_(
            models.Product.name.contains(search),
            models.Product.description.contains(search)
        ))
    return _paginate(query, page, page_size)


def get_products_by_tenant(
    db: Session,
    tenant_id: int,
    category_id: int = None,
    search: str = None,
    page: int = 1,
    page_size: int = 12,
):
    query = db.query(models.Product).filter(
        models.Product.tenant_id == tenant_id,
        models.Product.is_deleted == False,
    )
    if category_id:
        query = query.filter(models.Product.category_id == category_id)
    if search:
        query = query.filter(or_(
            models.Product.name.contains(search),
            models.Product.description.contains(search)
        ))
    return _paginate(query, page, page_size)


def get_product_for_tenant(id: int, tenant_id: int, db: Session):
    p = db.query(models.Product).filter(
        models.Product.id == id,
        models.Product.tenant_id == tenant_id,
        models.Product.is_deleted == False,
    ).first()
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {id} not found in this store"
        )
    return p


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


def update_product(id: int, request: schemas.ProductUpdate, image: Optional[UploadFile], tenant_id: int, db: Session):
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

    if image and image.filename:
        _delete_image(product.image_url)
        product.image_url = _save_image(image)

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
    _delete_image(product.image_url)
    product.is_deleted = True
    product.available_quantity = 0
    db.commit()
    return 'done'