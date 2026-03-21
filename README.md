# CampusMock

Peer-to-peer mock interview matching for NEU students. hackathon project.

**Stack:** Python, FastAPI, PostgreSQL (Supabase), SendGrid, Railway, Docker

---

## Local Setup

1. Clone the repo
2. Copy `.env.example` to `.env` and fill in values
3. `docker build -t campusmock .`
4. `docker run -p 8000:8000 campusmock`
5. Hit `http://localhost:8000/health` — expect `{"status": "ok"}`

## Environment Variables

See `.env.example` for required variables.

## Git Workflow

- Never push directly to `main`
- Branch naming: `feature/<name>` e.g. `feature/webhook`
- Pull from `main` at the start of every session
- Merge feature branches into `main` when done

## Deployment

Railway auto-deploys on every push to `main`.

- Production URL: `https://campusmock-production.up.railway.app`
- Health check: `https://campusmock-production.up.railway.app/health`
- To check logs: Railway dashboard → your service → Deployments → click latest build

## Database

Supabase project: `<your-supabase-url>`  
Request access from the project owner.  
Tables: `users`, `requests`, `tokens`