from datetime import datetime, timedelta
from typing import Optional, Any, List
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext

from models.db_models import User, RoleEnum, AuditLog, Notification

# ---------------------------
# CONFIG
# ---------------------------
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
JWT_SECRET = "d9b2f0a5c87f45e8a4b3c1e7d6a9f8b2c4e5a6d7b8c9f0d1e2a3b4c5d6e7f8a9"
JWT_ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# ---------------------------
# AUTH HELPERS
# ---------------------------
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed):
    return pwd_context.verify(plain_password, hashed)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def decode_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    data = await decode_token(token)
    user = await User.get(data.get("user_id"))
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or inactive")
    return user

def require_role(roles: List[RoleEnum]):
    async def _checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(403, "Forbidden")
        return current_user
    return _checker

# ---------------------------
# AUDIT + NOTIFICATIONS
# ---------------------------
async def audit(actor_id: Optional[str], action_type: str, resource_type=None, resource_id=None, payload=None):
    await AuditLog(
        actor_id=actor_id,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload
    ).insert()

async def notify(user_id: str, message: str, type_: str = "info"):
    await Notification(user_id=user_id, type=type_, message=message).insert()
