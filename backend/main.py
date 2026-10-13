from fastapi import FastAPI

from backend.routes.shop.router import router as shop_router

app = FastAPI()

app.include_router(shop_router)
