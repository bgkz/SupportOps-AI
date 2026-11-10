from fastapi import Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories.orders_repository import OrdersRepository
from backend.services.orders_service import OrdersService


def get_orders_service(
    db: Session = Depends(get_db),  # noqa: B008
) -> OrdersService:
    return OrdersService(orders_repo=OrdersRepository(db))
