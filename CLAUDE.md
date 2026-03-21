# CampusMock — Project Context for Claude Code

## PRD

# CampusMock — Product Requirements Document

**Version:** 0.2 (MVP)
**Scope:** Hackathon prototype — NEU Seattle only

---

### 1. Problem

NEU students seeking mock interview practice have no trusted, free, peer-based option. Existing tools are expensive or unvetted. Students willing to practice with each other have no way to find and schedule with one another. This harms both career outcomes and student wellbeing.

---

### 2. Solution

CampusMock is a peer-to-peer mock interview matching platform for NEU students. Students submit their profile and interview request via a form. An AI matches them with a suitable peer interviewer. Scheduling is handled via email — no login, no dashboard.

---

### 3. Design Principles

**Email-first UX:** All user interactions happen through email. No login, no dashboard. The only custom frontend pages are the accept/taken confirmation screens triggered by email links. This lowers participation barriers and meets students where they already are.

---

### 4. Users

| Type | Description |
|---|---|
| Requester | Student who needs a mock interviewer. Also enters the interviewer pool. |
| Interviewer-only | Student who only wants to be available as a peer interviewer. |

> Every user who submits the form enters the interviewer pool. No exceptions.

---

### 5. User Flows

#### 5.1 Entry Point
Student finds a shared link (WhatsApp, forum, newsletter) → clicks → lands on Google Form.

#### 5.2 Form (Google Form)

**Step 1 — Intent selection (required, branching)**
- Option A: "I want a mock interview (and I'll join the interviewer pool)"
- Option B: "I only want to be an interviewer candidate"

**Fields for ALL users:**
- Full name
- NEU email address
- College
- Major
- Enrollment semester
- Cultural background
- General availability as interviewer (multi-select: weekday morning / weekday afternoon / weekday evening / weekend)
- CV upload (PDF)

**Additional fields for Option A (Requester) only:**
- Target company
- Role applying for
- Interview focus area (e.g. LeetCode, system design, behavioral)
- 3 specific available time slots (as interviewee)
- Preferred interviewer cultural background

**On submit:**
- User's data is saved/overwritten in DB (keyed by NEU email)
- User immediately enters the pool
- If requester, matching job triggers immediately

#### 5.3 Post-Submit Emails

**Interviewer-only:**
> Friendly confirmation email: "You're in the pool! We'll reach out when someone needs you."

**Requester:**
> "You're in the queue — we're finding your best match. Hang tight!"

#### 5.4 Matching (Background Job, triggers on form submit)

1. Pull all available interviewers from pool (exclude anyone with an open pending request).
2. Filter: at least one of requester's 3 time slots overlaps with interviewer's general availability.
3. If no overlap → skip that candidate.
4. Rank remaining candidates by AI (see §6).
5. Select top N (up to 3). If fewer than 3 qualify, send to however many do.
6. Send invitation email to each selected interviewer.

#### 5.5 Interviewer Invitation Email

Subject: "Someone needs your help — mock interview request"

Content:
- Requester's name, role, target company, focus area
- The one overlapping time slot (system picks it)
- Accept button → `/accept?token=<unique_token>`

Each interviewer gets a **unique token**. Tokens are single-use.

#### 5.6 Accept Flow

**First interviewer to click Accept:**
- Backend atomically marks request as `matched`
- Records accepted interviewer
- Redirects to confirmation page: "You're confirmed! Meet [Name] on [Date/Time]. Please coordinate a video link via email."
- Triggers confirmation emails to both requester and interviewer (see §5.7)

**Any subsequent interviewer clicks their Accept link:**
- Backend detects request already matched
- Redirects to: "This session was already claimed — thank you so much for being willing to help!"

#### 5.7 Confirmation Emails

**To requester:**
> "Great news! [Interviewer Name] will mock interview you on [Date/Time]. Please coordinate a video call link with them directly. Their email: [email]."

**To interviewer (accepted):**
> "You're all set! You'll be mock interviewing [Requester Name] on [Date/Time]. Their email: [email]. Please coordinate a video call link."

#### 5.8 48-Hour Timeout

- Timer starts from form submission.
- If no interviewer accepts within 48 hours → requester receives:
  > "We couldn't find a match this time. Please try again — more interviewers are joining every day."
- Request is closed. Requester re-enters interviewer pool as available.

---

### 6. AI Matching Logic

**Input per candidate:** CV text (parsed), cultural background, availability, role experience.

**Scoring signals:**
- Availability overlap with requester's 3 slots (hard filter — must pass)
- Open pending request status (hard filter — exclude if pending)
- Cultural background match to requester's preference (soft signal)
- Relevant experience for the role/focus area (soft signal, inferred from CV)

**Model:** Claude API (claude-sonnet). Prompt takes requester profile + list of candidate profiles → returns ranked list with brief reasoning per candidate.

**CV parsing:** On form submission, extract CV text, send to Claude with prompt to return structured JSON: `{ skills, experience_years, past_roles, companies }`. Store this JSON in DB.

---

### 7. Functional Requirements

| # | Requirement |
|---|---|
| F1 | Google Form with branching (requester vs interviewer-only) |
| F2 | On submit, upsert user record in DB (keyed by NEU email), trigger matching if requester |
| F3 | Send post-submit confirmation email (interviewer-only or requester) |
| F4 | Matching job filters by availability overlap, excludes users with open requests |
| F5 | Claude API ranks candidates, returns top ≤3 |
| F6 | Send invitation emails with unique per-interviewer accept tokens |
| F7 | `/accept` endpoint handles atomic match locking, renders correct UI state |
| F8 | Send confirmation emails to both parties on match |
| F9 | Cron job checks for requests past 48hr with no match → sends sorry email |
| F10 | CV text extraction + Claude-based parsing on upload |

---

### 8. Out of Scope (MVP)
- Email verification
- Cancellation or rescheduling
- Auto-generated video meeting links
- Student dashboard / request status page
- Re-matching after timeout (manual resubmit only)
- Multi-campus support
- Data retention / deletion policy
- Mobile-optimized custom form

---

## TDD

# CampusMock — Technical Design Document

**Version:** 1.0 | **Scope:** MVP — NEU Seattle

---

### 1. Tech Stack

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

### 2. Project Structure

```
campusmock/
├── main.py
├── webhook.py
├── cv_parser.py
├── matching.py
├── emails.py
├── accept.py
├── cron.py
├── db.py
├── models.py
├── .env
├── .env.example
├── requirements.txt
└── templates/
    ├── confirmed.html
    └── taken.html
```

---

### 3. Database Schema

#### users
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
| role | TEXT | `requester` or `interviewer_only` |
| created_at | TIMESTAMPTZ | auto |
| updated_at | TIMESTAMPTZ | auto |

#### requests
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
| status | TEXT | `pending`, `matched`, or `expired` |
| slot_confirmed | TIMESTAMPTZ | nullable, set when someone accepts |
| matched_at | TIMESTAMPTZ | nullable |
| expires_at | TIMESTAMPTZ | created_at + 48hrs |
| created_at | TIMESTAMPTZ | auto |

#### tokens
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

### 4. API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/webhook` | Receives Apps Script payload on form submit |
| GET | `/accept?token=<uuid>` | Interviewer clicks accept link from email |
| GET | `/health` | Railway health check |

---

### 5. Request Lifecycle

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
Run matching job
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

### 6. CV Parsing

Two-step process: extract raw text from the PDF using pymupdf, then send the text to Claude with a structured prompt. Store the returned JSON in `cv_parsed`. PDF bytes are discarded after parsing.

Parsed JSON shape: `{ skills, experience_years, past_roles, companies }`

---

### 7. Atomic Accept Logic

Use a PostgreSQL `SELECT ... FOR UPDATE` transaction. If `status != 'matched'`, update the request, set `interviewer_id`, `slot_confirmed`, `matched_at`, mark the token as used, and commit. If already matched, rollback and redirect to `/taken`.

---

### 8. Availability Overlap Logic

| Bucket | When |
|---|---|
| `weekday_morning` | Mon–Fri, 6am–12pm PT |
| `weekday_afternoon` | Mon–Fri, 12pm–5pm PT |
| `weekday_evening` | Mon–Fri, 5pm–10pm PT |
| `weekend` | Sat–Sun, all hours |

If any of the requester's 3 slots maps to a bucket in the interviewer's availability array → overlap exists. Use the first overlapping slot as `slot_offered` in the invitation email.

---

### 9. AI Matching

Inputs: requester profile + filtered candidate profiles (availability overlap passed, no open pending request).

Output: ranked list of up to 3 candidate IDs with reasoning.

Model: `claude-sonnet`.

---

### 10. Google Apps Script Webhook

In the Form's Apps Script editor, set up a trigger on form submit. The script fetches the uploaded CV from Google Drive, base64-encodes it, and POSTs the full form payload including `cv_base64` to `/webhook` on Railway.

---

### 11. Email Templates

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

### 12. Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key |
| `SENDGRID_API_KEY` | SendGrid API key |
| `BASE_URL` | Railway deployment URL (for accept links) |
| `DATABASE_URL` | Postgres connection string |

---

### 13. Git Conventions

- Never push directly to `main`
- Branch naming: `feature/<n>` e.g. `feature/webhook`, `feature/matching`
- Pull from `main` at the start of every work session
- `.env` is in `.gitignore` — use `.env.example` with placeholder values

### 14. Local Environment

Local development uses Docker. See `Dockerfile` in repo root.