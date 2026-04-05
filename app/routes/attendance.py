"""
app/routes/attendance.py — Attendance listing with date range filter.
GET /api/attendance — auth, paginated, date range filter, JOIN query (no N+1)
"""
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import Attendance, Employee
from app.schemas import AttendanceResponse

router = APIRouter(prefix="/api/attendance", tags=["Attendance"])


@router.get("", response_model=list[AttendanceResponse])
async def list_attendance(
    request: Request,
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
    employee_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = request.state.org_id

    # Single JOIN query — no N+1
    query = (
        select(Attendance, Employee.name.label("employee_name"))
        .join(Employee, Attendance.employee_id == Employee.id)
        .where(Attendance.org_id == org_id)
    )

    if start_date:
        query = query.where(Attendance.date >= start_date)
    if end_date:
        query = query.where(Attendance.date <= end_date)
    if employee_id:
        query = query.where(Attendance.employee_id == employee_id)

    query = query.order_by(Attendance.date.desc(), Employee.name)
    query = query.offset((page - 1) * limit).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return [
        AttendanceResponse(
            id=att.id,
            org_id=att.org_id,
            employee_id=att.employee_id,
            employee_name=emp_name,
            date=att.date,
            status=att.status,
            check_in=att.check_in,
            check_out=att.check_out,
            created_at=att.created_at,
        )
        for att, emp_name in rows
    ]
