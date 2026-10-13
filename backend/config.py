import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")


BACKEND_API_KEY = os.getenv("BACKEND_API_KEY")
BASE_BACKEND_URL = "http://127.0.0.1:8000/"
