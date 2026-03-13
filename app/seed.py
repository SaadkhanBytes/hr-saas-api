"""
Seed data: 3 companies with distinct employees, attendance, and leave requests.
Demonstrates complete HR data isolation per organization.
"""

from datetime import date, timedelta
from sqlalchemy import select, text
from app.models import (
    Base, Organization, Employee, Attendance, LeaveRequest,
    PlanType, Department, EmployeeRole, EmployeeStatus,
    AttendanceStatus, LeaveType, LeaveStatus,
)
from app.database import engine, async_session


async def seed_database():
    """Create tables and populate with demo data if empty."""

    async with engine.begin() as conn:
        # Drop everything cleanly (handles old enum types)
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        result = await session.execute(select(Organization).limit(1))
        if result.scalar():
            return

        today = date.today()

        # ══════════════════════════════════════════════════════
        # Organization 1: TechVista Solutions (Tech Startup)
        # ══════════════════════════════════════════════════════
        org1 = Organization(name="TechVista Solutions", slug="techvista", plan=PlanType.PRO, industry="Technology")
        session.add(org1)
        await session.flush()

        emp1 = [
            Employee(org_id=org1.id, name="Sarah Chen", email="sarah@techvista.io", phone="+1-555-0101", department=Department.ENGINEERING, role=EmployeeRole.CXO, position="CTO", salary=185000, status=EmployeeStatus.ACTIVE, join_date=date(2022, 1, 15)),
            Employee(org_id=org1.id, name="Marcus Rivera", email="marcus@techvista.io", phone="+1-555-0102", department=Department.ENGINEERING, role=EmployeeRole.LEAD, position="Tech Lead", salary=145000, status=EmployeeStatus.ACTIVE, join_date=date(2022, 3, 1)),
            Employee(org_id=org1.id, name="Emily Park", email="emily@techvista.io", phone="+1-555-0103", department=Department.DESIGN, role=EmployeeRole.SENIOR, position="Senior UI Designer", salary=120000, status=EmployeeStatus.ACTIVE, join_date=date(2022, 6, 10)),
            Employee(org_id=org1.id, name="Jake Thompson", email="jake@techvista.io", phone="+1-555-0104", department=Department.ENGINEERING, role=EmployeeRole.MID, position="Backend Developer", salary=95000, status=EmployeeStatus.ACTIVE, join_date=date(2023, 2, 20)),
            Employee(org_id=org1.id, name="Aisha Patel", email="aisha@techvista.io", phone="+1-555-0105", department=Department.MARKETING, role=EmployeeRole.MANAGER, position="Marketing Manager", salary=110000, status=EmployeeStatus.ACTIVE, join_date=date(2023, 4, 5)),
            Employee(org_id=org1.id, name="David Kim", email="david@techvista.io", phone="+1-555-0106", department=Department.ENGINEERING, role=EmployeeRole.JUNIOR, position="Junior Developer", salary=70000, status=EmployeeStatus.PROBATION, join_date=date(2024, 11, 1)),
            Employee(org_id=org1.id, name="Lisa Wang", email="lisa@techvista.io", phone="+1-555-0107", department=Department.HR, role=EmployeeRole.SENIOR, position="HR Manager", salary=105000, status=EmployeeStatus.ACTIVE, join_date=date(2022, 2, 14)),
            Employee(org_id=org1.id, name="Ryan Costa", email="ryan@techvista.io", phone="+1-555-0108", department=Department.SALES, role=EmployeeRole.MID, position="Account Executive", salary=85000, status=EmployeeStatus.ON_LEAVE, join_date=date(2023, 8, 1)),
        ]
        session.add_all(emp1)
        await session.flush()

        # Attendance for org1 (last 5 days)
        att_statuses = [
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT],
            [AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME],
            [AttendanceStatus.WORK_FROM_HOME, AttendanceStatus.WORK_FROM_HOME, AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY, AttendanceStatus.PRESENT],
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.LATE],
            [AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT],
            [AttendanceStatus.LATE, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME, AttendanceStatus.PRESENT],
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY],
            [AttendanceStatus.ABSENT, AttendanceStatus.ABSENT, AttendanceStatus.ABSENT, AttendanceStatus.ABSENT, AttendanceStatus.ABSENT],
        ]
        for i, emp in enumerate(emp1):
            for day in range(5):
                d = today - timedelta(days=4 - day)
                session.add(Attendance(
                    org_id=org1.id, employee_id=emp.id, date=d,
                    status=att_statuses[i][day],
                    check_in="09:00" if att_statuses[i][day] != AttendanceStatus.ABSENT else "",
                    check_out="18:00" if att_statuses[i][day] != AttendanceStatus.ABSENT else "",
                ))

        # Leave requests for org1
        session.add_all([
            LeaveRequest(org_id=org1.id, employee_id=emp1[7].id, leave_type=LeaveType.SICK, start_date=today - timedelta(days=4), end_date=today, reason="Flu and fever", status=LeaveStatus.APPROVED),
            LeaveRequest(org_id=org1.id, employee_id=emp1[2].id, leave_type=LeaveType.ANNUAL, start_date=today + timedelta(days=10), end_date=today + timedelta(days=17), reason="Family vacation", status=LeaveStatus.PENDING),
            LeaveRequest(org_id=org1.id, employee_id=emp1[3].id, leave_type=LeaveType.CASUAL, start_date=today + timedelta(days=3), end_date=today + timedelta(days=3), reason="Personal errand", status=LeaveStatus.APPROVED),
            LeaveRequest(org_id=org1.id, employee_id=emp1[0].id, leave_type=LeaveType.ANNUAL, start_date=today - timedelta(days=30), end_date=today - timedelta(days=25), reason="Conference trip", status=LeaveStatus.APPROVED),
        ])

        # ══════════════════════════════════════════════════════
        # Organization 2: Bloom Health Clinic
        # ══════════════════════════════════════════════════════
        org2 = Organization(name="Bloom Health Clinic", slug="bloom-health", plan=PlanType.STARTER, industry="Healthcare")
        session.add(org2)
        await session.flush()

        emp2 = [
            Employee(org_id=org2.id, name="Dr. Luna Wright", email="luna@bloomhealth.com", phone="+1-555-0201", department=Department.OPERATIONS, role=EmployeeRole.DIRECTOR, position="Medical Director", salary=220000, status=EmployeeStatus.ACTIVE, join_date=date(2020, 5, 1)),
            Employee(org_id=org2.id, name="Kai Nakamura", email="kai@bloomhealth.com", phone="+1-555-0202", department=Department.OPERATIONS, role=EmployeeRole.SENIOR, position="Senior Nurse", salary=78000, status=EmployeeStatus.ACTIVE, join_date=date(2021, 3, 15)),
            Employee(org_id=org2.id, name="Priya Sharma", email="priya@bloomhealth.com", phone="+1-555-0203", department=Department.HR, role=EmployeeRole.MID, position="HR Coordinator", salary=62000, status=EmployeeStatus.ACTIVE, join_date=date(2022, 9, 1)),
            Employee(org_id=org2.id, name="Carlos Mendez", email="carlos@bloomhealth.com", phone="+1-555-0204", department=Department.FINANCE, role=EmployeeRole.SENIOR, position="Finance Manager", salary=95000, status=EmployeeStatus.ACTIVE, join_date=date(2021, 7, 20)),
            Employee(org_id=org2.id, name="Amara Johnson", email="amara@bloomhealth.com", phone="+1-555-0205", department=Department.SUPPORT, role=EmployeeRole.JUNIOR, position="Receptionist", salary=42000, status=EmployeeStatus.ACTIVE, join_date=date(2024, 1, 10)),
        ]
        session.add_all(emp2)
        await session.flush()

        for i, emp in enumerate(emp2):
            statuses = [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT]
            if i == 1:
                statuses[2] = AttendanceStatus.HALF_DAY
            if i == 4:
                statuses[3] = AttendanceStatus.LATE
            for day in range(5):
                d = today - timedelta(days=4 - day)
                session.add(Attendance(
                    org_id=org2.id, employee_id=emp.id, date=d,
                    status=statuses[day],
                    check_in="08:30", check_out="17:30",
                ))

        session.add_all([
            LeaveRequest(org_id=org2.id, employee_id=emp2[1].id, leave_type=LeaveType.ANNUAL, start_date=today + timedelta(days=5), end_date=today + timedelta(days=12), reason="Vacation", status=LeaveStatus.PENDING),
            LeaveRequest(org_id=org2.id, employee_id=emp2[3].id, leave_type=LeaveType.SICK, start_date=today - timedelta(days=10), end_date=today - timedelta(days=8), reason="Dental surgery", status=LeaveStatus.APPROVED),
        ])

        # ══════════════════════════════════════════════════════
        # Organization 3: NovaTech Manufacturing
        # ══════════════════════════════════════════════════════
        org3 = Organization(name="NovaTech Manufacturing", slug="novatech-mfg", plan=PlanType.ENTERPRISE, industry="Manufacturing")
        session.add(org3)
        await session.flush()

        emp3 = [
            Employee(org_id=org3.id, name="Dr. Alex Morgan", email="alex@novatech.com", phone="+1-555-0301", department=Department.OPERATIONS, role=EmployeeRole.VP, position="VP Operations", salary=195000, status=EmployeeStatus.ACTIVE, join_date=date(2019, 1, 5)),
            Employee(org_id=org3.id, name="Rachel Kim", email="rachel@novatech.com", phone="+1-555-0302", department=Department.HR, role=EmployeeRole.DIRECTOR, position="HR Director", salary=155000, status=EmployeeStatus.ACTIVE, join_date=date(2019, 3, 10)),
            Employee(org_id=org3.id, name="David Okonkwo", email="david@novatech.com", phone="+1-555-0303", department=Department.ENGINEERING, role=EmployeeRole.LEAD, position="Production Lead", salary=125000, status=EmployeeStatus.ACTIVE, join_date=date(2020, 6, 15)),
            Employee(org_id=org3.id, name="Sofia Martinez", email="sofia@novatech.com", phone="+1-555-0304", department=Department.FINANCE, role=EmployeeRole.MANAGER, position="Finance Manager", salary=115000, status=EmployeeStatus.ACTIVE, join_date=date(2020, 9, 1)),
            Employee(org_id=org3.id, name="James Lee", email="james@novatech.com", phone="+1-555-0305", department=Department.ENGINEERING, role=EmployeeRole.SENIOR, position="Senior Engineer", salary=110000, status=EmployeeStatus.ACTIVE, join_date=date(2021, 2, 20)),
            Employee(org_id=org3.id, name="Nina Petrova", email="nina@novatech.com", phone="+1-555-0306", department=Department.MARKETING, role=EmployeeRole.MID, position="Marketing Specialist", salary=75000, status=EmployeeStatus.ACTIVE, join_date=date(2022, 4, 1)),
            Employee(org_id=org3.id, name="Tom Baker", email="tom@novatech.com", phone="+1-555-0307", department=Department.SUPPORT, role=EmployeeRole.JUNIOR, position="Support Analyst", salary=55000, status=EmployeeStatus.PROBATION, join_date=date(2024, 10, 15)),
            Employee(org_id=org3.id, name="Fatima Al-Rashid", email="fatima@novatech.com", phone="+1-555-0308", department=Department.SALES, role=EmployeeRole.MANAGER, position="Sales Manager", salary=100000, status=EmployeeStatus.ACTIVE, join_date=date(2021, 8, 1)),
            Employee(org_id=org3.id, name="Liam O'Brien", email="liam@novatech.com", phone="+1-555-0309", department=Department.ENGINEERING, role=EmployeeRole.MID, position="QA Engineer", salary=88000, status=EmployeeStatus.ON_LEAVE, join_date=date(2022, 11, 5)),
            Employee(org_id=org3.id, name="Chen Wei", email="chen@novatech.com", phone="+1-555-0310", department=Department.OPERATIONS, role=EmployeeRole.SENIOR, position="Ops Manager", salary=105000, status=EmployeeStatus.ACTIVE, join_date=date(2020, 1, 20)),
        ]
        session.add_all(emp3)
        await session.flush()

        att3_patterns = [
            [AttendanceStatus.PRESENT] * 5,
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT],
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.LATE, AttendanceStatus.PRESENT],
            [AttendanceStatus.PRESENT, AttendanceStatus.HALF_DAY, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT],
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME],
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.ABSENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT],
            [AttendanceStatus.LATE, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT],
            [AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT],
            [AttendanceStatus.ABSENT, AttendanceStatus.ABSENT, AttendanceStatus.ABSENT, AttendanceStatus.ABSENT, AttendanceStatus.ABSENT],
            [AttendanceStatus.PRESENT, AttendanceStatus.WORK_FROM_HOME, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT, AttendanceStatus.PRESENT],
        ]
        for i, emp in enumerate(emp3):
            for day in range(5):
                d = today - timedelta(days=4 - day)
                session.add(Attendance(
                    org_id=org3.id, employee_id=emp.id, date=d,
                    status=att3_patterns[i][day],
                    check_in="07:30" if att3_patterns[i][day] != AttendanceStatus.ABSENT else "",
                    check_out="16:30" if att3_patterns[i][day] != AttendanceStatus.ABSENT else "",
                ))

        session.add_all([
            LeaveRequest(org_id=org3.id, employee_id=emp3[8].id, leave_type=LeaveType.PATERNITY, start_date=today - timedelta(days=4), end_date=today + timedelta(days=10), reason="Paternity leave", status=LeaveStatus.APPROVED),
            LeaveRequest(org_id=org3.id, employee_id=emp3[5].id, leave_type=LeaveType.CASUAL, start_date=today + timedelta(days=2), end_date=today + timedelta(days=2), reason="Moving day", status=LeaveStatus.PENDING),
            LeaveRequest(org_id=org3.id, employee_id=emp3[3].id, leave_type=LeaveType.ANNUAL, start_date=today + timedelta(days=20), end_date=today + timedelta(days=30), reason="Europe trip", status=LeaveStatus.PENDING),
            LeaveRequest(org_id=org3.id, employee_id=emp3[0].id, leave_type=LeaveType.SICK, start_date=today - timedelta(days=15), end_date=today - timedelta(days=14), reason="Cold", status=LeaveStatus.APPROVED),
            LeaveRequest(org_id=org3.id, employee_id=emp3[6].id, leave_type=LeaveType.CASUAL, start_date=today - timedelta(days=5), end_date=today - timedelta(days=5), reason="Doctor visit", status=LeaveStatus.REJECTED),
        ])

        await session.commit()
        print("✅ Database seeded with 3 companies!")
