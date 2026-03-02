from fastapi import APIRouter, Depends, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from .. import schemas, database, oauth2, models
from typing import List, Optional
from ..repositories import product

router = APIRouter(
    prefix="/product",
    tags=['Product']
)
get_db = database.get_db


@router.post('/category', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowCategory)
def create_category(request: schemas.Category, db: Session = Depends(get_db), tenant_info: dict = Depends(oauth2.get_tenant_user)):
    return product.create_category(request.name, db)


@router.get('/category', response_model=List[schemas.ShowCategory])
def get_all_categories(db: Session = Depends(get_db)):
    return product.get_all_categories(db)


@router.post('', status_code=status.HTTP_201_CREATED, response_model=schemas.ShowProduct)
def create_product(
    request: schemas.Product = Depends(schemas.Product.as_form),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    tenant_info: dict = Depends(oauth2.get_tenant_user)
):
    tenant_id = tenant_info["tenant"].id
    return product.create_product(request, image, tenant_id, db)


@router.get('', response_model=List[schemas.ShowProduct])
def get_all_products(
    db: Session = Depends(get_db),
    category_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None)
):
    return product.get_all_products(db, category_id, search)


@router.get('/my-products', response_model=List[schemas.ShowProduct])
def get_my_products(db: Session = Depends(get_db), tenant_info: dict = Depends(oauth2.get_tenant_user)):
    tenant_id = tenant_info["tenant"].id
    return product.get_tenant_products(tenant_id, db)


@router.get('/{id}', response_model=schemas.ShowProduct)
def get_product(id: int, db: Session = Depends(get_db)):
    return product.get_product(id, db)


@router.put('/{id}', status_code=status.HTTP_202_ACCEPTED, response_model=schemas.ShowProduct)
def update_product(
    id: int,
    request: schemas.ProductUpdate = Depends(schemas.ProductUpdate.as_form),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    tenant_info: dict = Depends(oauth2.get_tenant_user)
):
    tenant_id = tenant_info["tenant"].id
    return product.update_product(id, request, image, tenant_id, db)


@router.delete('/{id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_product(id: int, db: Session = Depends(get_db), tenant_info: dict = Depends(oauth2.get_tenant_user)):
    tenant_id = tenant_info["tenant"].id
    return product.delete_product(id, tenant_id, db)