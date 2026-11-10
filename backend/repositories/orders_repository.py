from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.exceptions.orders import OrderRetrievalError
from backend.models.orders import Orders


class OrdersRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_user_id(self, user_id: UUID) -> list[Orders]:
        try:
            statement = (
                select(Orders)
                .where(Orders.user_id == user_id)
                .order_by(Orders.created_at.desc())
            )
            return list(self.db.execute(statement).scalars().all())

        except SQLAlchemyError as error:
            raise OrderRetrievalError("Orders could not be retrieved") from error

    def get_by_order_number_and_user_id(
        self,
        order_number: str,
        user_id: UUID,
    ) -> Orders | None:
        try:
            statement = select(Orders).where(
                Orders.user_id == user_id, Orders.order_number == order_number
            )
            return self.db.execute(statement=statement).scalar_one_or_none()
        except SQLAlchemyError as error:
            raise OrderRetrievalError("Order could not be retrieved") from error

    def get_by_order_number(self, order_number: str, user_id: UUID) -> Orders | None:
        statement = select(Orders).where(
            Orders.order_number == order_number,
            Orders.user_id == user_id,
        )
        try:
            return self.db.execute(statement).scalar_one_or_none()
        except SQLAlchemyError as error:
            raise OrderRetrievalError("Order could not be retrieved") from error
