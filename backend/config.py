import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")
BASE_BACKEND_URL = os.getenv("BASE_BACKEND_URL", "http://127.0.0.1:8000/")
DATABASE_URL = os.getenv("DATABASE_URL")
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
RQ_QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "default")
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")


MAIL_BACKEND = os.getenv("MAIL_BACKEND", "resend")
SMTP_HOST = os.getenv("SMTP_HOST", "127.0.0.1")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))

TICKET_CLASSIFICATION_CONFIDENCE_THRESHOLD = 0.8
TICKET_TEXT_MIN_LENGTH = 10
TICKET_TEXT_MAX_LENGTH = 1000

ORDER_NUMBER_MAX_LENGTH = 10
PASSWORD_MIN_LENGTH = 12


QDRANT_CLIENT_URL = "http://localhost:6333"
QDRANT_COLLECTION_NAME = "support_knowledge"


GPT_MODEL = "gpt-6-luna"
