import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from .database import get_db
from .models import User

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer = HTTPBearer()

def hash_password(password): return pwd_context.hash(password)
def verify_password(password, hashed): return pwd_context.verify(password, hashed)

def create_token(user):
    payload = {"sub": str(user.id), "role": user.role,
               "exp": datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def current_user(creds: HTTPAuthorizationCredentials = Depends(bearer),
                 db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(creds.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        uid = int(payload["sub"])
    except (JWTError, ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.get(User, uid)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_roles(*roles):
    def dependency(user=Depends(current_user)):
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return user
    return dependency
