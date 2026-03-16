from fastapi import FastAPI
from . import models
from .database import engine
from .routers import authentication, user, tenant, product, order, favorite, cart
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

models.Base.metadata.create_all(engine)

app.include_router(authentication.router)
app.include_router(user.router)
app.include_router(tenant.router)
app.include_router(product.router)
app.include_router(order.router)
app.include_router(favorite.router)
app.include_router(cart.router)