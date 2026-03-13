"""
Employees route — fully tenant-scoped.
Every query is filtered by org_id from the tenant middleware.
"""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Employee

router = APIRouter(prefix="/api/employees", tags=["employees"])


@router.get("")
async def list_employees(request: Request, db: AsyncSession = Depends(get_db)):
    """List all employees for the current organization."""
    org_id = request.state.org_id
    result = await db.execute(
        select(Employee).where(Employee.org_id == org_id).order_by(Employee.name)
    )
    employees = result.scalars().all()
    return [
        {
            "id": e.id,
            "org_id": e.org_id,
            "name": e.name,
            "email": e.email,
            "phone": e.phone,
            "department": e.department.value,
            "role": e.role.value,
            "position": e.position,
            "salary": e.salary,
            "status": e.status.value,
            "join_date": e.join_date.isoformat(),
            "created_at": e.created_at.isoformat(),
        }
        for e in employees
    ]


@router.post("")
async def create_employee(request: Request, db: AsyncSession = Depends(get_db)):
    """Create a new employee in the current organization."""
    org_id = request.state.org_id
    body = await request.json()
    emp = Employee(
        org_id=org_id,
        name=body["name"],
        email=body["email"],
        phone=body.get("phone", ""),
        department=body["department"],
        role=body.get("role", "mid"),
        position=body.get("position", ""),
        salary=body.get("salary", 0),
    )
    db.add(emp)
    await db.flush()
    return {"id": emp.id, "name": emp.name, "org_id": emp.org_id}


@router.delete("/{emp_id}")
async def delete_employee(emp_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Delete an employee (scoped to current org)."""
    org_id = request.state.org_id
    result = await db.execute(
        select(Employee).where(Employee.id == emp_id, Employee.org_id == org_id)
    )
    emp = result.scalar()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found in this organization")
    await db.delete(emp)
    return {"message": "Employee deleted", "id": emp_id}
