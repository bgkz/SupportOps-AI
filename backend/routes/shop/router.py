from fastapi import APIRouter, Depends

from backend.routes.shop.orders import router as shop_orders_router
from backend.security.api_key import verify_api_key

router = APIRouter(
    prefix="/shop",
    dependencies=[Depends(verify_api_key)],
)


router.include_router(shop_orders_router)
