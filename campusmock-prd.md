# CampusMock — Product Requirements Document

**Version:** 0.1 (MVP)
**Scope:** Hackathon prototype — NEU Seattle only

---

## 1. Problem

NEU students seeking mock interview practice have no trusted, free, peer-based option. Existing tools are expensive or unvetted. Students willing to practice with each other have no way to find and schedule with one another. This harms both career outcomes and student wellbeing.

---

## 2. Solution

CampusMock is a peer-to-peer mock interview matching platform for NEU students. Students submit their profile and interview request via a form. An AI matches them with a suitable peer interviewer. Scheduling is handled via email — no login, no dashboard.

---

## 3. Users

| Type | Description |
|---|---|
| Requester | Student who needs a mock interviewer. Also enters the interviewer pool. |
| Interviewer-only | Student who only wants to be available as a peer interviewer. |

> Every user who submits the form enters the interviewer pool. No exceptions.

---

## 4. User Flows

### 4.1 Entry Point
Student finds a shared link (WhatsApp, forum, newsletter) → clicks → lands on Google Form.

---

### 4.2 Form (Google Form)

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
- Backend sends verification email to NEU address

---

### 4.3 Email Verification

User receives email: "Confirm your NEU email to join CampusMock" → clicks link → `/verify?token=xyz` → record marked verified → enters pool.

- Unverified users are NOT matched.
- Verification link expires in 24 hours.

---

### 4.4 Post-Verification Emails

**Interviewer-only:**
> Friendly confirmation email: "You're in the pool! We'll reach out when someone needs you."

**Requester:**
> "You're in the queue — we're finding your best match. Hang tight!"

---

### 4.5 Matching (Background Job, triggers on verification)

1. Pull all verified, available interviewers from pool (exclude anyone with an open pending request).
2. Filter: at least one of requester's 3 time slots overlaps with interviewer's general availability.
3. If no overlap → skip that candidate.
4. Rank remaining candidates by AI (see §5).
5. Select top N (up to 3). If fewer than 3 qualify, send to however many do.
6. Send invitation email to each selected interviewer.

---

### 4.6 Interviewer Invitation Email

Subject: "Someone needs your help — mock interview request"

Content:
- Requester's name, role, target company, focus area
- The one overlapping time slot (system picks it)
- Accept button → `/accept?token=<unique_token>`

Each interviewer gets a **unique token**. Tokens are single-use.

---

### 4.7 Accept Flow

**First interviewer to click Accept:**
- Backend atomically marks request as `matched`
- Records accepted interviewer
- Redirects to confirmation page: "You're confirmed! Meet [Name] on [Date/Time]. Please coordinate a video link via email."
- Triggers confirmation emails to both requester and interviewer (see §4.8)

**Any subsequent interviewer clicks their Accept link:**
- Backend detects request already matched
- Redirects to: "This session was already claimed — thank you so much for being willing to help!"

---

### 4.8 Confirmation Emails

**To requester:**
> "Great news! [Interviewer Name] will mock interview you on [Date/Time]. Please coordinate a video call link with them directly. Their email: [email]."

**To interviewer (accepted):**
> "You're all set! You'll be mock interviewing [Requester Name] on [Date/Time]. Their email: [email]. Please coordinate a video call link."

---

### 4.9 48-Hour Timeout

- Timer starts from form submission.
- If no interviewer accepts within 48 hours → requester receives:
  > "We couldn't find a match this time. Please try again — more interviewers are joining every day."
- Request is closed. Requester re-enters interviewer pool as available.

---

## 5. AI Matching Logic

**Input per candidate:** CV text (parsed), cultural background, availability, role experience.

**Scoring signals:**
- Availability overlap with requester's 3 slots (hard filter — must pass)
- Requester's open pending request status (hard filter — exclude if pending)
- Cultural background match to requester's preference (soft signal)
- Relevant experience for the role/focus area (soft signal, inferred from CV)

**Model:** Claude API (claude-sonnet). Prompt takes requester profile + list of candidate profiles → returns ranked list with brief reasoning per candidate.

**CV parsing:** On form submission, extract CV text, send to Claude with prompt to return structured JSON: `{ skills, experience_years, past_roles, companies }`. Store this JSON in DB.

---

## 6. Functional Requirements

| # | Requirement |
|---|---|
| F1 | Google Form with branching (requester vs interviewer-only) |
| F2 | On submit, upsert user record in DB (keyed by NEU email) |
| F3 | Send verification email with unique token link |
| F4 | `/verify` endpoint marks user verified and triggers matching if requester |
| F5 | Matching job filters by availability overlap, excludes users with open requests |
| F6 | Claude API ranks candidates, returns top ≤3 |
| F7 | Send invitation emails with unique per-interviewer accept tokens |
| F8 | `/accept` endpoint handles atomic match locking, renders correct UI state |
| F9 | Send confirmation emails to both parties on match |
| F10 | Cron job checks for requests past 48hr with no match → sends sorry email |
| F11 | CV text extraction + Claude-based parsing on upload |

---

## 7. Out of Scope (MVP)

- Cancellation or rescheduling
- Auto-generated video meeting links
- Student dashboard / request status page
- Re-matching after timeout (manual resubmit only)
- Multi-campus support
- Data retention / deletion policy
- Mobile-optimized custom form

---

## 8. Later Improvements

1. **Email verification alternative** — if Google login on form is sufficient proof of NEU identity, skip the extra verification step
2. **Replace Google Form with custom form** — for better UX, branching control, and portfolio value; remove Google account requirement for CV upload
3. **Timezone support** — extend beyond Seattle when other campuses join
4. **Cancellation / reschedule flow** — let matched pairs reschedule without resubmitting
5. **Auto-generated meeting links** — use Whereby API (single call, no OAuth) to generate unique room per match
6. **Re-match on timeout** — automatically try next batch of candidates instead of sending sorry email; send requester an AI mock interview prep kit as fallback
7. **Opt-out of interviewer pool** — let users remove themselves after their match is resolved
8. **Data retention policy** — auto-delete CV and profile data after X months
9. **Multi-campus rollout** — NEU Boston, etc.
10. **Language preference matching** — if platform expands beyond English-only interviews
11. **Interviewer feedback loop** — post-interview rating to improve match quality over time
