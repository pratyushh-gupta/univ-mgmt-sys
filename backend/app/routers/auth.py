from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from ..core.dependencies import current_user
from ..core.security import verify_password, create_token
from ..database.connection import get_db
from ..models import User
from ..schemas import LoginRequest
from ..services.serializers import user_json
from ..services.domain import audit_event, commit_or_conflict

router = APIRouter()
@router.post("/auth/login")
def login(data: LoginRequest, request: Request, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.user_id == data.user_id).first()
    if not u or not u.is_active or not verify_password(data.password, u.password_hash):
        raise HTTPException(401, "Invalid user ID or password")
    audit_event(db, user=u, action="auth.login", entity_type="user", entity_id=u.id, request=request)
    commit_or_conflict(db)
    return {"access_token": create_token(u), "token_type": "bearer", "user": user_json(u)}

@router.get("/auth/me")
def me(user=Depends(current_user)): return user_json(user)

