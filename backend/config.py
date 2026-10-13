import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")
BASE_BACKEND_URL = "http://127.0.0.1:8000/"
DATABASE_URL = os.getenv("DATABASE_URL")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_NAME = os.getenv("DATABASE_NAME")

ORDER_NUMBER_MAX_LENGTH = 10
PASSWORD_MIN_LENGTH = 12
