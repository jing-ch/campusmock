
```markdown
# 🚀 CampusMock: AI-Powered Peer Interview Matching

CampusMock is a high-concurrency orchestration service built with **FastAPI**. It automates the transition from student resume submission to peer interviewer matching using **Claude 3.5 Haiku Vision** and an asynchronous **SendGrid** notification pipeline.

---

## 📂 Project Structure & Responsibilities

| File | Category | Responsibility |
| :--- | :--- | :--- |
| **`main.py`** | **Entry Point** | Manages FastAPI lifespan (Cron startup), logging, and API route registration. |
| **`webhook.py`** | **Student API** | Entry point for students; handles resume uploads and triggers matching. |
| **`accept.py`** | **Interviewer API** | Manages the "Claim" logic using **Atomic Thread Locks** to prevent double-booking. |
| **`matching.py`** | **Logic Engine** | Implements the **Major Cluster Algorithm** for fuzzy matching. |
| **`cv_parser.py`** | **AI Service** | Interfaces with Claude Vision to transform resume images into structured JSON. |
| **`emails.py`** | **Messaging** | Handles SendGrid templates for invitations, confirmations, and 48h alerts. |
| **`cron.py`** | **Background** | Runs the scheduler to fall back to **AI Interviewers** for unclaimed requests. |

---

## ⚙️ Prerequisites & Setup

### 1. Environment Variables (`.env`)
Create a `.env` file in the root. **Do not use quotes** around values [cite: 2026-03-21].
```env
# Anthropic API for Resume Parsing
ANTHROPIC_API_KEY=your_claude_api_key

# SendGrid API for Email Orchestration
SENDGRID_API_KEY=SG.your_sendgrid_key_here

# Verified Sender Email (Must match your SendGrid Verified Identity)
FROM_EMAIL=li.z30@northeastern.edu

# (Optional) Supabase Database Credentials
SUPABASE_URL=your_project_url
SUPABASE_SERVICE_KEY=your_key
```

### 2. Email Identity & Test Configuration
* **Verify Sender**: Complete **Single Sender Verification** in your SendGrid dashboard.
* **Update Sender**: Set `FROM_EMAIL` in `emails.py` to match your verified SendGrid identity.
* **Update Test Recipient (Critical for Testing)**: 
    * Open **`webhook.py`**.
    * Locate the `background_process_submission` function.
    * Change `test_receiver = "example@gmail.com"` to your **own email address** so you can receive the test invitation link.


### 3. Local Installation
```bash
pip install -r requirements.txt 
```

---

## 🧪 Local Verification Steps

### Step 1: Start Server
```bash
uvicorn main:app --reload
```
* **Base API URL**: `http://127.0.0.1:8000/api/v1`
* **Health Check**: `http://127.0.0.1:8000/api/v1/health` (Returns dynamic timestamp).
* **Docs**: `http://127.0.0.1:8000/docs` (Swagger UI).

### Step 2: Test Matching & Email
```bash
python test_webhook.py
```
* **Verification**: Check console for `Status Code 202` and your email for the invitation link.

### Step 3: Test Atomic Locking (Concurrent Claiming)
Open two terminals and run simultaneously to ensure only one person can claim:
```bash
# Terminal 1: Winner
curl "http://127.0.0.1:8000/api/v1/accept?req_id=test_999&intv_id=001"

# Terminal 2: Already Claimed
curl "http://127.0.0.1:8000/api/v1/accept?req_id=test_999&intv_id=002"
```

---

## 🛠 Engineering & Workflow (NEU Hackathon Norms)

### Git Workflow
* **No Direct Push**: Do not push directly to `main`.
* **Branching**: Always create a `feature/<your-name>` branch.
* **Pull Requests**: Merge to `main` only via Pull Requests.

---

feature/jenny
## 🏗 Roadmap
- [x] Claude Vision Resume Parsing
- [x] SendGrid Asynchronous Notification Pipeline
- [x] Atomic Thread-Lock Claiming Mechanism
- [x] 48h Timeout Falling back to AI Interviewer
- [ ] **Next Step**: Transition In-memory states to persistent **MCP Database Layer (Supabase)**.

Supabase project: `https://bcwegwxwyaquycsiyhkx.supabase.co`
Request access from the project owner.  
You can view tables visualized on browser.

## google form

url: form link: https://docs.google.com/forms/d/e/1FAIpQLSdlWd0dXB5bMqNm-0bD9uEAz3QpR_8DU50fl_3a0ZdXhpDU4A/viewform?usp=publish-editor
main
