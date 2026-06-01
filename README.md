# 🏢 WMS — Workplace Management System

A Flask-based internal tool for managing hybrid work schedules, parking spot reservations, and team visibility across an organisation.

---

## Features

| Module | Description |
|---|---|
| **Authentication** | Register, login, logout with role-based access |
| **Work Status Calendar** | See the whole team's office/remote/PTO status per week |
| **Parking Management** | Reserve, release, and claim parking spots with approval flow |
| **Notifications** | In-app alerts for released spots, claim approvals/rejections |
| **Admin Panel** | Create and manage users, teams, and roles (Executive only) |
| **Reports** | Weekly utilisation stats by team (Team Leader + Executive) |

---

## Roles

| Role | Access |
|---|---|
| `operator` | Set own status, book/release parking, claim released spots |
| `team_leader` | All of above + approve/reject claims, view all users, view reports |
| `executive` | All of above + create/edit users, manage teams, activate/deactivate accounts |

---

## Project Structure

```
workplace_mgmt/
├── run.py                  # Entry point
├── seed.py                 # Populates DB with demo data
├── app.py                  # Flask app factory
├── config.py               # Configuration
├── models.py               # SQLAlchemy ORM models
├── forms.py                # WTForms form definitions
├── requirements.txt
├── routes/
│   ├── auth.py             # Login, register, logout
│   ├── dashboard.py        # Calendar, set status, notifications
│   ├── parking.py          # Book, release, claim, review
│   ├── admin.py            # User/team management, reports
│   └── api.py              # AJAX endpoints
└── templates/
    ├── base.html
    ├── auth/
    ├── dashboard/
    ├── parking/
    └── admin/
```

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/KaranMotwani22/WMS--Workplace-Management-System.git
cd WMS--Workplace-Management-System
cd "Workplace Management System"
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment (optional)

Create a `.env` file in the project root to override defaults:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///workplace.db
```

If no `.env` is provided the app runs with SQLite and a default dev secret key.

### 5. Seed the database

```bash
python seed.py
```

This creates the SQLite database and inserts demo users and teams.

### 6. Run the app

```bash
python run.py
```

Visit **http://127.0.0.1:5000**

---

## Demo Accounts

All accounts use the password: `password`

| Email | Role | Team |
|---|---|---|
| alice@demo.com | Executive | — |
| bob@demo.com | Team Leader | Engineering |
| carol@demo.com | Team Leader | Marketing |
| dave@demo.com | Operator | Engineering |
| eve@demo.com | Operator | Marketing |

---

## Parking Logic

- Only **4 spots** available per day (configurable in `config.py` via `PARKING_SPOTS_TOTAL`)
- A user must have their status set to **Office** before booking parking
- When a spot is released, all other users with Office status that day are notified
- Claims on released spots require **Team Leader approval**
- Approving one claim auto-rejects all other pending claims for the same spot

---

## Tech Stack

- **Backend** — Flask, Flask-SQLAlchemy, Flask-Login, Flask-WTF
- **Database** — SQLite (dev) — swap `DATABASE_URL` for PostgreSQL in production
- **Frontend** — Bootstrap 5.3, Bootstrap Icons, vanilla JS (AJAX calendar navigation)
- **Forms & CSRF** — WTForms + Flask-WTF CSRFProtect

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/week-statuses?offset=N` | All user statuses for a given week |
| GET | `/api/parking/availability?date=YYYY-MM-DD` | Available spots for a date |
| GET | `/api/notifications/unread-count` | Current user's unread notification count |

---

## Notes

- Passwords are hashed with Werkzeug's `generate_password_hash`
- CSRF protection is enabled globally via `CSRFProtect`
- `db.create_all()` runs automatically on startup via `run.py`
- Past dates are blocked on both status setting and parking booking
