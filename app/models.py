"""
SQLAlchemy models for Multi-Tenant HR SaaS.
Every table (except organizations) has an org_id FK — the tenant isolation key.
Each organization = one company with its own employees, departments, attendance, leave.
"""

from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Date, Float,
    ForeignKey, Enum as SAEnum, Boolean
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ──────────────────────────────────────────────

class PlanType(str, enum.Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Department(str, enum.Enum):
    ENGINEERING = "engineering"
    DESIGN = "design"
    MARKETING = "marketing"
    SALES = "sales"
    HR = "hr"
    FINANCE = "finance"
    OPERATIONS = "operations"
    SUPPORT = "support"


class EmployeeStatus(str, enum.Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"
    PROBATION = "probation"


class EmployeeRole(str, enum.Enum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    VP = "vp"
    CXO = "cxo"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    HALF_DAY = "half_day"
    WORK_FROM_HOME = "work_from_home"
    LATE = "late"


class LeaveType(str, enum.Enum):
    SICK = "sick"
    CASUAL = "casual"
    ANNUAL = "annual"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    UNPAID = "unpaid"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


# ── Models ─────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    plan = Column(SAEnum(PlanType), default=PlanType.FREE, nullable=False)
    industry = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    employees = relationship("Employee", back_populates="organization", cascade="all, delete-orphan")
    attendance_records = relationship("Attendance", back_populates="organization", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="organization", cascade="all, delete-orphan")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), default="")
    department = Column(SAEnum(Department), nullable=False)
    role = Column(SAEnum(EmployeeRole), default=EmployeeRole.MID, nullable=False)
    position = Column(String(255), default="")
    salary = Column(Float, default=0.0)
    status = Column(SAEnum(EmployeeStatus), default=EmployeeStatus.ACTIVE, nullable=False)
    join_date = Column(Date, default=date.today, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="employees")
    attendance_records = relationship("Attendance", back_populates="employee", cascade="all, delete-orphan")
    leave_requests = relationship("LeaveRequest", back_populates="employee", cascade="all, delete-orphan")


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    status = Column(SAEnum(AttendanceStatus), default=AttendanceStatus.PRESENT, nullable=False)
    check_in = Column(String(10), default="")
    check_out = Column(String(10), default="")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="attendance_records")
    employee = relationship("Employee", back_populates="attendance_records")


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    org_id = Column(Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_type = Column(SAEnum(LeaveType), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text, default="")
    status = Column(SAEnum(LeaveStatus), default=LeaveStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    organization = relationship("Organization", back_populates="leave_requests")
    employee = relationship("Employee", back_populates="leave_requests")
