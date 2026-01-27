from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

app=FastAPI()

@app.get('/')
def index():
    return {'data': {'name': 'E-Commerce Application'}}

@app.get('/shop/{id}')
def about(id: int):
    return {'data': id}

class Product(BaseModel):
    name: str
    description: str
    price: float
    quantity: Optional[int]

@app.post('/product')
def create_product(request: Product):
    return {f"Product is created with name: {request.name}\nPrice: {request.price}"}