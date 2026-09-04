#!/usr/bin/env python
"""
MIU-EMS Local Startup
Run once: python start.py
Does everything automatically — no manual config needed.
"""
import os, sys, subprocess, time, webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE  = BASE_DIR / ".env"
SETTINGS  = "config.settings.development"
ADMIN     = {"username": "admin", "password": "Admin@12345", "email": "admin@miu.ac.ug"}

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):   print(f"{GREEN}✅ {msg}{RESET}")
def err(msg):  print(f"{RED}❌ {msg}{RESET}")
def info(msg): print(f"{YELLOW}➜  {msg}{RESET}")
def hdr(msg):  print(f"\n{BOLD}{msg}{RESET}")

def banner():
    print(f"""
{BOLD}╔══════════════════════════════════════════╗
║   Metropolitan International University  ║
║   Employee Management System — Local     ║
╚══════════════════════════════════════════╝{RESET}
""")

def fix_env():
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        patched, has_settings = [], False
        for line in lines:
            s = line.strip()
            if s.startswith("DATABASE_URL=postgresql") or s.startswith("DATABASE_URL=postgres"):
                patched.append("# " + line + "  # disabled for local SQLite")
                ok("Disabled PostgreSQL DATABASE_URL → using SQLite")
            elif "DJANGO_SETTINGS_MODULE" in s and not s.startswith("#"):
                patched.append("DJANGO_SETTINGS_MODULE=" + SETTINGS)
                has_settings = True
            else:
                patched.append(line)
        if not has_settings:
            patched.append("DJANGO_SETTINGS_MODULE=" + SETTINGS)
        ENV_FILE.write_text("\n".join(patched), encoding="utf-8")
    else:
        ENV_FILE.write_text(
            f"DJANGO_SETTINGS_MODULE={SETTINGS}\n"
            "SECRET_KEY=django-insecure-miu-local-dev-only\n"
            "DEBUG=True\n",
            encoding="utf-8"
        )
        ok(".env created for local development")

def run(cmd, capture=False):
    env = {**os.environ, "DJANGO_SETTINGS_MODULE": SETTINGS}
    return subprocess.run(
        [sys.executable, "manage.py"] + cmd,
        cwd=BASE_DIR, env=env,
        capture_output=capture, text=capture
    )

def migrate():
    info("Running database migrations...")
    result = run(["migrate"])
    if result.returncode != 0:
        err("Migration failed. Check errors above.")
        sys.exit(1)
    ok("Migrations complete")

def create_admin():
    info("Setting up admin account...")
    env = {
        **os.environ,
        "DJANGO_SETTINGS_MODULE": SETTINGS,
        "DJANGO_SUPERUSER_USERNAME": ADMIN["username"],
        "DJANGO_SUPERUSER_PASSWORD": ADMIN["password"],
        "DJANGO_SUPERUSER_EMAIL":    ADMIN["email"],
    }
    r = subprocess.run(
        [sys.executable, "manage.py", "createsuperuser", "--no-input"],
        cwd=BASE_DIR, env=env, capture_output=True, text=True
    )
    if r.returncode == 0:
        ok(f"Admin created  →  username: {ADMIN['username']}  |  password: {ADMIN['password']}")
    elif "already exists" in (r.stderr + r.stdout):
        ok(f"Admin already exists  →  username: {ADMIN['username']}  |  password: {ADMIN['password']}")
    else:
        print(f"{YELLOW}⚠️  Could not auto-create admin:{RESET}", r.stderr.strip() or r.stdout.strip())

def seed_demo_data():
    """Seed realistic MIU demo data for presentation."""
    import django
    django.setup()

    import datetime
    from django.contrib.auth import get_user_model
    from apps.departments.models   import Department, Position
    from apps.employees.models     import Employee
    from apps.leave_management.models import LeaveType
    from apps.attendance.models    import Attendance

    User = get_user_model()
    today = datetime.date.today()

    hdr("Seeding demo data...")

    # ── Departments ──────────────────────────────────────────────────
    dept_data = [
        ("Faculty of Computing & Information Technology", "FCIT"),
        ("Faculty of Business & Management",              "FBM"),
        ("Faculty of Education",                          "FED"),
        ("Human Resources Department",                    "HRD"),
        ("Finance Department",                            "FIN"),
        ("Registry & Academic Affairs",                   "RAA"),
    ]
    depts = {}
    for name, code in dept_data:
        d, created = Department.objects.get_or_create(
            code=code, defaults={"name": name}
        )
        depts[code] = d
    ok(f"Departments ready ({len(depts)})")

    # ── Positions ────────────────────────────────────────────────────
    pos_data = [
        ("Lecturer",              "FCIT"), ("Senior Lecturer",      "FCIT"),
        ("HOD Computing",         "FCIT"), ("Lecturer",              "FBM"),
        ("Senior Lecturer",       "FBM"),  ("Lecturer",              "FED"),
        ("HR Officer",            "HRD"),  ("HR Manager",            "HRD"),
        ("Finance Officer",       "FIN"),  ("Registrar",             "RAA"),
        ("Assistant Registrar",   "RAA"),
    ]
    positions = {}
    for title, dept_code in pos_data:
        p, _ = Position.objects.get_or_create(
            title=title, department=depts[dept_code]
        )
        positions[(title, dept_code)] = p
    ok(f"Positions ready ({len(positions)})")

    # ── Leave Types ──────────────────────────────────────────────────
    leave_types = [
        ("Annual Leave",        21, "Standard annual leave entitlement"),
        ("Sick Leave",          10, "Medical/illness leave"),
        ("Maternity Leave",     60, "Maternity leave for female staff"),
        ("Paternity Leave",      5, "Paternity leave for male staff"),
        ("Study Leave",         14, "Leave for academic or professional study"),
        ("Compassionate Leave",  3, "Bereavement or family emergency"),
        ("Unpaid Leave",         0, "Leave without pay, approved by management"),
    ]
    for name, days, desc in leave_types:
        LeaveType.objects.get_or_create(
            name=name, defaults={"default_annual_days": days, "description": desc}
        )
    ok(f"Leave types ready ({len(leave_types)})")

    # ── Demo Employees ───────────────────────────────────────────────
    employees_data = [
        # (emp_id, first, last, email, dept_code, position_title, emp_type, username, password, role)
        ("MIU-2023-001", "Grace",    "Nakato",    "g.nakato@miu.ac.ug",   "FCIT", "HOD Computing",      "FULL_TIME", "nakato",    "Pass@2025", "DEPARTMENT_HEAD"),
        ("MIU-2023-002", "Robert",   "Mugisha",   "r.mugisha@miu.ac.ug",  "FCIT", "Senior Lecturer",    "FULL_TIME", "mugisha",   "Pass@2025", "EMPLOYEE"),
        ("MIU-2023-003", "Patricia", "Auma",      "p.auma@miu.ac.ug",     "FBM",  "Lecturer",           "FULL_TIME", "auma",      "Pass@2025", "EMPLOYEE"),
        ("MIU-2024-001", "David",    "Ssemakula", "d.ssemakula@miu.ac.ug","FED",  "Lecturer",           "FULL_TIME", "ssemakula", "Pass@2025", "EMPLOYEE"),
        ("MIU-2022-001", "Florence", "Nabirye",   "f.nabirye@miu.ac.ug",  "HRD",  "HR Manager",         "FULL_TIME", "nabirye",   "Pass@2025", "HR"),
        ("MIU-2022-002", "Joseph",   "Okello",    "j.okello@miu.ac.ug",   "HRD",  "HR Officer",         "FULL_TIME", "okello",    "Pass@2025", "HR"),
        ("MIU-2021-001", "Sarah",    "Kyomugisha","s.kyomugisha@miu.ac.ug","FIN",  "Finance Officer",    "FULL_TIME", "kyomugisha","Pass@2025", "EMPLOYEE"),
        ("MIU-2020-001", "Emmanuel", "Tumwine",   "e.tumwine@miu.ac.ug",  "RAA",  "Registrar",          "FULL_TIME", "tumwine",   "Pass@2025", "MANAGEMENT"),
        ("MIU-2024-002", "Brenda",   "Atim",      "b.atim@miu.ac.ug",     "FBM",  "Senior Lecturer",    "FULL_TIME", "atim",      "Pass@2025", "EMPLOYEE"),
        ("MIU-2024-003", "Moses",    "Wanyama",   "m.wanyama@miu.ac.ug",  "FCIT", "Lecturer",           "CONTRACT",  "wanyama",   "Pass@2025", "EMPLOYEE"),
    ]

    created_employees = []
    for (eid, fn, ln, email, dept_code, pos_title, emp_type, uname, pwd, role) in employees_data:
        # Create or get user account
        user, u_created = User.objects.get_or_create(
            username=uname,
            defaults={"email": email, "first_name": fn, "last_name": ln, "role": role}
        )
        if u_created:
            user.set_password(pwd)
            user.save()

        # Create or get employee profile
        emp, e_created = Employee.objects.get_or_create(
            employee_id=eid,
            defaults={
                "user": user,
                "first_name": fn,
                "last_name": ln,
                "email": email,
                "employment_type": emp_type,
                "employment_status": "ACTIVE",
                "date_joined_org": today.replace(year=int(eid.split("-")[1])),
                "department": depts[dept_code],
                "position": positions.get((pos_title, dept_code)),
            }
        )
        if e_created and not emp.user:
            emp.user = user
            emp.save()
        created_employees.append(emp)

    ok(f"Demo employees ready ({len(created_employees)})")

    # ── Link admin to employee profile ───────────────────────────────
    try:
        admin_user = User.objects.get(username=ADMIN["username"])
        if not Employee.objects.filter(user=admin_user).exists():
            emp, _ = Employee.objects.get_or_create(
                employee_id="MIU-ADMIN-001",
                defaults={
                    "user": admin_user,
                    "first_name": "System",
                    "last_name": "Administrator",
                    "email": ADMIN["email"],
                    "employment_type": "FULL_TIME",
                    "employment_status": "ACTIVE",
                    "date_joined_org": today,
                }
            )
            ok("Admin employee profile linked")
        else:
            ok("Admin employee profile already linked")
    except Exception as e:
        print(f"{YELLOW}⚠️  Admin profile: {e}{RESET}")

    # ── Today's Attendance for all active employees ──────────────────
    att_statuses = ["PRESENT","PRESENT","PRESENT","PRESENT","PRESENT",
                    "PRESENT","LATE","PRESENT","PRESENT","ON_LEAVE"]
    try:
        all_emps = Employee.objects.filter(employment_status="ACTIVE")
        att_count = 0
        for i, emp in enumerate(all_emps):
            status = att_statuses[i % len(att_statuses)]
            _, created = Attendance.objects.get_or_create(
                employee=emp,
                date=today,
                defaults={
                    "status": status,
                    "check_in_time": datetime.time(8, 0) if status == "PRESENT" else (
                        datetime.time(9, 15) if status == "LATE" else None
                    ),
                }
            )
            if created:
                att_count += 1
        ok(f"Today's attendance seeded ({att_count} new records)")
    except Exception as e:
        print(f"{YELLOW}⚠️  Attendance seed skipped: {e}{RESET}")

    hdr("Demo data ready.")
    print(f"""
  {BOLD}Demo accounts for presentation:{RESET}
  ┌─────────────┬──────────────┬─────────────────┐
  │ Username    │ Password     │ Role            │
  ├─────────────┼──────────────┼─────────────────┤
  │ admin       │ Admin@12345  │ Administrator   │
  │ nabirye     │ Pass@2025    │ HR Manager      │
  │ nakato      │ Pass@2025    │ Department Head │
  │ mugisha     │ Pass@2025    │ Employee        │
  │ tumwine     │ Pass@2025    │ Management      │
  └─────────────┴──────────────┴─────────────────┘
""")

def start_server():
    url = "http://127.0.0.1:8000"
    print(f"""
{BOLD}🚀 Server starting...{RESET}
   App:   {url}
   Admin: {url}/admin
   Stop   →  Ctrl+C
""")
    time.sleep(1)
    webbrowser.open(url)
    run(["runserver"])

if __name__ == "__main__":
    banner()
    fix_env()
    migrate()
    create_admin()
    seed_demo_data()
    start_server()
