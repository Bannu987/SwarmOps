# SwarmOps

The Claude of marketing. A multi-agent AI marketing platform where 6 specialist agents collaborate under a strategic orchestrator.

## Architecture

- **Frontend**: Next.js 14 + Tailwind + Shadcn/ui + Supabase Auth
- **Backend**: FastAPI + OpenRouter + Supabase
- **Agents**: Nexus (orchestrator) + SEO, Content, Analytics, CRO, AEO

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Deployment

- Backend: Render (free tier)
- Frontend: Vercel (free tier)
- Database: Supabase (free tier)

## Status

v2.0 — Rebuilt from scratch with hard-won lessons from v1.
