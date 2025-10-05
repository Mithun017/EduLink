# app.py
import enum
from datetime import datetime, timedelta
from typing import List, Optional, Any

from fastapi import FastAPI, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from passlib.context import CryptContext
from jose import jwt, JWTError

from beanie import Document, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

# ---------------------------
# Config
# ---------------------------
MONGO_URL = "mongodb://localhost:27017/lms_db"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
JWT_SECRET = "d9b2f0a5c87f45e8a4b3c1e7d6a9f8b2c4e5a6d7b8c9f0d1e2a3b4c5d6e7f8a9"

JWT_ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# ---------------------------
# ENUMS
# ---------------------------
class RoleEnum(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    professor = "professor"
    student = "student"

class VisibilityEnum(str, enum.Enum):
    all = "all"
    department = "department"
    individual = "individual"

class AssignmentState(str, enum.Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    submitted = "submitted"
    reviewed = "reviewed"
    completed = "completed"
    reopened = "reopened"

# ---------------------------
# MODELS (Beanie Documents)
# ---------------------------
class Department(Document):
    name: str
    code: Optional[str] = None

class User(Document):
    email: EmailStr
    full_name: Optional[str] = None
    password_hash: str
    role: RoleEnum = RoleEnum.student
    department_id: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Task(Document):
    title: str
    description: Optional[str] = None
    created_by: str
    visibility: VisibilityEnum = VisibilityEnum.all
    target_departments: List[str] = []
    target_students: List[str] = []
    due_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Assignment(Document):
    task_id: str
    student_id: str
    assigned_by: str
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    state: AssignmentState = AssignmentState.assigned
    submission: Optional[dict] = None
    grade: Optional[int] = None
    feedback: Optional[str] = None
    last_update: datetime = Field(default_factory=datetime.utcnow)

class AuditLog(Document):
    actor_id: Optional[str] = None
    action_type: str
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    payload: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Notification(Document):
    user_id: str
    type: str = "info"
    message: str
    read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

# ---------------------------
# Utility functions
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

async def audit(actor_id: Optional[str], action_type: str, resource_type=None, resource_id=None, payload=None):
    await AuditLog(actor_id=actor_id, action_type=action_type, resource_type=resource_type, resource_id=resource_id, payload=payload).insert()

async def notify(user_id: str, message: str, type_: str = "info"):
    await Notification(user_id=user_id, type=type_, message=message).insert()

# ---------------------------
# App
# ---------------------------
app = FastAPI(title="LMS MongoDB Backend")

# ---------------------------
# AUTH
# ---------------------------
@app.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"user_id": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me")
async def me(current: User = Depends(get_current_user)):
    return current

# ---------------------------
# USER MANAGEMENT
# ---------------------------
@app.post("/auth/register")
async def register(user_in: dict, current: User = Depends(require_role([RoleEnum.superadmin, RoleEnum.admin]))):
    existing = await User.find_one(User.email == user_in["email"])
    if existing:
        raise HTTPException(400, "User exists")
    user = User(
        email=user_in["email"],
        full_name=user_in.get("full_name"),
        password_hash=get_password_hash(user_in["password"]),
        role=user_in.get("role", RoleEnum.student),
        department_id=user_in.get("department_id")
    )
    await user.insert()
    await audit(str(current.id), "CREATE_USER", "user", str(user.id), {"email": user.email})
    return user

# ---------------------------
# DEPARTMENT
# ---------------------------
@app.post("/departments")
async def create_department(payload: dict, current: User = Depends(require_role([RoleEnum.admin, RoleEnum.superadmin]))):
    d = Department(**payload)
    await d.insert()
    await audit(str(current.id), "CREATE_DEPT", "department", str(d.id), {"name": d.name})
    return d

@app.get("/departments")
async def list_departments():
    return await Department.find_all().to_list()

# ---------------------------
# TASKS
# ---------------------------
@app.post("/tasks")
async def create_task(payload: dict, current: User = Depends(require_role([RoleEnum.professor, RoleEnum.admin, RoleEnum.superadmin]))):
    task = Task(**payload, created_by=str(current.id))
    await task.insert()
    await audit(str(current.id), "CREATE_TASK", "task", str(task.id), {"title": task.title})
    return task

@app.get("/tasks")
async def list_tasks(current: User = Depends(get_current_user)):
    if current.role == RoleEnum.professor:
        return await Task.find(Task.created_by == str(current.id)).to_list()
    if current.role == RoleEnum.student:
        assigns = await Assignment.find(Assignment.student_id == str(current.id)).to_list()
        ids = [a.task_id for a in assigns]
        return await Task.find(Task.id.in_(ids)).to_list()
    return await Task.find_all().to_list()

# ---------------------------
# STARTUP
# ---------------------------
@app.on_event("startup")
async def startup():
    client = AsyncIOMotorClient(MONGO_URL)
    await init_beanie(database=client.get_default_database(), document_models=[
        User, Department, Task, Assignment, AuditLog, Notification
    ])
    if not await User.find_one(User.role == RoleEnum.superadmin):
        sa = User(email="superadmin@example.com", full_name="Super Admin", password_hash=get_password_hash("superadmin123"), role=RoleEnum.superadmin)
        await sa.insert()
        print("Created default superadmin: superadmin@example.com / superadmin123")
