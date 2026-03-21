# CampusMock — Technical Design Document

**Version:** 1.0 | **Scope:** MVP — NEU Seattle

---

## 1. Tech Stack

| Layer | Choice |
|---|---|
| Language | Python |
| Framework | FastAPI |
| Database | PostgreSQL (Supabase) |
| File storage | None — JSON only |
| Email | SendGrid |
| PDF extraction | pymupdf |
| AI | Anthropic SDK (claude-sonnet) |
| Background jobs / cron | APScheduler |
| Frontend pages | Jinja2 + Tailwind CDN |
| Form | Google Form + Apps Script webhook |
| Hosting | Railway |

**`requirements.txt`**
```
fastapi
uvicorn
supabase
pymupdf
anthropic
sendgrid
apscheduler
python-dotenv
httpx
jinja2
python-multipart
```

---

## 2. Project Structure

```
campusmock/
├── main.py
├── webhook.py
├── cv_parser.py
├── matching.py          # placeholder — to be designed
├── emails.py
├── accept.py
├── cron.py
├── db.py
├── models.py
├── .env                 # never commit
├── .env.example
├── requirements.txt
└── templates/
    ├── confirmed.html
    └── taken.html
```

---

## 3. Database Schema

### users
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | auto-generated |
| email | TEXT UNIQUE NOT NULL | NEU email, upsert key |
| first_name | TEXT | |
| last_name | TEXT | |
| college | TEXT | |
| major | TEXT | |
| enrollment_semester | TEXT | e.g. "2024sp" |
| languages | TEXT | comma-separated |
| cultural_background | TEXT | comma-separated |
| availability | TEXT | comma-separated buckets |
| cv_parsed | JSONB | `{skills, experience_years, past_roles, companies}` |
| role | TEXT | `requester` \| `interviewer_only` |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

### requests
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| requester_id | UUID FK → users.id | |
| interviewer_id | UUID FK → users.id | nullable, set on match |
| target_company | TEXT | |
| role_title | TEXT | |
| focus_area | TEXT | |
| slot_1 | TIMESTAMPTZ | |
| slot_2 | TIMESTAMPTZ | |
| slot_3 | TIMESTAMPTZ | |
| pref_cultural_bg | TEXT | nullable |
| status | TEXT | `pending` \| `matched` \| `expired` |
| slot_confirmed | TIMESTAMPTZ | nullable, set when someone accepts |
| matched_at | TIMESTAMPTZ | nullable |
| expires_at | TIMESTAMPTZ | created_at + 48hrs |
| created_at | TIMESTAMPTZ | auto |

### tokens
| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| request_id | UUID FK → requests.id | |
| interviewer_id | UUID FK → users.id | |
| token | TEXT UNIQUE | UUID v4, embedded in accept link |
| slot_offered | TIMESTAMPTZ | specific slot included in invitation |
| used | BOOLEAN DEFAULT false | |
| created_at | TIMESTAMPTZ | auto |

---

## 4. API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/webhook` | Receives Apps Script payload on form submit |
| GET | `/accept?token=<uuid>` | Interviewer clicks accept link from email |
| GET | `/health` | Railway health check |

---

## 5. Request Lifecycle

```
Student submits Google Form
        ↓
Apps Script POST /webhook
        ↓
Return 200 OK immediately
        ↓ (background task)
Extract CV text (pymupdf)
        ↓
Parse CV → JSON (Claude)
        ↓
Upsert user row in DB
        ↓
Send confirmation email (SendGrid)
        ↓ (if requester)
Run matching job → [to be designed]
        ↓
Send invitation emails to up to 3 interviewers (unique token each)
        ↓
First interviewer clicks /accept?token=
        ↓
Atomic DB lock (FOR UPDATE) → mark request matched
        ↓
Redirect to /confirmed page
Send confirmation emails to both parties
        ↓
Subsequent interviewers click accept → /taken page
```

**48hr cron** (APScheduler, runs every 15 min): find requests where `expires_at < now` and `status = pending` → send sorry email → set status to `expired`.

---

## 6. CV Parsing

Two-step process: extract raw text from the PDF using pymupdf, then send the text to Claude with a structured prompt. Store the returned JSON in `cv_parsed`. PDF bytes are discarded after parsing.

Parsed JSON shape: `{ skills, experience_years, past_roles, companies }`

---

## 7. Atomic Accept Logic

Use a PostgreSQL `SELECT ... FOR UPDATE` transaction. If `status != 'matched'`, update the request, set `interviewer_id`, `slot_confirmed`, `matched_at`, mark the token as used, and commit. If already matched, rollback and redirect to `/taken`.

---

## 8. Availability Overlap Logic

Interviewer availability is stored as buckets. Requester provides 3 specific datetime slots. Map each slot to its bucket:

| Bucket | When |
|---|---|
| `weekday_morning` | Mon–Fri, 6am–12pm PT |
| `weekday_afternoon` | Mon–Fri, 12pm–5pm PT |
| `weekday_evening` | Mon–Fri, 5pm–10pm PT |
| `weekend` | Sat–Sun, all hours |

If any of the requester's 3 slots maps to a bucket in the interviewer's availability array → overlap exists. Use the first overlapping slot as `slot_offered` in the invitation email.

---

## 9. AI Matching

> **Placeholder — to be designed in a separate session.**

Inputs: requester profile + filtered candidate profiles (availability overlap passed, no open pending request).

Output: ranked list of up to 3 candidate IDs with reasoning.

Model: `claude-sonnet`.

---

## 10. Google Apps Script Webhook

In the Form's Apps Script editor, set up a trigger on form submit. The script fetches the uploaded CV from Google Drive, base64-encodes it, and POSTs the full form payload including `cv_base64` to `/webhook` on Railway.

---

## 11. Email Templates

| Trigger | Recipient | Content |
|---|---|---|
| Interviewer-only submits | Interviewer | You're in the pool. We'll reach out when needed. |
| Requester submits | Requester | You're in the queue. Finding your match now. |
| Match found | Up to 3 interviewers | Request details + overlapping slot + Accept button |
| Accept clicked (first) | Both parties | Confirmed: name, date/time, other party's email |
| 48hr timeout | Requester | No match found. Please resubmit. |

Accept link format:
```
https://<railway-url>/accept?token=<uuid>
```

---

## 12. Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `SENDGRID_API_KEY` | SendGrid API key |
| `BASE_URL` | Railway deployment URL (for accept links) |
| `DATABASE_URL` | Postgres connection string |

---

## 13. Git Conventions

- Never push directly to `main`
- Branch naming: `feature/<n>` e.g. `feature/webhook`, `feature/matching`
- Pull from `main` at the start of every work session
- `.env` is in `.gitignore` — use `.env.example` with placeholder values

---

## 14. Local Environment

Local development uses Docker. See `Dockerfile` in repo root.