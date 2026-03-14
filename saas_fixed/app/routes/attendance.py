"""
Attendance route — tenant-scoped, date-filtered, paginated.
"""

from datetime import date
from fastapi import APIRouter, Depends, Request, Query
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Attendance, Employee
from app.auth import get_current_user

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.get("")
async def list_attendance(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _user: Employee = Depends(get_current_user),
    date_from: date = Query(default=None, description="Filter from date (YYYY-MM-DD)"),
    date_to: date = Query(default=None, description="Filter to date (YYYY-MM-DD)"),
    employee_id: int = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    """List attendance records — date-filtered, paginated, no N+1."""
    org_id = request.state.org_id
    try:
        q = (
            select(Attendance, Employee.name)
            .join(Employee, Attendance.employee_id == Employee.id)
            .where(Attendance.org_id == org_id)
        )
        if date_from:
            q = q.where(Attendance.date >= date_from)
        if date_to:
            q = q.where(Attendance.date <= date_to)
        if employee_id:
            q = q.where(Attendance.employee_id == employee_id)

        q = q.order_by(Attendance.date.desc(), Attendance.employee_id)
        q = q.offset((page - 1) * page_size).limit(page_size)

        result = await db.execute(q)
        rows = result.all()

        return [
            {
                "id": att.id,
                "org_id": att.org_id,
                "employee_id": att.employee_id,
                "employee_name": emp_name,
                "date": att.date.isoformat(),
                "status": att.status.value,
                "check_in": att.check_in,
                "check_out": att.check_out,
            }
            for att, emp_name in rows
        ]
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch attendance records") from exc
