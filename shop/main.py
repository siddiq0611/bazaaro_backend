from fastapi import FastAPI
from . import models
from .database import engine
from .routers import authentication, user, tenant, product, order

app = FastAPI()

models.Base.metadata.create_all(engine)

app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(tenant.router)
app.include_router(product.router)
app.include_router(order.router)