# SwarmOps Deployment Modes

This document details the configuration, run commands, and characteristics of the different environment modes available for the SwarmOps backend.

---

## A. LOCAL_DEV (Local Development)

This mode is used for daily local development and testing of agents, UI components, and integrations.

* **Backend Base URL**: `http://localhost:8000`
* **Frontend Environment Configuration**:
  ```env
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```

### Run Commands

* **Backend**:
  ```powershell
  cd backend
  # Ensure virtual environment is active
  uvicorn main:app --reload --host 127.0.0.1 --port 8000
  ```
* **Frontend**:
  ```powershell
  cd frontend
  npm run dev
  ```

### Verification Checks

* **Local Health Check**:
  * **PowerShell**:
    ```powershell
    Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    ```
  * **cURL (Bash)**:
    ```bash
    curl -i http://localhost:8000/health
    ```
* **Local SSE Stream Check**:
  * **PowerShell**:
    ```powershell
    # To run a simple streaming chat check:
    $body = @{ message = "Ping agents"; conversation_id = "test-local-sse" } | ConvertTo-Json
    Invoke-RestMethod -Uri "http://localhost:8000/api/chat/stream" -Method Post -Body $body -ContentType "application/json"
    ```
  * **cURL (Bash)**:
    ```bash
    curl -N -X POST -H "Content-Type: application/json" -d '{"message":"Ping agents","conversation_id":"test-local-sse"}' http://localhost:8000/api/chat/stream
    ```

---

## B. FALLBACK_DEMO_RENDER (Render Free Tier)

This mode is the existing deployed backend. It remains active as a backup to ensure zero downtime during the Cloud Run migration.

* **Backend Base URL**: `https://swarmops.onrender.com`
* **When to Use**: Only as a temporary fallback if the future Cloud Run backend experiences outages or during initial migration verification.
* **Why it is Fallback/Demo Only**: 
  * **Cold Starts**: Render free tier spins down the web service after 15 minutes of inactivity. The next request triggers a cold start taking 1–3 minutes, causing severe frontend timeout errors.
  * **Long Request Timeout Risk**: Render terminates requests that do not respond within 30 seconds (or limits them depending on free tier policies), which conflicts with Boardroom multi-agent reasoning loops that can take 60–120 seconds.
  * **SSE Fragility**: Render's routing layer occasionally buffers Server-Sent Events (SSE) or drops connections prematurely, causing the frontend UI spinner to run indefinitely.
  * **Slow Model-Call UX**: Reduced CPU/memory sharing under free plans affects JSON parsing and HTTP client request scheduling.

---

## C. PUBLIC_DEMO_CLOUD_RUN (Google Cloud Run)

This is the target primary deployment backend for the public demo. It resolves the limitations of Render free tier by supporting dynamic scale-to-zero, low cold-start latency, custom request timeouts, and unbuffered SSE streams.

* **Backend Base URL**: Created after deploy (e.g. `https://swarmops-backend-xxxxxx-uc.a.run.app`)
* **When to Use**: Primary backend for the public Vercel frontend.
* **Required Environment Variables**:
  * `SUPABASE_URL`
  * `SUPABASE_ANON_KEY`
  * `SUPABASE_SERVICE_ROLE_KEY`
  * `OPENROUTER_API_KEY`
  * `FRONTEND_URL` (Matches the Vercel production deployment URL for CORS)
  * Feature Flags (e.g., `ENABLE_STREAMING_BOARDROOM=True`, `ENABLE_PROJECT_MEMORY=True`, etc.)
* **Verification Gate**: Before updating the Vercel frontend `NEXT_PUBLIC_API_URL`, the Cloud Run service must pass all SSE and recovery checks.

---

## D. PROD_LATER (Paid Production Mode)

Future paid operational scale.

* **Infrastructure**: Cloud Run with a minimum instance configuration (`--min-instances 1`) or a dedicated Virtual Private Server (VPS) / Kubernetes deployment.
* **Purpose**: Prevents cold starts completely for paid enterprise workspaces.
* **Requirement Status**: Not required today (under active development and testing).
