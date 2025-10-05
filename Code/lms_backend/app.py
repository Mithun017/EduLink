from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from models.db_models import User, Department, Task, Assignment, AuditLog, Notification, RoleEnum
from routes.endpoints import router as api_router
from services.utils import get_password_hash

MONGO_URL = "mongodb://localhost:27017/lms_db"

app = FastAPI(title="LMS MongoDB Backend (MVC)")

@app.on_event("startup")
async def startup():
    client = AsyncIOMotorClient(MONGO_URL)
    await init_beanie(database=client.get_default_database(), document_models=[
        User, Department, Task, Assignment, AuditLog, Notification
    ])
    if not await User.find_one(User.role == RoleEnum.superadmin):
        sa = User(
            email="superadmin@example.com",
            full_name="Super Admin",
            password_hash=get_password_hash("superadmin123"),
            role=RoleEnum.superadmin
        )
        await sa.insert()
        print("Created default superadmin: superadmin@example.com / superadmin123")

# Register all API routes
app.include_router(api_router)
