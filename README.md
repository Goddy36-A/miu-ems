# MIU Employee Management System (MIU-EMS)

Django implementation for *Evaluating the Effectiveness of an Employee
Management System on Workforce Administration and Organizational
Performance in Metropolitan International University*.

> **Branding notice:** the MIU logo and color palette used in this app are
> a placeholder theme (see `config/settings/base.py` → `MIU_BRANDING`),
> not verified official MIU branding. Replace them in one place once
> official assets are supplied.
>
> **Data notice:** no real MIU employee records, departments, or
> statistics are included. `seed_demo_data` loads clearly-labeled sample
> data only.

## Quick Start (local development, SQLite)

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env              # edit as needed; SQLite works out of the box

export DJANGO_SETTINGS_MODULE=config.settings.development
python manage.py migrate
python manage.py seed_demo_data   # optional: sample departments/employees/leave types
python manage.py createsuperuser  # optional: separate real admin account
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`. If you ran `seed_demo_data`, sign in with
any of: `admin_demo`, `hr_demo`, `depthead_demo`, `employee_demo`,
`management_demo` — password `ChangeMe123!` for all. **Change these
immediately in any shared/deployed environment.**

## Running Tests

```bash
export DJANGO_SETTINGS_MODULE=config.settings.testing
python manage.py test apps
```

## Using PostgreSQL

Set `DATABASE_URL` in `.env`, e.g.:

```
DATABASE_URL=postgres://miu_ems_user:changeme@localhost:5432/miu_ems
```

Then re-run `python manage.py migrate`.

## Project Structure

```
config/settings/{base,development,testing,production}.py   # environment-based settings
apps/
  core/            # shared abstract models, RBAC helpers, branding, error pages
  accounts/        # custom User model, auth views, account lockout
  departments/     # Department, Position
  employees/       # Employee profile, self-service vs HR forms
  attendance/      # Attendance records + rate calculation service
  leave_management/# LeaveType, LeaveRequest workflow, LeaveBalance
  performance/     # PerformanceCycle/Criterion/Evaluation/Score, weighted scoring
  notifications/   # In-app notifications
  documents/       # Secure employee document storage (private, authorization-gated)
  audit/           # Immutable AuditLog + middleware
  reports/         # Role-restricted HR/workforce reports + CSV export
  dashboard/       # Role-specific dashboards + system-effectiveness evaluation module
templates/         # MIU-branded templates (base.html + per-app)
static/            # miu-theme.css, placeholder logo
```

## Security Notes

- Authorization is enforced server-side in every view (see
  `apps/core/permissions.py`) — never only by hiding UI elements.
- Employee documents are stored under `PRIVATE_MEDIA_ROOT`, outside any
  publicly served media path, and are only reachable through
  `documents:download`, which checks authorization and logs every access.
- Account lockout after 5 failed login attempts (`apps/accounts/backends.py`).
- All sensitive actions are recorded in an immutable `AuditLog`
  (no update/delete path exists anywhere in the app).
- `config/settings/production.py` refuses to start against SQLite and
  enforces HTTPS/HSTS/secure-cookie settings.

## What's Implemented vs. Outstanding

Implemented: employee/department/position management, attendance +
rate calculation, full leave approval workflow with balances,
configurable weighted performance evaluations, secure document storage,
in-app notifications, role-based dashboards, HR/workforce reports + CSV
export, the system-effectiveness evaluation module (baseline vs.
post-implementation indicators, satisfaction survey), immutable audit
logging, and an automated test suite covering the leave workflow,
attendance calculations, performance scoring, and authorization
boundaries (IDOR/privilege-escalation checks).

Not yet implemented (natural next steps): DRF API endpoints, Celery/Redis
async notifications, PDF/Excel export beyond CSV, full accessibility
audit, deployment manifests (Nginx/Gunicorn config files), and the
formal academic System Analysis and Design document (deferred per your
request to prioritize code first).

## Deploying to Render

This repo includes a Render Blueprint (`render.yaml`) that provisions a
free-tier web service plus a managed PostgreSQL database.

1. Push this repo to GitHub (see below).
2. In the Render dashboard: **New → Blueprint**, point it at your repo.
   Render reads `render.yaml` and creates the web service + database.
3. After the first deploy, set these env vars on the web service if you
   need them (Render's dashboard → Environment):
   - `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` — for real
     password-reset emails (defaults to Django's console backend, which
     only logs emails, if unset).
   - `CSRF_TRUSTED_ORIGINS` — usually auto-added from Render's hostname,
     but set explicitly if you attach a custom domain.
4. `build.sh` runs `collectstatic` and `migrate` on every deploy.
   Uncomment the `seed_demo_data` line in `build.sh` only for a demo
   deployment — never on a real institutional deployment.

**Important — Render free-tier disks are ephemeral.** Uploaded employee
documents and profile photos (stored under `PRIVATE_MEDIA_ROOT` /
`MEDIA_ROOT`) will be **lost on every redeploy or restart** unless you
attach a persistent [Render Disk](https://render.com/docs/disks) (paid)
or move file storage to S3-compatible object storage. Do not use the
free tier for real employee documents.

## Pushing to GitHub

```bash
git init
git add .
git commit -m "Initial commit: MIU-EMS Django implementation"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```
