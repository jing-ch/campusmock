# CampusMock: AI-Powered Peer Interview Matching

---

## Project Structure

| File | Responsibility |
| :--- | :--- |
| `main.py` | FastAPI app entry point, lifespan management, route registration |
| `webhook.py` | Receives form submission, parses CV, upserts user and request to Supabase, sends confirmation email |
| `cv_parser.py` | Converts PDF to PNG, sends to Claude Vision, returns structured JSON |
| `db.py` | Supabase client, `upsert_user` and `insert_request` functions |
| `models.py` | Pydantic models for `UserUpsert` and `RequestInsert` |
| `emails.py` | SendGrid email functions for confirmations, invitations, and timeout notifications |
| `matching.py` | Matches requesters with interviewers |
| `accept.py` | Handles interviewer accept flow with atomic locking |
| `cron.py` | Background scheduler for 48-hour timeout logic |

---

## Setup

### Environment Variables

Create a `.env` file in the root:

```env
ANTHROPIC_API_KEY=your_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
SENDGRID_API_KEY=your_sendgrid_key
BASE_URL=https://your-railway-url.up.railway.app
DATABASE_URL=your_postgres_connection_string
```

### Supabase Database

The database is hosted on Supabase and has a visual, interactive dashboard where you can browse and edit tables directly in the browser. Request access from the project owner to view it.

### Supabase Migrations

Link your project and apply schema migrations:

```bash
supabase link --project-ref bcwegwxwyaquycsiyhkx
supabase db push
```

To create a new migration:

```bash
# Add a new SQL file to supabase/migrations/ then push
supabase db push
```

---

## Running Locally

### Option A — Docker

```bash
docker build -t campusmock .
docker run --env-file .env -p 8000:8000 campusmock
```

### Option B — Without Docker

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Form is available at `http://localhost:8000/form`.

---

## Running Tests

### Docker

```bash
docker run --env-file .env campusmock pytest tests/test_webhook.py -v
```

### Without Docker

```bash
pytest tests/test_webhook.py -v
```

---

## Manual Testing

1. Start the server locally (Docker or without Docker)
2. Open `http://localhost:8000/form` in your browser
3. Fill in the form and submit
4. Check:
   - **Supabase dashboard → `users` table** — new row with `cv_parsed` populated
   - **Supabase dashboard → `requests` table** — new row with `status = pending` (requesters only)
   - **Your inbox** — confirmation email from SendGrid

---

## Git Workflow

- No direct push to `main`
- Branch naming: `feature/<name>` e.g. `feature/webhook`, `feature/matching`
- Merge to `main` via Pull Requests only
