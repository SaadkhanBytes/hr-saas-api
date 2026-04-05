"""
app/models.py — SQLAlchemy ORM models for the multi-tenant HR SaaS.
All tenant-scoped tables have an org_id FK with CASCADE DELETE.
"""
import enum
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database import Base


# ── Enums ──────────────────────────────────────────────────────────────────────

class PlanType(str, enum.Enum):
    free = "free"
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class Department(str, enum.Enum):
    engineering = "engineering"
    design = "design"
    marketing = "marketing"
    sales = "sales"
    hr = "hr"
    finance = "finance"
    operations = "operations"
    support = "support"


class EmployeeRole(str, enum.Enum):
    intern = "intern"
    junior = "junior"
    mid = "mid"
    senior = "senior"
    lead = "lead"
    manager = "manager"
    director = "director"
    vp = "vp"
    cxo = "cxo"


class EmployeeStatus(str, enum.Enum):
    active = "active"
    on_leave = "on_leave"
    terminated = "terminated"
    probation = "probation"


class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    half_day = "half_day"
    work_from_home = "work_from_home"
    late = "late"


class LeaveType(str, enum.Enum):
    sick = "sick"
    casual = "casual"
    annual = "annual"
    maternity = "maternity"
    paternity = "paternity"
    unpaid = "unpaid"


class LeaveStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


ADMIN_ROLES = {EmployeeRole.manager, EmployeeRole.director, EmployeeRole.vp, EmployeeRole.cxo}


# ── Models ─────────────────────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(Enum(PlanType), nullable=False, default=PlanType.free)
    industry = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    employees = relationship("Employee", back_populates="organization", cascade="all, delete-orphan")


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("org_id", "email", name="uq_org_email"),
        Index("ix_employees_org_id", "org_id"),
        Index("ix_employees_email", "email"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    department = Column(Enum(Department), nullable=False)
    role = Column(Enum(EmployeeRole), nullable=False)
    position = Column(String(255), nullable=True)
    salary = Column(Float, nullable=True)
    status = Column(Enum(EmployeeStatus), nullable=False, default=EmployeeStatus.active)
    join_date = Column(Date, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    organization = relationship("Organization", back_populates="employees")
    attendance_records = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (
        Index("ix_attendance_org_id", "org_id"),
        Index("ix_attendance_employee_id", "employee_id"),
        Index("ix_attendance_date", "date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(Enum(AttendanceStatus), nullable=False)
    check_in = Column(String(10), nullable=True)
    check_out = Column(String(10), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    employee = relationship("Employee", back_populates="attendance_records")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"
    __table_args__ = (
        Index("ix_leave_requests_org_id", "org_id"),
        Index("ix_leave_requests_employee_id", "employee_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(Enum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(String(500), nullable=True)
    status = Column(Enum(LeaveStatus), nullable=False, default=LeaveStatus.pending)
    created_at = Column(DateTime, server_default=func.now())

    employee = relationship("Employee", back_populates="leave_requests")


class PasswordResetToken(Base):
    """Stores hashed password-reset tokens with expiry and usage tracking."""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now())
