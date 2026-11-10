from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends

from backend.dependencies.auth import get_current_user
from backend.dependencies.orders import get_orders_service
from backend.exceptions.orders import OrderRetrievalError
from backend.models.orders import Orders
from backend.models.users import Users
from backend.services.orders_service import OrdersService

router = APIRouter(prefix="/orders")


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_orders(
    user_id: UUID,
    current_user: Users = Depends(get_current_user),  # noqa: B008
    orders_service: OrdersService = Depends(get_orders_service),  # noqa: B008
):

    try:
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied"
            )
        return orders_service.get_orders_by_user(user_id=user_id)

    except OrderRetrievalError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)
        )
