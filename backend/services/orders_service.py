from uuid import UUID

from backend.exceptions.orders import OrderNotFoundError
from backend.models.orders import Orders
from backend.repositories.orders_repository import OrdersRepository


class OrdersService:
    def __init__(self, orders_repo: OrdersRepository) -> None:
        self.orders_repo = orders_repo

    def get_orders_by_user(self, user_id: UUID) -> list[Orders]:
        return self.orders_repo.get_by_user_id(user_id=user_id)

    def get_order_for_user(self, order_number: str, user_id: UUID) -> Orders:
        order = self.orders_repo.get_by_order_number_and_user_id(
            order_number=order_number, user_id=user_id
        )
        if order is None:
            raise OrderNotFoundError(f"Order: {order_number} not found")
        return order
