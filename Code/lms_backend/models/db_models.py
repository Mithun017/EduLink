import enum
from datetime import datetime
from typing import Optional, List, Any
from beanie import Document
from pydantic import EmailStr, Field

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
