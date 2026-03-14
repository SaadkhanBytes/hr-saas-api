"""
Stats route — HR dashboard metrics, fully tenant-scoped with error handling.
"""

from datetime import date
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Employee, Attendance, LeaveRequest, EmployeeStatus, LeaveStatus
from app.auth import get_current_user

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("")
async def get_stats(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _user: Employee = Depends(get_current_user),
):
    """Get HR dashboard stats — 3 GROUP BY queries."""
    org_id = request.state.org_id
    today = date.today()

    try:
        emp_result = await db.execute(
            select(
                func.count(Employee.id).label("total"),
                func.count(case((Employee.status == EmployeeStatus.ACTIVE, 1))).label("active"),
                func.count(case((Employee.status == EmployeeStatus.ON_LEAVE, 1))).label("on_leave"),
                func.avg(Employee.salary).label("avg_salary"),
            ).where(Employee.org_id == org_id)
        )
        emp_stats = emp_result.one()

        dept_result = await db.execute(
            select(Employee.department, func.count(Employee.id))
            .where(Employee.org_id == org_id)
            .group_by(Employee.department)
        )
        dept_counts = {dept.value: count for dept, count in dept_result.all()}

        att_result = await db.execute(
            select(Attendance.status, func.count(Attendance.id))
            .where(Attendance.org_id == org_id, Attendance.date == today)
            .group_by(Attendance.status)
        )
        today_att = {status.value: count for status, count in att_result.all()}

        leave_result = await db.execute(
            select(
                func.count(LeaveRequest.id).label("total"),
                func.count(case((LeaveRequest.status == LeaveStatus.PENDING, 1))).label("pending"),
            ).where(LeaveRequest.org_id == org_id)
        )
        leave_stats = leave_result.one()

        return {
            "total_employees": emp_stats.total,
            "active_employees": emp_stats.active,
            "on_leave": emp_stats.on_leave,
            "departments": dept_counts,
            "today_attendance": today_att,
            "pending_leaves": leave_stats.pending,
            "total_leaves": leave_stats.total,
            "avg_salary": round(emp_stats.avg_salary or 0, 0),
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to fetch stats") from exc
