from fastapi import APIRouter, Depends, HTTPException
from models.db_models import User, Department, Task, Assignment, RoleEnum
from services.utils import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, require_role, audit
)
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

# ---------------------------
# AUTH
# ---------------------------
@router.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await User.find_one(User.email == form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    token = create_access_token({"user_id": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/auth/me")
async def me(current: User = Depends(get_current_user)):
    return current

@router.post("/auth/register")
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
@router.post("/departments")
async def create_department(payload: dict, current: User = Depends(require_role([RoleEnum.admin, RoleEnum.superadmin]))):
    d = Department(**payload)
    await d.insert()
    await audit(str(current.id), "CREATE_DEPT", "department", str(d.id), {"name": d.name})
    return d

@router.get("/departments")
async def list_departments():
    return await Department.find_all().to_list()

# ---------------------------
# TASKS
# ---------------------------
@router.post("/tasks")
async def create_task(payload: dict, current: User = Depends(require_role([RoleEnum.professor, RoleEnum.admin, RoleEnum.superadmin]))):
    task = Task(**payload, created_by=str(current.id))
    await task.insert()
    await audit(str(current.id), "CREATE_TASK", "task", str(task.id), {"title": task.title})
    return task

@router.get("/tasks")
async def list_tasks(current: User = Depends(get_current_user)):
    if current.role == RoleEnum.professor:
        return await Task.find(Task.created_by == str(current.id)).to_list()
    if current.role == RoleEnum.student:
        assigns = await Assignment.find(Assignment.student_id == str(current.id)).to_list()
        ids = [a.task_id for a in assigns]
        return await Task.find(Task.id.in_(ids)).to_list()
    return await Task.find_all().to_list()
