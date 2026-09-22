# CS CyberSafe Learn

**Project:** Design and Implementation of an E-Learning Platform for Cyber Safety Education.

A Flask + SQLite educational platform implementing structured cyber-safety courses, learner accounts, profile management, progress tracking, lesson knowledge checks, scenario practice, final assessments, automatically issued certificates, QR verification and an administrator area.

## Run locally

1. Install Python 3.11+.
2. Open this folder in VS Code.
3. Double-click `RUN.bat`.
4. Visit `http://127.0.0.1:5000`.

The script creates `.venv` and installs `requirements.txt`. No XAMPP or MySQL is required.

## Demo accounts

- Administrator: `admin@cybersafe.local` / `Admin@12345`
- Student: `student@cybersafe.local` / `Student@12345`

Change these credentials before any public deployment.

## Deployment

Set a strong `SECRET_KEY` and a PostgreSQL `DATABASE_URL` in the deployment environment. Gunicorn is configured through `Procfile`.

Example start command: `gunicorn run:app`

For Render, connect the GitHub repository, configure the environment variables, and use the Gunicorn start command. The application uses SQLAlchemy so PostgreSQL can replace SQLite without changing the learning logic.

## Research basis

The educational approach is designed to be informed by authoritative cybersecurity and digital-safety guidance such as NIST and CISA, with UNICEF and other reputable privacy/digital-safety sources used where appropriate. Lesson wording in this demonstration is original and intentionally beginner-friendly.

## Security notes

Passwords are hashed; CSRF protection is enabled; admin routes require the admin role; server-side validation is used; secrets belong in environment variables; certificate QR codes contain a verification URL/ID rather than sensitive learner data.


## Certificate workflow

A learner becomes certificate-eligible after completing all required lessons and passing the course final assessment at 70% or above. The system automatically creates a unique certificate ID, stores the issue date, provides a certificate page and professional PDF download, and exposes a public verification page through the QR code.

## Learner profile

Authenticated learners can open Profile from the main navigation to update their full name and email address and optionally change their password. Existing account fields are reused so this UI improvement does not require destructive database changes.
