from pydantic import BaseModel, Field, ValidationError, model_validator, field_validator
from typing import List, Optional, Any
from datetime import datetime, timezone
from fastapi import Form, HTTPException, UploadFile, File, status


class SignUp(BaseModel):
    first_name: str
    last_name: str
    username: str
    email: str
    password: str


class ShowUser(BaseModel):
    id: int
    name: str
    email: str

    class Config():
        from_attributes = True


class Tenant(BaseModel):
    brand_name: str
    domain: str
    user_id: int

class ShowTenant(BaseModel):
    id: int
    brand_name: str
    domain: str
    user: ShowUser
    class Config():
        from_attributes = True


class Category(BaseModel):
    name: str


class ShowCategory(BaseModel):
    id: int
    name: str
    class Config():
        from_attributes = True


class Product(BaseModel):
    name: str
    description: str
    price: float = Field(..., gt=0,  description="Price must be greater than 0")
    available_quantity: int =Field(..., ge=0,  description="Quantity cannot be negative")
    category_id: int

    @classmethod
    def as_form(
        cls,
        name: str               = Form(...),
        description: str        = Form(""),
        price: float            = Form(...),
        available_quantity: int = Form(...),
        category_id: int        = Form(...),
    ) -> "Product":
        try:
            return cls(
                name=name,
                description=description,
                price=price,
                available_quantity=available_quantity,
                category_id=category_id,
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors()
            )


class ProductUpdate(BaseModel):
    name: Optional[str]               = None
    description: Optional[str]        = None
    price: Optional[float]            = Field(None, gt=0, description="Price must be greater than 0")
    available_quantity: Optional[int] = Field(None, ge=0, description="Quantity cannot be negative")
    category_id: Optional[int]        = None

    @classmethod
    def as_form(
        cls,
        name: Optional[str]               = Form(None),
        description: Optional[str]        = Form(None),
        price: Optional[float]            = Form(None),
        available_quantity: Optional[int] = Form(None),
        category_id: Optional[int]        = Form(None),
    ) -> "ProductUpdate":
        try:
            return cls(
                name=name,
                description=description,
                price=price,
                available_quantity=available_quantity,
                category_id=category_id,
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=e.errors()
            )


class ShowProduct(BaseModel):
    id: int
    name: str
    description: str
    price: float
    available_quantity: int
    image_url: Optional[str] = None
    category: ShowCategory
    tenant: ShowTenant
    class Config():
        from_attributes = True


class PaginatedProducts(BaseModel):
    items: List[ShowProduct]
    total: int       
    page: int       
    page_size: int   
    total_pages: int 

    class Config():
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int


class ShowOrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    product_name: str = ""
    image_url: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def pull_product_name(cls, obj: Any) -> Any:
        if hasattr(obj, "product") and obj.product is not None:
            return {
                "id": obj.id,
                "product_id": obj.product_id,
                "quantity": obj.quantity,
                "price": obj.price,
                "product_name": obj.product.name,
                "image_url": getattr(obj.product, "image_url", None)
            }
        return obj

    class Config():
        from_attributes = True


class OrderCreate(BaseModel):
    order_items: List[OrderItemCreate]


class ShowOrder(BaseModel):
    id: int
    total_quantity: int
    total_amount: float
    created_at: datetime
    order_items: List[ShowOrderItem]

    @field_validator("created_at", mode="before")
    @classmethod
    def ensure_utc(cls, v: Any) -> datetime:
        if isinstance(v, datetime) and v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    class Config():
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class FavoriteProductCreate(BaseModel):
    product_id: int


class ShowFavoriteProduct(BaseModel):
    id: int
    product_id: int
    created_at: datetime
    product: ShowProduct
    class Config():
        from_attributes = True


class CartItemUpsert(BaseModel):
    product_id: int
    quantity: int

class ShowCartItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    product: ShowProduct

    class Config():
        from_attributes = True

class ShowCart(BaseModel):
    id: int
    items: List[ShowCartItem]

    class Config():
        from_attributes = True