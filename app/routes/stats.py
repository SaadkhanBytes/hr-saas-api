"""
Stats route — HR dashboard metrics, fully tenant-scoped.
"""

from datetime import date
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import (
    Employee, Attendance, LeaveRequest,
    EmployeeStatus, Department, AttendanceStatus, LeaveStatus
)

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(request: Request, db: AsyncSession = Depends(get_db)):
    """Get HR dashboard statistics for the current organization."""
    org_id = request.state.org_id
    today = date.today()

    # Employee count
    total_emps = (await db.execute(
        select(func.count(Employee.id)).where(Employee.org_id == org_id)
    )).scalar() or 0

    active_emps = (await db.execute(
        select(func.count(Employee.id)).where(
            Employee.org_id == org_id, Employee.status == EmployeeStatus.ACTIVE
        )
    )).scalar() or 0

    on_leave_emps = (await db.execute(
        select(func.count(Employee.id)).where(
            Employee.org_id == org_id, Employee.status == EmployeeStatus.ON_LEAVE
        )
    )).scalar() or 0

    # Department breakdown
    dept_counts = {}
    for dept in Department:
        count = (await db.execute(
            select(func.count(Employee.id)).where(
                Employee.org_id == org_id, Employee.department == dept
            )
        )).scalar() or 0
        if count > 0:
            dept_counts[dept.value] = count

    # Today's attendance
    today_att = {}
    for status in AttendanceStatus:
        count = (await db.execute(
            select(func.count(Attendance.id)).where(
                Attendance.org_id == org_id,
                Attendance.date == today,
                Attendance.status == status
            )
        )).scalar() or 0
        today_att[status.value] = count

    # Pending leave requests
    pending_leaves = (await db.execute(
        select(func.count(LeaveRequest.id)).where(
            LeaveRequest.org_id == org_id,
            LeaveRequest.status == LeaveStatus.PENDING
        )
    )).scalar() or 0

    total_leaves = (await db.execute(
        select(func.count(LeaveRequest.id)).where(LeaveRequest.org_id == org_id)
    )).scalar() or 0

    # Average salary
    avg_salary = (await db.execute(
        select(func.avg(Employee.salary)).where(Employee.org_id == org_id)
    )).scalar() or 0

    return {
        "total_employees": total_emps,
        "active_employees": active_emps,
        "on_leave": on_leave_emps,
        "departments": dept_counts,
        "today_attendance": today_att,
        "pending_leaves": pending_leaves,
        "total_leaves": total_leaves,
        "avg_salary": round(avg_salary, 0),
    }
