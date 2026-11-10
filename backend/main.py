from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes.auth import router as auth_router
from backend.routes.tickets import router as tickets_router
from backend.routes.users import router as users_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["POST"],
    allow_headers=["Content-Type", "X-API-Key"],
    allow_credentials=True,
)

app.include_router(users_router)
app.include_router(tickets_router)
app.include_router(auth_router)
