"""
create_db.py — Creates the hr_saas PostgreSQL database if it doesn't exist.
Reads connection details from .env file.
Run this once before starting the app: python create_db.py
"""
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# Import all models so their tables are registered with Base.metadata
from app.models import (  # noqa: F401
    Organization,
    Employee,
    Attendance,
    LeaveRequest,
    PasswordResetToken,
)

load_dotenv()

# Parse from DATABASE_URL: postgresql+asyncpg://user:pass@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "")
url = DATABASE_URL.replace("postgresql+asyncpg://", "").replace("postgresql://", "")
user_pass, host_db = url.split("@")
user, password = user_pass.split(":", 1)  # split on first : (handles passwords with colons)
host_port, db_name = host_db.split("/")
host, port = (host_port.split(":") + ["5432"])[:2]


def create_database():
    """Create the PostgreSQL database if it does not already exist."""
    conn = psycopg2.connect(
        host=host,
        port=int(port),
        user=user,
        password=password,
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()

    cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
    exists = cursor.fetchone()

    if not exists:
        cursor.execute(f'CREATE DATABASE "{db_name}"')
        print(f"✅ Database '{db_name}' created successfully.")
    else:
        print(f"✅ Database '{db_name}' already exists.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_database()
