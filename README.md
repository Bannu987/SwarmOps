# SwarmOps — AI-Powered Marketing OS

> An autonomous multi-agent marketing platform that acts as your full CMO team. Built with 11 specialized AI agents that collaborate, learn, and execute marketing strategy end-to-end.

**[Live Demo →](https://frontend-liart-nine-36.vercel.app/)**

---

## What It Does

SwarmOps replaces an entire marketing team with a coordinated swarm of AI agents. You describe your business — it analyzes your brand, researches competitors, generates strategy, and recommends concrete actions across SEO, content, ads, CRM, analytics, and more.

The agents share memory, learn your preferences over time, and get smarter with every interaction.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · SQLite (WAL) |
| Frontend | React · Deployed on Vercel |
| AI | Claude (Anthropic) via multi-agent orchestration |
| Deployment | Railway (API) · Vercel (UI) |
| Data | SQLite with thread-safe WAL mode · persistent agent memory |

---

## 11 Specialized Agents

| Agent | Role |
|---|---|
| **Nexus** | CMO orchestrator — routes queries, synthesizes multi-agent output |
| **SEO** | Keyword strategy, on-page optimization, technical SEO |
| **Content** | Blog posts, copy, content calendar, tone-of-voice consistency |
| **PPC** | Paid ad strategy, budget allocation, bid recommendations |
| **Analytics** | Data interpretation, KPI tracking, performance insights |
| **CRM** | Lead scoring, customer segmentation, lifecycle strategy |
| **SMM** | Social media strategy, posting schedules, platform optimization |
| **Brand** | Brand DNA extraction, positioning, messaging framework |
| **CRO** | Conversion rate optimization, funnel analysis, A/B test ideas |
| **Web UX** | UX audits, user journey mapping, design recommendations |
| **Research** | Deep market research, trend analysis, competitor intelligence |

---

## Key Features

- **Brand DNA Engine** — Scrapes your website and uses LLM extraction to build a brand profile that's injected into every agent prompt automatically
- **Competitive Intelligence** — Adds competitors by URL, runs 5 parallel analyses (website, SEO, content, social, ads), detects changes over time, generates battle cards
- **Learning Engine** — Tracks your interaction patterns and topic preferences; agents adapt their recommendations over time
- **Revenue Tracker** — Logs every agent recommendation with predicted business impact
- **Persistent Agent Memory** — All agents share a SQLite-backed memory store across sessions
- **Smart Routing** — Nexus automatically dispatches queries to the right specialist agent(s)

---

## Architecture

```
User Query
    │
    ▼
Nexus (CMO Orchestrator)
    │
    ├── Brand DNA Context (auto-injected)
    ├── Competitive Intel Context (auto-injected)
    ├── User Preference Context (learning engine)
    │
    ▼
Specialist Agent(s)
    │
    ├── SEO / Content / PPC / Analytics / CRM
    ├── SMM / Brand / CRO / Web UX / Research
    │
    ▼
Structured Response + Revenue Impact Estimate
    │
    ▼
Learning Engine (records preference signals)
```

**Backend:** FastAPI app (`backend/main.py`) with 14 SQLite tables, thread-local connections in WAL mode
**Frontend:** React single-page app with three-panel AI dashboard UI
**Deployment:** Procfile-based Railway deployment; Vercel for frontend

---

## Running Locally

```bash
# Clone and set up backend
git clone https://github.com/Bannu987/MarketingOS2.0
cd swarmops
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY=your_key_here

# Start the API server
cd backend && uvicorn main:app --reload --port 8000

# In another terminal, start the frontend
cd frontend
npm install
npm start
```

The app runs at `http://localhost:3000` with the API at `http://localhost:8000`.

---

## Project Structure

```
swarmops/
├── backend/
│   └── main.py              # FastAPI app + all endpoints
├── nexus.py                 # CMO orchestrator (smart routing)
├── *_agent.py               # 11 specialist agents
├── brand_dna.py             # Website scraper + brand extraction
├── competitive_intel.py     # Competitor tracking + battle cards
├── learning_engine.py       # User preference learning
├── revenue_tracker.py       # Business impact logging
├── memory_store.py          # Persistent SQLite agent memory
├── db.py                    # Centralized DB connection (WAL)
└── frontend/
    └── src/                 # React UI
```

---

## License

MIT
