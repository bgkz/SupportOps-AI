from fastapi import APIRouter, status

router = APIRouter(prefix="/auth")


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register():
    pass
