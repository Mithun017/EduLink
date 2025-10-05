# 📘 EduLink

This is the backend service for the **LMS Multi-Agent Dashboard** inspired by GitHub Actions-like workflows. Built with **FastAPI**, it supports CRUD operations for Admin, Professor, and Student roles.

---

## 🚀 How to Run

```bash
uvicorn app:app --reload
```

Visit: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for interactive API documentation.

---

## 🔑 Authentication APIs

### **Register User** (Admin/Superadmin only)

```http
POST /auth/register
Authorization: Bearer <token>
```

Body:

```json
{
  "email": "prof1@example.com",
  "password": "password123",
  "full_name": "Prof One",
  "role": "professor",
  "department_id": 1
}
```

### **Login (Get Token)**

```http
POST /auth/token
```

Form Data:

```
username=superadmin@example.com
password=superadmin123
```

### **Get Current User**

```http
GET /auth/me
Authorization: Bearer <token>
```

---

## 🏢 Department APIs

### **Create Department**

```http
POST /departments
Authorization: Bearer <token>
```

```json
{
  "name": "Computer Science",
  "code": "CSE"
}
```

### **List Departments**

```http
GET /departments
```

### **Update Department**

```http
PUT /departments/{dept_id}
```

### **Delete Department**

```http
DELETE /departments/{dept_id}
```

---

## 👤 User APIs (Admin/Superadmin)

* `GET /users` → List all users (filters: `?role=professor`, `?dept=1`).
* `GET /users/{id}` → Get single user.
* `PUT /users/{id}` → Update user.
* `DELETE /users/{id}` → Deactivate user.

---

## 📚 Task APIs

### **Create Task** (Professor/Admin/Superadmin)

```http
POST /tasks
Authorization: Bearer <token>
```

```json
{
  "title": "ML Assignment 1",
  "description": "Train a model",
  "visibility": "department",
  "target_departments": [1],
  "due_date": "2025-10-15T23:59:59"
}
```

### **List Tasks**

```http
GET /tasks
```

(Students → own tasks, Professors → their created tasks, Admin → all)

### **Get Task**

```http
GET /tasks/{task_id}
```

### **Update Task**

```http
PUT /tasks/{task_id}
```

### **Delete Task**

```http
DELETE /tasks/{task_id}
```

---

## 📝 Assignment APIs

### **List Assignments**

```http
GET /assignments
```

### **Start Assignment**

```http
POST /assignments/{id}/start
```

### **Submit Assignment** (Student)

```http
POST /assignments/{id}/submit
```

```json
{
  "submission_url": "https://github.com/student1/solution",
  "notes": "Completed",
  "attachments": []
}
```

### **Grade Assignment** (Professor/Admin)

```http
POST /assignments/{id}/grade
```

```json
{
  "grade": 90,
  "feedback": "Good work",
  "set_state": "reviewed"
}
```

### **Reopen Assignment**

```http
POST /assignments/{id}/reopen
```

---

## 🔔 Notification APIs

* `GET /notifications` → Get user’s notifications.
* `POST /notifications/{nid}/mark_read` → Mark notification as read.

---

## 📜 Audit Log APIs

* `GET /audit_logs` → View all logs (Admin/Superadmin).

---

## 📊 Analytics APIs

* `GET /analytics/overview`

```json
{
  "total_users": 10,
  "total_students": 6,
  "total_professors": 3,
  "total_tasks": 5,
  "pending_submissions": 2,
  "completed_assignments": 3
}
```

---

## 🧪 Testing Flow Example

1. **Login as Superadmin** → get token.
2. **Create Department** → `POST /departments`.
3. **Register Professor/Students** → `POST /auth/register`.
4. **Login as Professor** → create tasks via `POST /tasks`.
5. **Students Login** → view tasks via `GET /tasks`.
6. **Student Starts + Submits Assignment** → `POST /assignments/{id}/submit`.
7. **Professor Grades** → `POST /assignments/{id}/grade`.
8. **Admin Checks Dashboard** → `GET /analytics/overview` + `GET /audit_logs`.

---

## 📦 Requirements

```
fastapi
uvicorn
beanie
motor
passlib[bcrypt]
python-jose
pydantic[email]
```
