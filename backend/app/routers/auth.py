from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.dependencies import current_user
from ..core.security import verify_password, create_token
from ..database.connection import get_db
from ..models import User
from ..schemas import LoginRequest
from ..services.serializers import user_json

router = APIRouter()
@router.post("/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.user_id == data.user_id).first()
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(401, "Invalid user ID or password")
    return {"access_token": create_token(u), "token_type": "bearer", "user": user_json(u)}

@router.get("/auth/me")
def me(user=Depends(current_user)): return user_json(user)

