from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class User(BaseModel):
    name: str
    email: str
    password: str

class ShowUser(BaseModel):
    id: int
    name: str
    email: str
    is_admin: bool
    class Config():
        from_attributes=True

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
        from_attributes=True

class Category(BaseModel):
    name: str

class ShowCategory(BaseModel):
    id: int
    name: str
    class Config():
        from_attributes=True

class Product(BaseModel):
    name: str
    description: str
    price: float
    available_quantity: int
    category_id: int

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    available_quantity: Optional[int] = None
    category_id: Optional[int] = None

class ShowProduct(BaseModel):
    id: int
    name: str
    description: str
    price: float
    available_quantity: int
    category: ShowCategory
    tenant: ShowTenant
    class Config():
        from_attributes=True

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int

class ShowOrderItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: float
    class Config():
        from_attributes=True

class OrderCreate(BaseModel):
    order_items: List[OrderItemCreate]

class ShowOrder(BaseModel):
    id: int
    total_quantity: int
    total_amount: float
    created_at: datetime
    order_items: List[ShowOrderItem]
    class Config():
        from_attributes=True

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class FavoriteProductCreate(BaseModel):
    product_id: int

class ShowFavoriteProduct(BaseModel):
    id: int
    product_id: int
    created_at: datetime
    product: ShowProduct
    class Config():
        from_attributes=True