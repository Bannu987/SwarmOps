# SwarmOps v2 Architecture

## Backend Structure
```
backend/
├── main.py                 # FastAPI app, all routes
├── requirements.txt
├── .env.example
├── core/
│   ├── __init__.py
│   ├── model_router.py     # OpenRouter unified gateway
│   ├── supabase_client.py  # DB + auth + storage
│   ├── workflow_engine.py  # 6 workflow blueprints
│   ├── memory.py           # Composite memory system
│   ├── context.py          # Data inventory, honesty rules
│   └── prompts.py          # System prompts for all agents
├── agents/
│   ├── __init__.py
│   ├── nexus.py            # Orchestrator
│   ├── seo.py
│   ├── content.py
│   ├── analytics.py
│   ├── cro.py
│   └── aeo.py
└── integrations/
    ├── __init__.py
    ├── file_processor.py   # Universal file upload
    └── credentials.py      # Per-user API keys
```

## Frontend Structure
```
frontend/
├── package.json
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
├── components.json         # Shadcn config
├── .env.local.example
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Landing page
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   └── (app)/
│       ├── layout.tsx      # Authenticated layout
│       ├── dashboard/page.tsx
│       ├── chat/[id]/page.tsx
│       ├── projects/page.tsx
│       ├── agents/page.tsx
│       ├── approval/page.tsx
│       └── settings/page.tsx
├── components/
│   ├── ui/                 # Shadcn primitives
│   ├── sidebar/
│   ├── chat/
│   └── shared/
├── lib/
│   ├── supabase/
│   │   ├── client.ts
│   │   ├── server.ts
│   │   └── middleware.ts
│   ├── api.ts              # Backend client
│   └── utils.ts
└── types/
    └── index.ts
```

## Database Schema (Supabase)

7 tables (created via SQL editor):
- profiles, projects, conversations, messages
- user_credentials, artifacts, file_uploads

All with Row Level Security enforcing per-user isolation.

## Agent Architecture

**Single orchestrator pattern**: Nexus is the only user-facing agent.
5 specialists run as background workers. UI shows them as a unified team.

**Blueprint-first**: LLM generates text only. Python code controls
workflow routing, agent selection, and quality gates.

**Composite memory**: Each memory scored by semantic similarity +
recency decay + importance. Critical decisions persist across sessions.
