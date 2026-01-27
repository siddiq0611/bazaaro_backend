from sqlalchemy.orm import Session
from .. import models, schemas
from fastapi import HTTPException, status

def create_order(request: schemas.OrderCreate, user_id: int, db: Session):
    if not request.order_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order must contain at least one item")
    
    total_quantity = 0
    total_amount = 0.0
    order_items_data = []
    
    for item in request.order_items:
        product = db.query(models.Product).filter(models.Product.id==item.product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product with id {item.product_id} not found")
        
        if item.quantity > product.available_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail=f"Product {product.name} has only {product.available_quantity} items available"
            )
        
        item_total = product.price * item.quantity
        total_quantity += item.quantity
        total_amount += item_total
        
        order_items_data.append({
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price": product.price,
            "product": product
        })
    
    new_order = models.Order(
        user_id=user_id,
        total_quantity=total_quantity,
        total_amount=total_amount
    )
    db.add(new_order)
    db.flush()
    
    for item_data in order_items_data:
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=item_data["product_id"],
            quantity=item_data["quantity"],
            price=item_data["price"]
        )
        db.add(order_item)
        
        product = item_data["product"]
        product.available_quantity -= item_data["quantity"]
    
    db.commit()
    db.refresh(new_order)
    return new_order

def get_user_orders(user_id: int, db: Session):
    orders = db.query(models.Order).filter(models.Order.user_id==user_id).all()
    return orders

def get_order(order_id: int, user_id: int, db: Session):
    order = db.query(models.Order).filter(models.Order.id==order_id, models.Order.user_id==user_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order with id {order_id} not found")
    return order