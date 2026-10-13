from uuid import UUID

from fastapi import APIRouter, Depends

from backend.security.api_key import verify_api_key

router = APIRouter(
    prefix="/shop/orders",
    dependencies=[Depends(verify_api_key)],
)


@router.post("/{order_id}/cancel")
def cancel_order(order_id: UUID):
    pass


@router.post("/")
def create_order():
    pass


@router.get("/{order_id}")
def get_order(order_id: UUID):
    pass


@router.patch("/{order_id}")
def change_order(order_id: UUID):
    pass


@router.delete("/{order_id}")
def delete_order(order_id: UUID):
    pass
