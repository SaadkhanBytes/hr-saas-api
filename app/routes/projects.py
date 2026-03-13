"""
Attendance route — fully tenant-scoped.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Attendance, Employee

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


@router.get("")
async def list_attendance(request: Request, db: AsyncSession = Depends(get_db)):
    """List attendance records for the current organization."""
    org_id = request.state.org_id
    result = await db.execute(
        select(Attendance).where(Attendance.org_id == org_id).order_by(Attendance.date.desc(), Attendance.employee_id)
    )
    records = result.scalars().all()

    att_list = []
    for a in records:
        emp_result = await db.execute(select(Employee.name).where(Employee.id == a.employee_id))
        emp_name = emp_result.scalar()
        att_list.append({
            "id": a.id,
            "org_id": a.org_id,
            "employee_id": a.employee_id,
            "employee_name": emp_name,
            "date": a.date.isoformat(),
            "status": a.status.value,
            "check_in": a.check_in,
            "check_out": a.check_out,
        })
    return att_list
