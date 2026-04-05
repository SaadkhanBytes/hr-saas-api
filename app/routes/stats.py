"""
app/routes/stats.py — Dashboard metrics.
GET /api/stats — auth, returns KPIs for the current org
"""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models import (
    Attendance,
    AttendanceStatus,
    Employee,
    EmployeeStatus,
    LeaveRequest,
    LeaveStatus,
)

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("")
async def get_stats(
    request: Request,
    current_user: Employee = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    org_id = request.state.org_id
    today = date.today()

    # Total employees
    total_result = await db.execute(
        select(func.count(Employee.id)).where(Employee.org_id == org_id)
    )
    total_employees = total_result.scalar() or 0

    # Active employees
    active_result = await db.execute(
        select(func.count(Employee.id)).where(
            Employee.org_id == org_id, Employee.status == EmployeeStatus.active
        )
    )
    active_employees = active_result.scalar() or 0

    # Department breakdown
    dept_result = await db.execute(
        select(Employee.department, func.count(Employee.id))
        .where(Employee.org_id == org_id)
        .group_by(Employee.department)
    )
    departments = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in dept_result.all()}

    # Today's attendance
    att_result = await db.execute(
        select(Attendance.status, func.count(Attendance.id))
        .where(Attendance.org_id == org_id, Attendance.date == today)
        .group_by(Attendance.status)
    )
    today_attendance = {row[0].value if hasattr(row[0], 'value') else str(row[0]): row[1] for row in att_result.all()}

    # Today's attendance details (with employee names)
    att_detail_result = await db.execute(
        select(Attendance, Employee.name.label("employee_name"))
        .join(Employee, Attendance.employee_id == Employee.id)
        .where(Attendance.org_id == org_id, Attendance.date == today)
        .order_by(Employee.name)
    )
    today_attendance_list = [
        {
            "employee_id": att.employee_id,
            "employee_name": emp_name,
            "status": att.status.value,
            "check_in": att.check_in,
            "check_out": att.check_out,
        }
        for att, emp_name in att_detail_result.all()
    ]

    # Pending leaves
    pending_result = await db.execute(
        select(func.count(LeaveRequest.id)).where(
            LeaveRequest.org_id == org_id, LeaveRequest.status == LeaveStatus.pending
        )
    )
    pending_leaves = pending_result.scalar() or 0

    # Pending leave details
    pending_detail_result = await db.execute(
        select(LeaveRequest, Employee.name.label("employee_name"))
        .join(Employee, LeaveRequest.employee_id == Employee.id)
        .where(LeaveRequest.org_id == org_id, LeaveRequest.status == LeaveStatus.pending)
        .order_by(LeaveRequest.created_at.desc())
    )
    pending_leaves_list = [
        {
            "id": lr.id,
            "employee_id": lr.employee_id,
            "employee_name": emp_name,
            "leave_type": lr.leave_type.value,
            "start_date": lr.start_date.isoformat(),
            "end_date": lr.end_date.isoformat(),
            "reason": lr.reason,
        }
        for lr, emp_name in pending_detail_result.all()
    ]

    # Average salary
    salary_result = await db.execute(
        select(func.avg(Employee.salary)).where(
            Employee.org_id == org_id, Employee.salary.isnot(None)
        )
    )
    avg_salary = round(salary_result.scalar() or 0, 2)

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "pending_leaves": pending_leaves,
        "avg_salary": avg_salary,
        "departments": departments,
        "today_attendance": today_attendance,
        "today_attendance_list": today_attendance_list,
        "pending_leaves_list": pending_leaves_list,
    }
