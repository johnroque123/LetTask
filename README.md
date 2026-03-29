# LetTask 📋

A full-featured personal productivity web app built with Django — manage tasks, habits, notes, schedules, and get AI assistance, all in one place.

---

## Features

- **Todo / Tasks** — Create, update, delete, and track tasks with priorities, categories, and due dates
- **Habits Tracker** — Track daily habits with streaks, heatmaps, and completion rates
- **Notes** — Pin, archive, and manage personal notes with color coding
- **Calendar & Schedules** — Visualize tasks and schedules on a monthly calendar with day-modal detail view
- **AI Chatbot** — Gemini-powered assistant integrated into the app
- **Authentication** — Register, login with OTP verification, brute-force lockout, and secure password reset

---

## Tech Stack

- **Backend** — Django 5.x, Python 3.13
- **Database** — SQLite
- **AI** — Google Gemini API (`gemini-2.5-flash`)
- **Styling** — Tailwind CSS (CDN)
- **Email** — Gmail SMTP
- **Static files** — WhiteNoise
- **Containerization** — Docker & Docker Compose

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) & Docker Compose installed
- A `.env` file (see below)

---

### Environment Variables

Create a `.env` file in the project root (same level as `manage.py`):

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=http://localhost:8000

EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

GEMINI_API_KEY=your-gemini-api-key

SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_SSL_REDIRECT=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
TRUSTED_PROXY_COUNT=0
```

> For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) — not your regular password.

---

### Run with Docker Compose

```bash
# Clone the repo
git clone https://github.com/johnroque123/LetTask.git
cd LetTask

# Build and start
docker compose up --build

# In a separate terminal — run migrations
docker compose exec web python manage.py migrate

# Create a superuser (optional)
docker compose exec web python manage.py createsuperuser
```

Visit: [http://localhost:8000](http://localhost:8000)

To stop the app:

```bash
docker compose down
```

---

## Project Structure

```
manager/
├── task/               # Project settings & URLs
├── registration/       # Auth — login, register, OTP, password reset, chatbot
├── todo/               # Tasks & dashboard
├── notes/              # Notes app
├── habits/             # Habits tracker
├── templates/          # All HTML templates
├── staticfiles/        # Collected static files
├── manage.py
├── docker-compose.yml
└── .env                # Environment variables (never committed)
```
