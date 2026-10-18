"""Shared RQ queue. Import job and call job.enqueue(function, *args)."""

from redis import Redis
from rq import Queue

from backend.config import REDIS_URL, RQ_QUEUE_NAME

redis_connection = Redis.from_url(REDIS_URL)
job = Queue(RQ_QUEUE_NAME, connection=redis_connection, default_timeout=300)
