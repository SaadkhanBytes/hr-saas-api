"""
app/schemas.py — Pydantic schemas for request/response validation.
"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models import (
    AttendanceStatus,
    Department,
    EmployeeRole,
    EmployeeStatus,
    LeaveStatus,
    LeaveType,
    PlanType,
)


# ── Organization ───────────────────────────────────────────────────────────────

class OrgRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    plan: PlanType = PlanType.free
    industry: Optional[str] = None
    admin_name: str = Field(..., min_length=1, max_length=255)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6)


class OrgResponse(BaseModel):
    id: int
    name: str
    slug: str
    plan: PlanType
    industry: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Auth ───────────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee: dict


# ── Employee ───────────────────────────────────────────────────────────────────

class EmployeeCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone: Optional[str] = None
    department: Department
    role: EmployeeRole
    position: Optional[str] = None
    salary: Optional[float] = None
    status: EmployeeStatus = EmployeeStatus.active
    join_date: Optional[date] = None


class EmployeeUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[Department] = None
    role: Optional[EmployeeRole] = None
    position: Optional[str] = None
    salary: Optional[float] = None
    status: Optional[EmployeeStatus] = None
    join_date: Optional[date] = None
    password: Optional[str] = Field(None, min_length=8)


class EmployeeResponse(BaseModel):
    id: int
    org_id: int
    name: str
    email: str
    phone: Optional[str] = None
    department: Department
    role: EmployeeRole
    position: Optional[str] = None
    salary: Optional[float] = None
    status: EmployeeStatus
    join_date: Optional[date] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Attendance ─────────────────────────────────────────────────────────────────

class AttendanceResponse(BaseModel):
    id: int
    org_id: int
    employee_id: int
    employee_name: Optional[str] = None
    date: date
    status: AttendanceStatus
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Leave ──────────────────────────────────────────────────────────────────────

class LeaveCreateRequest(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None

    @model_validator(mode="after")
    def check_dates(self) -> "LeaveCreateRequest":
        """Validate that end_date is not before start_date."""
        if self.end_date < self.start_date:
            raise ValueError("end_date must not be before start_date")
        return self


class LeaveUpdateRequest(BaseModel):
    status: LeaveStatus


class LeaveResponse(BaseModel):
    id: int
    org_id: int
    employee_id: int
    employee_name: Optional[str] = None
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: Optional[str] = None
    status: LeaveStatus
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Password Reset ─────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    """Request body for the forgot-password endpoint."""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request body for the reset-password endpoint."""
    token: str
    new_password: str = Field(..., min_length=8)
