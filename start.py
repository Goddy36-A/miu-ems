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

def ok(msg):  print(f"{GREEN}✅ {msg}{RESET}")
def err(msg): print(f"{RED}❌ {msg}{RESET}")
def info(msg):print(f"{YELLOW}➜  {msg}{RESET}")

def banner():
    print(f"""
{BOLD}╔══════════════════════════════════════════╗
║   Metropolitan International University  ║
║   Employee Management System — Local     ║
╚══════════════════════════════════════════╝{RESET}
""")

def fix_env():
    """Create or patch .env so SQLite is used locally."""
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
        patched = []
        has_settings = False
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

def start_server():
    url = "http://127.0.0.1:8000"
    print(f"""
{BOLD}🚀 Server starting...{RESET}
   App:   {url}
   Admin: {url}/admin

   Login  →  {ADMIN['username']} / {ADMIN['password']}
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
    start_server()
