"""
Pydantic schemas for request/response validation.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date


# ── Auth ───────────────────────────────────────────────

class RegisterRequest(BaseModel):
    org_name: str = Field(..., min_length=2, max_length=255)
    org_slug: str = Field(..., min_length=2, max_length=100, pattern=r"^[a-z0-9\-]+$")
    admin_name: str = Field(..., min_length=2, max_length=255)
    email: str
    password: str = Field(..., min_length=6)
    industry: str = ""

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v

    @field_validator("org_slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        return v.strip().lower()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    org_id: int
    org_name: str
    employee_name: str
    employee_role: str


# ── Employee ───────────────────────────────────────────

class EmployeeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=3, max_length=255)
    phone: str = Field(default="", max_length=20)
    department: str
    role: str = "mid"
    position: str = ""
    salary: float = Field(default=0, ge=0)
    password: Optional[str] = Field(default=None, min_length=6)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        v = v.strip().lower()
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email address")
        return v

    @field_validator("department")
    @classmethod
    def validate_department(cls, v: str) -> str:
        valid = {"engineering","design","marketing","sales","hr","finance","operations","support"}
        if v.lower() not in valid:
            raise ValueError(f"department must be one of: {', '.join(sorted(valid))}")
        return v.lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid = {"intern","junior","mid","senior","lead","manager","director","vp","cxo"}
        if v.lower() not in valid:
            raise ValueError(f"role must be one of: {', '.join(sorted(valid))}")
        return v.lower()


class EmployeeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=20)
    department: Optional[str] = None
    role: Optional[str] = None
    position: Optional[str] = None
    salary: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = None

    @field_validator("department")
    @classmethod
    def validate_department(cls, v):
        if v is None:
            return v
        valid = {"engineering","design","marketing","sales","hr","finance","operations","support"}
        if v.lower() not in valid:
            raise ValueError(f"department must be one of: {', '.join(sorted(valid))}")
        return v.lower()

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is None:
            return v
        valid = {"intern","junior","mid","senior","lead","manager","director","vp","cxo"}
        if v.lower() not in valid:
            raise ValueError(f"role must be one of: {', '.join(sorted(valid))}")
        return v.lower()

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is None:
            return v
        valid = {"active","on_leave","terminated","probation"}
        if v.lower() not in valid:
            raise ValueError(f"status must be one of: {', '.join(sorted(valid))}")
        return v.lower()


# ── Leave ──────────────────────────────────────────────

class LeaveCreate(BaseModel):
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    reason: str = ""

    @field_validator("leave_type")
    @classmethod
    def validate_leave_type(cls, v: str) -> str:
        valid = {"sick","casual","annual","maternity","paternity","unpaid"}
        if v.lower() not in valid:
            raise ValueError(f"leave_type must be one of: {', '.join(sorted(valid))}")
        return v.lower()

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, v, info):
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be on or after start_date")
        return v


class LeaveUpdateStatus(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected|cancelled)$")
