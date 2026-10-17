from sqlalchemy.orm import Session


class TicketsRepository:
    def __init__(self, db: Session):
        self.db = db
