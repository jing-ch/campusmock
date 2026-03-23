# CampusMock

> AI-Powered Peer Interview Matching Platform

CampusMock is an automated orchestration service built with **FastAPI**. It streamlines the transition from student resume submission to peer interviewer matching using **Claude 3.5 Sonnet Vision** and an asynchronous **SendGrid** notification pipeline.

---

## 📂 Project Structure

| File | Responsibility |
|------|---------------|
| `main.py` | FastAPI app entry point, lifespan management (Cron startup), and route registration |
| `webhook.py` | Receives form submission, parses CV, upserts user and request to Supabase, and initiates matching |
| `cv_parser.py` | Converts PDF to PNG, sends to Claude Vision, and returns structured JSON resume data |
| `db.py` | Supabase client handling `upsert_user`, `insert_request`, and specialized matching queries |
| `models.py` | Pydantic models for `UserUpsert` and `RequestInsert` |
| `emails.py` | SendGrid email functions for confirmations, invitations, and timeout notifications |
| `matching.py` | Matches requesters with interviewers using Major Cluster and experience logic |
| `accept.py` | Handles interviewer "Claim" flow with Atomic Locking and Idempotency (fixes pre-fetch issues) |
| `cron.py` | Background scheduler for 48-hour timeout logic (falling back to AI) |

---

## ⚙️ Setup

### Environment Variables

Create a `.env` file in the root directory. **Do not use quotes around values.**

```env
# API Keys
ANTHROPIC_API_KEY=your_anthropic_key
SENDGRID_API_KEY=your_sendgrid_key
SUPABASE_URL=your_supabase_project_url
SUPABASE_SERVICE_KEY=your_service_role_key

# Email Configuration
# Must be a verified "Single Sender" in your SendGrid Dashboard
FROM_EMAIL=li.z30@northeastern.edu

# App Configuration
# Use http://localhost:8000 for local dev or your production URL
BASE_URL=http://localhost:8000
DATABASE_URL=your_postgres_connection_string
```

### Supabase Database

The database is hosted on Supabase. For the matching engine to recognize and select interviewers, the `cv_parsed` column in the `users` table must **not be NULL**.

#### Activating Interviewers for Testing

If you are manually adding interviewers to the database, run this SQL in the **Supabase SQL Editor** to make them matchable by the engine:

```sql
UPDATE users 
SET 
  major = 'MS in AI',
  cv_parsed = '{"experience_years": 3, "top_skills": ["Python", "AI"], "summary": "Ready for peer interview test."}'::jsonb
WHERE email = 'your_test_email@northeastern.edu';
```

### Supabase Migrations

Link your project and apply schema migrations:

```bash
supabase link --project-ref your_project_ref
supabase db push
```

---

## 🚀 Running Locally

### Option A — Docker

```bash
docker build -t campusmock .
docker run --env-file .env -p 8000:8000 campusmock
```

### Option B — Standard Installation

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload
```

- **Health Check:** http://localhost:8000/api/v1/health  
- **Form Interface:** http://localhost:8000/form

---

## 🧪 Testing

> **Prerequisites:** Make sure the server is already running before executing any tests.
>
> **Terminal 1 — Start the server:**
> ```bash
> source venv/bin/activate
> uvicorn main:app --reload
> ```
> Keep this terminal running, then open a **new terminal** for the test commands below.

### Full Flow Integration Test

Tests the entire pipeline: Submission → AI Parsing → Matching → Email Notification → Acceptance (Claim via email link)

Open a **new terminal window** (keep the server running in the original one), then run:

```bash
# Activate the virtual environment first
source venv/bin/activate

python tests/test_full_flow.py
```

### Unit Tests

Open a **new terminal window**, then run:

```bash
# Activate the virtual environment first
source venv/bin/activate

# Local
pytest tests/test_webhook.py -v
```

```bash
# Using Docker (no venv needed)
docker run --env-file .env campusmock pytest tests/test_webhook.py -v
```

### ✅ Manual Verification Steps

1. **Start Server** — Ensure the backend is running and connected to Supabase/SendGrid.
2. **Submit Form** — Fill out the form at `/form`. Use an interviewer email you can access.
3. **Check Database:**
   - `users` table: New row created with `cv_parsed` populated via AI.
   - `requests` table: New row created with `status = pending`.
4. **Check Inbox** — Look for an invitation email (check spam if missing).
5. **Claim the Interview** — Click the "Accept" link in the email.
   > **Idempotency note:** `accept.py` handles link pre-fetching by email security scanners — your manual click will still show "Success" even if the link was auto-visited first.

---

## 🛠 Engineering Workflow

- **No Direct Push** — Do not push directly to the `main` branch.
- **Branching** — Create `feature/<your-name>` branches for all new changes.
- **PRs** — Merge to `main` only via approved Pull Requests.
