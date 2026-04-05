"""
app/seed.py — Seed data for development environment.
Only runs when ENV=development. Drops and recreates public schema for a clean slate.
3 organizations with employees, attendance (last 7 weekdays), and leave requests.
"""
import os
from datetime import date, timedelta, datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import hash_password
from app.database import async_session, engine
from app.models import (
    Attendance,
    AttendanceStatus,
    Base,
    Department,
    Employee,
    EmployeeRole,
    EmployeeStatus,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    Organization,
    PlanType,
)


ATTENDANCE_ROTATION = [
    AttendanceStatus.present,
    AttendanceStatus.present,
    AttendanceStatus.present,
    AttendanceStatus.work_from_home,
    AttendanceStatus.late,
    AttendanceStatus.absent,
]

CHECK_IN_TIMES = ["09:00", "09:15", "09:30", "08:45", "10:00", None]
CHECK_OUT_TIMES = ["17:00", "17:30", "18:00", "16:30", "17:15", None]


def get_last_n_weekdays(n: int) -> list[date]:
    """Return the last n weekdays (Mon-Fri) before today."""
    days = []
    current = date.today() - timedelta(days=1)
    while len(days) < n:
        if current.weekday() < 5:  # Mon=0..Fri=4
            days.append(current)
        current -= timedelta(days=1)
    return list(reversed(days))


async def seed_data():
    env = os.getenv("ENV", "production")
    if env != "development":
        # Production: only create tables, never seed
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Production mode: tables created, no seed data.")
        return

    # Development: drop and recreate public schema (clean slate)
    async with engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)

    print("Development mode: schema reset, seeding data...")

    password = hash_password("password123")

    async with async_session() as session:
        # ── Organization 1: TechVista Solutions ─────────────────────────────
        org1 = Organization(name="TechVista Solutions", slug="techvista", plan=PlanType.pro, industry="Technology")
        session.add(org1)
        await session.flush()

        org1_employees = [
            Employee(org_id=org1.id, name="Sarah Chen", email="sarah@techvista.io", password_hash=password,
                     department=Department.engineering, role=EmployeeRole.cxo, position="CEO",
                     salary=180000.0, status=EmployeeStatus.active, join_date=date(2020, 1, 15)),
            Employee(org_id=org1.id, name="Marcus Rivera", email="marcus@techvista.io", password_hash=password,
                     department=Department.engineering, role=EmployeeRole.lead, position="Tech Lead",
                     salary=140000.0, status=EmployeeStatus.active, join_date=date(2020, 6, 1)),
            Employee(org_id=org1.id, name="Priya Patel", email="priya@techvista.io", password_hash=password,
                     department=Department.design, role=EmployeeRole.senior, position="Senior Designer",
                     salary=120000.0, status=EmployeeStatus.active, join_date=date(2021, 3, 10)),
            Employee(org_id=org1.id, name="Jake Thompson", email="jake@techvista.io", password_hash=password,
                     department=Department.marketing, role=EmployeeRole.mid, position="Marketing Specialist",
                     salary=85000.0, status=EmployeeStatus.active, join_date=date(2022, 1, 5)),
            Employee(org_id=org1.id, name="Aisha Okonkwo", email="aisha@techvista.io", password_hash=password,
                     department=Department.hr, role=EmployeeRole.manager, position="HR Manager",
                     salary=110000.0, status=EmployeeStatus.active, join_date=date(2021, 7, 20)),
            Employee(org_id=org1.id, name="Leo Zhang", email="leo@techvista.io", password_hash=password,
                     department=Department.engineering, role=EmployeeRole.junior, position="Junior Developer",
                     salary=65000.0, status=EmployeeStatus.active, join_date=date(2023, 6, 1)),
            Employee(org_id=org1.id, name="Nina Kowalski", email="nina@techvista.io", password_hash=password,
                     department=Department.finance, role=EmployeeRole.senior, position="Senior Accountant",
                     salary=115000.0, status=EmployeeStatus.active, join_date=date(2021, 9, 15)),
            Employee(org_id=org1.id, name="Omar Siddiqui", email="omar@techvista.io", password_hash=password,
                     department=Department.engineering, role=EmployeeRole.mid, position="Software Engineer",
                     salary=95000.0, status=EmployeeStatus.active, join_date=date(2022, 4, 10)),
        ]
        session.add_all(org1_employees)
        await session.flush()

        # ── Organization 2: Bloom Health Clinic ────────────────────────────
        org2 = Organization(name="Bloom Health Clinic", slug="bloomhealth", plan=PlanType.starter, industry="Healthcare")
        session.add(org2)
        await session.flush()

        org2_employees = [
            Employee(org_id=org2.id, name="Dr. Luna Wright", email="luna@bloomhealth.com", password_hash=password,
                     department=Department.operations, role=EmployeeRole.director, position="Medical Director",
                     salary=200000.0, status=EmployeeStatus.active, join_date=date(2019, 3, 1)),
            Employee(org_id=org2.id, name="Dr. Raj Kumar", email="raj@bloomhealth.com", password_hash=password,
                     department=Department.operations, role=EmployeeRole.senior, position="Senior Physician",
                     salary=170000.0, status=EmployeeStatus.active, join_date=date(2020, 5, 15)),
            Employee(org_id=org2.id, name="Maria Santos", email="maria@bloomhealth.com", password_hash=password,
                     department=Department.support, role=EmployeeRole.mid, position="Patient Coordinator",
                     salary=55000.0, status=EmployeeStatus.active, join_date=date(2021, 8, 10)),
            Employee(org_id=org2.id, name="Tom Bradley", email="tom@bloomhealth.com", password_hash=password,
                     department=Department.finance, role=EmployeeRole.manager, position="Finance Manager",
                     salary=95000.0, status=EmployeeStatus.active, join_date=date(2020, 11, 1)),
            Employee(org_id=org2.id, name="Chen Wei", email="chen@bloomhealth.com", password_hash=password,
                     department=Department.hr, role=EmployeeRole.mid, position="HR Coordinator",
                     salary=60000.0, status=EmployeeStatus.active, join_date=date(2022, 2, 14)),
        ]
        session.add_all(org2_employees)
        await session.flush()

        # ── Organization 3: NovaTech Manufacturing ─────────────────────────
        org3 = Organization(name="NovaTech Manufacturing", slug="novatech", plan=PlanType.enterprise, industry="Manufacturing")
        session.add(org3)
        await session.flush()

        org3_employees = [
            Employee(org_id=org3.id, name="Dr. Alex Morgan", email="alex@novatech.com", password_hash=password,
                     department=Department.operations, role=EmployeeRole.vp, position="VP Operations",
                     salary=190000.0, status=EmployeeStatus.active, join_date=date(2018, 6, 1)),
            Employee(org_id=org3.id, name="Sandra Lee", email="sandra@novatech.com", password_hash=password,
                     department=Department.engineering, role=EmployeeRole.manager, position="Engineering Manager",
                     salary=130000.0, status=EmployeeStatus.active, join_date=date(2019, 9, 15)),
            Employee(org_id=org3.id, name="Ben Okafor", email="ben@novatech.com", password_hash=password,
                     department=Department.sales, role=EmployeeRole.senior, position="Senior Sales",
                     salary=105000.0, status=EmployeeStatus.active, join_date=date(2020, 2, 1)),
            Employee(org_id=org3.id, name="Fatima Al-Rashid", email="fatima@novatech.com", password_hash=password,
                     department=Department.finance, role=EmployeeRole.senior, position="Senior Analyst",
                     salary=110000.0, status=EmployeeStatus.active, join_date=date(2020, 7, 10)),
            Employee(org_id=org3.id, name="Ivan Petrov", email="ivan@novatech.com", password_hash=password,
                     department=Department.engineering, role=EmployeeRole.mid, position="Process Engineer",
                     salary=90000.0, status=EmployeeStatus.active, join_date=date(2021, 11, 1)),
            Employee(org_id=org3.id, name="Grace Kim", email="grace@novatech.com", password_hash=password,
                     department=Department.hr, role=EmployeeRole.manager, position="HR Manager",
                     salary=100000.0, status=EmployeeStatus.active, join_date=date(2021, 4, 15)),
        ]
        session.add_all(org3_employees)
        await session.flush()

        # ── Attendance: last 7 weekdays per employee ───────────────────────
        all_employees = org1_employees + org2_employees + org3_employees
        weekdays = get_last_n_weekdays(7)

        for emp in all_employees:
            for days_ago_idx, day in enumerate(weekdays):
                status_idx = (emp.id + (6 - days_ago_idx)) % 6
                att_status = ATTENDANCE_ROTATION[status_idx]
                check_in = CHECK_IN_TIMES[status_idx]
                check_out = CHECK_OUT_TIMES[status_idx]

                if att_status == AttendanceStatus.absent:
                    check_in = None
                    check_out = None

                att = Attendance(
                    org_id=emp.org_id,
                    employee_id=emp.id,
                    date=day,
                    status=att_status,
                    check_in=check_in,
                    check_out=check_out,
                )
                session.add(att)

        # ── Leave Requests: 7 across orgs ──────────────────────────────────
        today = date.today()
        leave_requests = [
            # Org 1
            LeaveRequest(org_id=org1.id, employee_id=org1_employees[2].id, leave_type=LeaveType.annual,
                         start_date=today + timedelta(days=5), end_date=today + timedelta(days=10),
                         reason="Family vacation", status=LeaveStatus.pending),
            LeaveRequest(org_id=org1.id, employee_id=org1_employees[3].id, leave_type=LeaveType.sick,
                         start_date=today - timedelta(days=3), end_date=today - timedelta(days=1),
                         reason="Flu symptoms", status=LeaveStatus.approved),
            LeaveRequest(org_id=org1.id, employee_id=org1_employees[5].id, leave_type=LeaveType.casual,
                         start_date=today + timedelta(days=2), end_date=today + timedelta(days=3),
                         reason="Personal errands", status=LeaveStatus.pending),
            # Org 2
            LeaveRequest(org_id=org2.id, employee_id=org2_employees[2].id, leave_type=LeaveType.maternity,
                         start_date=today + timedelta(days=30), end_date=today + timedelta(days=120),
                         reason="Maternity leave", status=LeaveStatus.approved),
            LeaveRequest(org_id=org2.id, employee_id=org2_employees[4].id, leave_type=LeaveType.casual,
                         start_date=today + timedelta(days=1), end_date=today + timedelta(days=2),
                         reason="Moving to new apartment", status=LeaveStatus.pending),
            # Org 3
            LeaveRequest(org_id=org3.id, employee_id=org3_employees[4].id, leave_type=LeaveType.annual,
                         start_date=today + timedelta(days=14), end_date=today + timedelta(days=21),
                         reason="Summer holiday", status=LeaveStatus.rejected),
            LeaveRequest(org_id=org3.id, employee_id=org3_employees[2].id, leave_type=LeaveType.sick,
                         start_date=today - timedelta(days=1), end_date=today,
                         reason="Doctor appointment", status=LeaveStatus.pending),
        ]
        session.add_all(leave_requests)

        await session.commit()
        print("Seed data inserted successfully!")
        print(f"  - {len(org1_employees)} employees for TechVista Solutions")
        print(f"  - {len(org2_employees)} employees for Bloom Health Clinic")
        print(f"  - {len(org3_employees)} employees for NovaTech Manufacturing")
        print(f"  - Attendance records for last 7 weekdays")
        print(f"  - 7 leave requests across organizations")
