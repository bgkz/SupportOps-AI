from fastapi import FastAPI

from backend.routes.shop.router import router as shop_router
from backend.routes.users import router as users_router

app = FastAPI()

app.include_router(shop_router)
app.include_router(users_router)
