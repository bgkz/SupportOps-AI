import json
import secrets
from uuid import UUID

from redis import Redis


class SessionsService:
    def __init__(self, redis_connection: Redis):
        self.redis = redis_connection

    def create_session(self, user_id: UUID) -> str:
        session_id = secrets.token_hex(32)

        self.redis.setex(
            name=f"session:{session_id}",
            time=86400,
            value=json.dumps({"user_id": str(user_id)}),
        )

        return session_id
