# HR SaaS API — Multi-Tenant HR Management System

A production-grade REST API for managing HR operations across multiple organizations, built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.

## 🏗️ Multi-Tenant Architecture

Every company that uses this system gets their own isolated data. All companies share the same database tables, but a tenant middleware layer ensures that every request is scoped to the authenticated organization — no company can ever see another's data.

```
Request → JWT Token → Extract org_id → Scope all DB queries to that org
```

## ✨ Features

- **JWT Authentication** — secure login with tokens that carry org and employee context
- **Role-Based Access Control** — intern / junior / mid / senior / lead / manager / director / VP / CXO
- **Employee Management** — full CRUD with pagination, filtering by department and status
- **Attendance Tracking** — daily check-in/check-out records per employee
- **Leave Management** — submit requests, approve/reject with manager role gate
- **HR Dashboard Stats** — headcount, department breakdown, attendance, payroll average
- **Pydantic Validation** — all inputs validated with detailed error messages
- **Tenant Middleware** — every API route automatically scoped to the correct organization

## 🛠️ Tech Stack

- **FastAPI** — async Python web framework
- **PostgreSQL** — relational database
- **SQLAlchemy 2.0** — async ORM
- **JWT (PyJWT)** — stateless authentication
- **Pydantic v2** — request/response validation
- **bcrypt** — password hashing

## 🚀 Quick Start

**1. Clone the repo**
```bash
git clone https://github.com/SaadkhanBytes/hr-saas-api.git
cd hr-saas-api
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Configure environment**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

**4. Create the database**
```bash
python create_db.py
```

**5. Run the API**
```bash
uvicorn app.main:app --reload
```

API is live at `http://localhost:8000`
Swagger docs at `http://localhost:8000/docs`

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/login` | Login, receive JWT | ❌ |
| GET | `/api/organizations` | List all organizations | ❌ |
| GET | `/api/employees` | List employees (paginated) | ✅ |
| POST | `/api/employees` | Add employee | ✅ Admin |
| PUT | `/api/employees/{id}` | Update employee | ✅ Admin |
| DELETE | `/api/employees/{id}` | Delete employee | ✅ Admin |
| GET | `/api/attendance` | List attendance records | ✅ |
| GET | `/api/leaves` | List leave requests | ✅ |
| POST | `/api/leaves` | Submit leave request | ✅ |
| PUT | `/api/leaves/{id}` | Approve / reject leave | ✅ Admin |
| GET | `/api/stats` | Dashboard statistics | ✅ |

## 🔐 How Authentication Works

Login returns a JWT token that contains the employee's `org_id`. Every protected route reads this token and scopes the database query to that organization automatically.

```bash
# 1. Login
POST /api/auth/login
{ "email": "admin@acme.com", "password": "secret" }

# 2. Use the token on every request
GET /api/employees
Authorization: Bearer <your_token>
```

## 📁 Project Structure

```
├── app/
│   ├── main.py          # App entry point, middleware, routes
│   ├── auth.py          # JWT creation, verification, dependency
│   ├── models.py        # SQLAlchemy models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── database.py      # Async DB session
│   ├── middleware.py    # Tenant isolation middleware
│   ├── seed.py          # Sample data for testing
│   └── routes/
│       ├── auth.py
│       ├── employees.py
│       ├── attendance.py
│       ├── leaves.py
│       ├── orgs.py
│       └── stats.py
├── static/              # Frontend dashboard
├── create_db.py
└── requirements.txt
```
