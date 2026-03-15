# HR SaaS API — Multi-Tenant HR Management System

> 🌐 **Live Demo:** https://hr-saas-api.onrender.com  
> 📖 **API Docs:** https://hr-saas-api.onrender.com/docs

A production-grade REST API for managing HR operations across multiple organizations, built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy**.

---

## 🏗️ Multi-Tenant Architecture

Every company that signs up gets their own completely isolated workspace. All organizations share the same database tables, but a tenant middleware layer ensures every request is scoped to the authenticated organization — no company can ever see another's data.

```
Request → JWT Token → Extract org_id → Scope all DB queries to that org
```

This is the same pattern used by **Slack, Notion, and Linear**.

---

## ✨ Features

- **Dynamic Org Registration** — any company can sign up and get their own isolated workspace instantly
- **JWT Authentication** — secure login with tokens that carry org and employee context
- **Role-Based Access Control** — intern / junior / mid / senior / lead / manager / director / VP / CXO
- **Employee Management** — full CRUD with pagination, filtering by department and status
- **Attendance Tracking** — daily check-in/check-out records per employee
- **Leave Management** — submit requests, approve/reject with manager role gate
- **HR Dashboard Stats** — headcount, department breakdown, attendance, payroll average
- **Pydantic Validation** — all inputs validated with detailed error messages
- **Tenant Middleware** — every API route automatically scoped to the correct organization

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| **FastAPI** | Async Python web framework |
| **PostgreSQL** | Relational database |
| **SQLAlchemy 2.0** | Async ORM |
| **PyJWT** | Stateless authentication |
| **Pydantic v2** | Request/response validation |
| **bcrypt** | Password hashing |
| **asyncpg** | High-performance async PostgreSQL driver |

---

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

- API live at `http://localhost:8000`
- Swagger docs at `http://localhost:8000/docs`
- Frontend dashboard at `http://localhost:8000`

---

## 📡 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/organizations/register` | Register a new company | ❌ |
| GET | `/api/organizations` | List all organizations | ❌ |
| POST | `/api/auth/login` | Login, receive JWT | ❌ |
| GET | `/api/employees` | List employees (paginated) | ✅ |
| POST | `/api/employees` | Add employee | ✅ Admin |
| PUT | `/api/employees/{id}` | Update employee | ✅ Admin |
| DELETE | `/api/employees/{id}` | Delete employee | ✅ Admin |
| GET | `/api/attendance` | List attendance records | ✅ |
| GET | `/api/leaves` | List leave requests | ✅ |
| POST | `/api/leaves` | Submit leave request | ✅ |
| PUT | `/api/leaves/{id}` | Approve / reject leave | ✅ Admin |
| GET | `/api/stats` | Dashboard statistics | ✅ |

---

## 🔐 How Authentication Works

**Step 1 — Register your company**
```bash
POST /api/organizations/register
{
  "org_name": "Acme Corp",
  "org_slug": "acme-corp",
  "admin_name": "Jane Smith",
  "email": "jane@acme.com",
  "password": "secret123"
}
```

**Step 2 — Login to get a JWT**
```bash
POST /api/auth/login
{
  "email": "jane@acme.com",
  "password": "secret123"
}
```

**Step 3 — Use the token on every request**
```bash
GET /api/employees
Authorization: Bearer <your_token>
```

The JWT contains the `org_id` — every protected route reads this and scopes the database query to that organization automatically.

---

## 🧪 Demo Accounts

| Name | Company | Email | Password |
|------|---------|-------|----------|
| Sarah Chen | TechVista Solutions | sarah@techvista.io | password123 |
| Dr. Luna Wright | Bloom Health | luna@bloomhealth.com | password123 |
| Dr. Alex Morgan | NovaTech Manufacturing | alex@novatech.com | password123 |

---

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
│       ├── auth.py      # Login endpoint
│       ├── orgs.py      # Org registration + listing
│       ├── employees.py # Employee CRUD
│       ├── attendance.py# Attendance records
│       ├── leaves.py    # Leave requests + approvals
│       └── stats.py     # Dashboard statistics
├── static/              # Frontend dashboard (HTML/CSS/JS)
├── create_db.py         # Database setup script
└── requirements.txt
```

---

## 💡 Key Concepts Demonstrated

- ✅ Multi-tenant architecture (shared tables + middleware isolation)
- ✅ JWT authentication with org_id embedding
- ✅ Role-based access control (9 roles)
- ✅ Async FastAPI with SQLAlchemy 2.0
- ✅ Pydantic v2 validation with custom validators
- ✅ Pagination and filtering on list endpoints
- ✅ N+1 query prevention with JOINs
- ✅ Dynamic org registration flow
- ✅ Frontend SPA served from FastAPI
