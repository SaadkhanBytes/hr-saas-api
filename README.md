# HR SaaS API

A multi-tenant HR management REST API built with **FastAPI**, **PostgreSQL**, and **Row Level Security (RLS)**. Supports multiple organizations on a single instance, each fully isolated by tenant.

---

## Features

 **Multi-tenancy** — organizations are fully isolated via tenant middleware
 **JWT Authentication** — secure login with access tokens
 **Employee Management** — full CRUD with role-based access control
 **Attendance Tracking** — log and query employee attendance
 **Leave Management** — submit, approve, and reject leave requests
 **Stats & Reporting** — org-level HR statistics
 **Rate Limiting** — via SlowAPI (10/min on login, 5/hr on password reset)
 **Static Frontend** — served directly from `/static`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| Database | PostgreSQL (async via asyncpg) |
| ORM | SQLAlchemy 2.0 (async) |
| Auth | JWT (PyJWT) + bcrypt (passlib) |
| Rate Limiting | SlowAPI |
| Server | Uvicorn |

---

## Project Structure
hr-saas-api/
├── app/
│   ├── main.py          # App entry point, middleware, routers
│   ├── auth.py          # JWT creation & verification, password hashing
│   ├── database.py      # Async SQLAlchemy engine & session
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── middleware.py    # Tenant resolution middleware
│   ├── limiter.py       # SlowAPI rate limiter instance
│   ├── seed.py          # Database seed data
│   └── routes/
│       ├── auth.py          # Login, forgot/reset password
│       ├── orgs.py          # Organization registration & listing
│       ├── employees.py     # Employee CRUD
│       ├── attendance.py    # Attendance tracking
│       ├── leaves.py        # Leave requests
│       └── stats.py         # HR statistics
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── create_db.py         # Database creation script
├── requirements.txt
├── .env.example
└── .gitignore


---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL running locally

### 1. Clone the repository
```bash
git clone https://github.com/SaadkhanBytes/hr-saas-api.git
cd hr-saas-api
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set up environment variables
```bash
cp .env.example .env
```

Edit `.env` with your own values:
```env
DATABASE_URL=postgresql+asyncpg://postgres:yourpassword@localhost:5432/hr_saas
DATABASE_URL_SYNC=postgresql://postgres:yourpassword@localhost:5432/hr_saas
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
ENV=development
ALLOWED_ORIGINS=http://localhost:3000
```

> ⚠️ Never commit your `.env` file. It is already listed in `.gitignore`.

Generate a secure secret key with:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 5. Create the database
```bash
python create_db.py
```

### 6. Run the server
```bash
uvicorn app.main:app --reload
```

API live at: `http://localhost:8000`  
Interactive docs at: `http://localhost:8000/docs`

---

## API Endpoints

### Auth
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/auth/login` | Public | Login, returns JWT |
| POST | `/api/auth/forgot-password` | Public | Initiate password reset |
| POST | `/api/auth/reset-password` | Public | Complete password reset |

### Organizations
| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/organizations/register` | Public | Register new org + admin user |
| GET | `/api/organizations` | Auth | List all organizations |

### Employees
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/employees` | Auth | List employees (filterable) |
| POST | `/api/employees` | Admin | Create employee |
| PUT | `/api/employees/{id}` | Admin | Update employee |
| DELETE | `/api/employees/{id}` | Admin | Delete employee |

### Attendance
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/attendance` | Auth | List attendance records |
| POST | `/api/attendance` | Auth | Log attendance |

### Leaves
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/leaves` | Auth | List leave requests |
| POST | `/api/leaves` | Auth | Submit leave request |
| PUT | `/api/leaves/{id}` | Admin | Approve / Reject leave |

### Stats
| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/stats` | Auth | Org-level HR statistics |

---

## Environment Variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | Async PostgreSQL connection string |
| `DATABASE_URL_SYNC` | Sync PostgreSQL connection string |
| `SECRET_KEY` | JWT signing secret |
| `ALGORITHM` | JWT algorithm (default: HS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry duration |
| `ENV` | Environment (`development` / `production`) |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |

---



