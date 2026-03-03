from .database import Base
from sqlalchemy import Column, Integer, String, ForeignKey, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class User(Base):
    __tablename__='users'
    id= Column(Integer, primary_key=True, index=True)
    name=Column(String)
    email=Column(String, unique=True, index=True)
    password=Column(String)
    keycloak_id = Column(String, unique=True, index=True)
    orders = relationship('Order', back_populates="user")

class Tenant(Base):
    __tablename__='tenants'
    id= Column(Integer, primary_key=True, index=True)
    brand_name=Column(String)
    domain=Column(String, unique=True, index=True)
    user_id=Column(Integer, ForeignKey("users.id"))

    is_deleted = Column(Boolean, default=False)
    user=relationship("User")
    products = relationship('Product', back_populates="tenant")

class Category(Base):
    __tablename__='categories'
    id= Column(Integer, primary_key=True, index=True)
    name=Column(String, unique=True)
    products = relationship('Product', back_populates="category")

class Product(Base):
    __tablename__='products'
    id= Column(Integer, primary_key=True, index=True)
    name=Column(String)
    description=Column(String)
    price=Column(Float)
    available_quantity=Column(Integer)
    category_id=Column(Integer, ForeignKey("categories.id"))
    tenant_id=Column(Integer, ForeignKey("tenants.id"))
    is_deleted = Column(Boolean, default=False)
    image_url = Column(String, nullable=True)
    category=relationship("Category", back_populates="products")
    tenant=relationship("Tenant", back_populates="products")
    order_items = relationship('OrderItem', back_populates="product")

class Order(Base):
    __tablename__='orders'
    id= Column(Integer, primary_key=True, index=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    total_quantity=Column(Integer)
    total_amount=Column(Float)
    created_at=Column(DateTime, default=datetime.utcnow)
    user=relationship("User", back_populates="orders")
    order_items = relationship('OrderItem', back_populates="order")

class OrderItem(Base):
    __tablename__='order_items'
    id= Column(Integer, primary_key=True, index=True)
    order_id=Column(Integer, ForeignKey("orders.id"))
    product_id=Column(Integer, ForeignKey("products.id"))
    quantity=Column(Integer)
    price=Column(Float)
    order=relationship("Order", back_populates="order_items")
    product=relationship("Product", back_populates="order_items")

class FavoriteProduct(Base):
    __tablename__='favorite_products'
    id= Column(Integer, primary_key=True, index=True)
    user_id=Column(Integer, ForeignKey("users.id"))
    product_id=Column(Integer, ForeignKey("products.id"))
    created_at=Column(DateTime, default=datetime.utcnow)
    
    user=relationship("User")
    product=relationship("Product")