"""
SwarmOps Backend v2 — FastAPI App
All routes consolidated. Auth optional (graceful fallback).
"""
import asyncio
import os
import re
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, UploadFile, File as FastAPIFile, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.supabase_client import get_user_from_token, get_admin_client, is_available as supabase_available
from core.workflow_engine import detect_workflow, run_workflow, run_single_agent
from core.events import create_bus, remove_bus
from core.streaming_workflow import run_workflow_streaming, run_single_agent_streaming
from core.context import get_context
from core.memory import get_memory
from integrations.file_processor import process_file
from integrations.credentials import save_credentials, get_credentials, list_credentials, disconnect_service
from core.scanner_runner import run_all_scans, run_scans_for_user

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


async def background_scan_loop():
    """
    Background loop that runs scans every 6 hours.
    Lightweight enough to run inside the web process for v1.
    For scale, move to dedicated worker (Render Background Worker).
    """
    await asyncio.sleep(60)  # initial delay on startup
    while True:
        try:
            logger.info("[background] Starting scan loop")
            result = run_all_scans()
            logger.info(f"[background] Scan complete: {result}")
            await asyncio.sleep(6 * 60 * 60)  # 6 hours
        except asyncio.CancelledError:
            logger.info("[background] Scan loop cancelled")
            break
        except Exception as e:
            logger.error(f"[background] Scan loop error: {e}")
            await asyncio.sleep(300)  # 5 min before retry on error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Background scan loop on startup."""
    task = asyncio.create_task(background_scan_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="SwarmOps", version="2.1.0", lifespan=lifespan)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

allowed_origins = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://6a17ca7---calm-creponne-043104.netlify.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.netlify\.app$|https://.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Type"],
)


# ============================================================
# MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    project_id: Optional[str] = None


class CredentialsRequest(BaseModel):
    service: str
    credentials: dict


class ProjectRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    website_url: Optional[str] = ""


# ============================================================
# HEALTH
# ============================================================

@app.get("/")
async def root():
    return {
        "service": "SwarmOps backend",
        "status": "healthy",
        "version": "production"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "swarmops-backend",
        "supabase": supabase_available(),
        "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
    }


@app.head("/health")
async def health_head():
    return Response(status_code=200)


@app.get("/api/health")
async def api_health():
    return {
        "status": "healthy",
        "service": "swarmops-backend",
        "supabase": supabase_available(),
        "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
    }


@app.head("/api/health")
async def api_health_head():
    return Response(status_code=200)


# ============================================================
# AUTH HELPER
# ============================================================

async def get_user(authorization: Optional[str] = Header(None)):
    """Extract user from Bearer token. Returns None if invalid/missing."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "")
    return get_user_from_token(token)


# ============================================================
# CHAT
# ============================================================

@app.post("/api/chat")
async def chat(
    request: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    """Main chat endpoint. Auth optional."""
    user = await get_user(authorization)
    user_id = str(user.id) if user else None

    msg = request.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    conversation_id = request.conversation_id or "default"
    
    ctx = get_context(conversation_id)
    if user_id:
        ctx.user_id = user_id
    if request.project_id:
        ctx.project_id = request.project_id

    # Slash command handling
    if msg.startswith("/"):
        parts = msg.split(maxsplit=1)
        cmd = parts[0][1:]
        remainder = parts[1] if len(parts) > 1 else ""

        if cmd in ["seo", "content", "analytics", "cro", "aeo"]:
            result = run_single_agent(cmd, remainder or "Help me with this topic", conversation_id)
        else:
            workflow = detect_workflow(msg)
            if workflow:
                result = run_workflow(workflow, msg, conversation_id)
            else:
                result = run_single_agent("nexus", msg, conversation_id)
    else:
        # Capture URL as brand context
        url_match = re.search(r'https?://[^\s]+', msg)
        if url_match:
            ctx = get_context(conversation_id)
            ctx.update_brand({"website_url": url_match.group(0)}, url=url_match.group(0))

        workflow = detect_workflow(msg)
        if workflow:
            result = run_workflow(workflow, msg, conversation_id)
        else:
            result = run_single_agent("nexus", msg, conversation_id)

    # Persist messages if authenticated
    if user_id and supabase_available() and conversation_id != "default":
        try:
            admin = get_admin_client()
            if admin:
                admin.table("messages").insert([
                    {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "role": "user",
                        "content": msg,
                    },
                    {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "role": "assistant",
                        "content": result.get("response", ""),
                        "agents_used": result.get("agents_used", []),
                        "workflow": result.get("workflow"),
                        "latency_ms": result.get("latency_ms"),
                    },
                ]).execute()
        except Exception as e:
            logger.warning(f"Failed to persist messages: {e}")

    return {
        "response": result.get("response", ""),
        "agents_used": result.get("agents_used", []),
        "workflow": result.get("workflow"),
        "latency_ms": result.get("latency_ms", 0),
        "confidence": result.get("confidence", 0.5),
        "structured": result.get("structured"),  # for future UI
    }


# ============================================================
# CHAT — STREAMING (SSE)
# ============================================================

@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    authorization: Optional[str] = Header(None),
):
    """
    Streaming chat endpoint.
    Returns SSE stream of agent events: started, thinking, responded,
    challenged, confidence.shifted, decision.reached.
    """
    user = await get_user(authorization)
    user_id = str(user.id) if user else None

    msg = request.message.strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Empty message")

    conversation_id = request.conversation_id or "default"
    
    ctx = get_context(conversation_id)
    if user_id:
        ctx.user_id = user_id
    if request.project_id:
        ctx.project_id = request.project_id

    request_id = str(uuid.uuid4())

    bus = create_bus(request_id)

    async def event_generator():
        loop = asyncio.get_event_loop()

        def workflow_thread():
            try:
                if msg.startswith("/"):
                    parts = msg.split(maxsplit=1)
                    cmd = parts[0][1:]
                    remainder = parts[1] if len(parts) > 1 else ""

                    if cmd in ["seo", "content", "analytics", "cro", "aeo"]:
                        actual_msg = remainder.strip() or f"Help me as the {cmd.upper()} specialist."
                        result = run_single_agent_streaming(cmd, actual_msg, conversation_id, bus)
                    else:
                        workflow = detect_workflow(msg)
                        if workflow:
                            result = run_workflow_streaming(workflow, msg, conversation_id, bus)
                        else:
                            result = run_single_agent_streaming("nexus", msg, conversation_id, bus)
                else:
                    workflow = detect_workflow(msg)
                    if workflow:
                        result = run_workflow_streaming(workflow, msg, conversation_id, bus)
                    else:
                        result = run_single_agent_streaming("nexus", msg, conversation_id, bus)

                # Persist if authenticated
                if user_id and supabase_available():
                    try:
                        admin = get_admin_client()
                        if admin and conversation_id != "default":
                            admin.table("messages").insert([
                                {
                                    "conversation_id": conversation_id,
                                    "user_id": user_id,
                                    "role": "user",
                                    "content": msg,
                                },
                                {
                                    "conversation_id": conversation_id,
                                    "user_id": user_id,
                                    "role": "assistant",
                                    "content": result.get("response", ""),
                                    "agents_used": result.get("agents_used", []),
                                    "workflow": result.get("workflow"),
                                    "latency_ms": result.get("latency_ms"),
                                    "metadata": {"structured": result.get("structured")},
                                },
                            ]).execute()
                    except Exception as e:
                        logger.warning(f"Failed to persist: {e}")
            except Exception as e:
                logger.error(f"Streaming workflow error: {e}")
                bus.emit("error", {"message": str(e)})
                bus.emit("stream.end", {})

        future = loop.run_in_executor(None, workflow_thread)

        try:
            async for sse in bus.stream():
                yield sse
        finally:
            remove_bus(request_id)
            try:
                await future
            except Exception:
                pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable Render's buffering
            "Connection": "keep-alive",
        },
    )


# ============================================================
# FILE UPLOAD
# ============================================================

@app.post("/api/upload")
async def upload(
    file: UploadFile = FastAPIFile(...),
    authorization: Optional[str] = Header(None),
    conversation_id: Optional[str] = Header(None),
):
    """Universal file upload."""
    result = await process_file(file)

    if result.get("success"):
        # Add to local workflow memory context
        ctx = get_context(conversation_id or "default")
        ctx.add_upload({
            "filename": result["filename"],
            "content": result["content"],
            "file_type": result["file_type"],
        })

        # Persist upload to database if authenticated
        user = await get_user(authorization)
        user_id = str(user.id) if user else None

        if user_id and supabase_available():
            try:
                admin = get_admin_client()
                if admin:
                    storage_path = f"uploads/{user_id}/{result['filename']}"
                    
                    # Attempt storage bucket upload
                    try:
                        await file.seek(0)
                        file_bytes = await file.read()
                        admin.storage.from_("uploads").upload(
                            path=f"{user_id}/{result['filename']}",
                            file=file_bytes,
                            file_options={"content-type": file.content_type or "application/octet-stream"}
                        )
                    except Exception as storage_err:
                        logger.warning(f"Supabase Storage upload skipped/failed: {storage_err}")

                    # Validate and format conversation_id UUID
                    valid_conv_id = None
                    if conversation_id and conversation_id != "default":
                        try:
                            uuid.UUID(conversation_id)
                            valid_conv_id = conversation_id
                        except ValueError:
                            pass

                    # Write record to file_uploads table
                    admin.table("file_uploads").insert({
                        "user_id": user_id,
                        "conversation_id": valid_conv_id,
                        "filename": result["filename"],
                        "file_type": result["file_type"],
                        "file_size": result["file_size"],
                        "storage_path": storage_path,
                        "extracted_text": result["content"],
                        "metadata": result.get("metadata", {}),
                    }).execute()
            except Exception as db_err:
                logger.error(f"Failed to persist file upload to database: {db_err}")

    return result


# ============================================================
# CREDENTIALS
# ============================================================

@app.post("/api/credentials")
async def connect_service(
    request: CredentialsRequest,
    authorization: Optional[str] = Header(None),
):
    """Connect a data source."""
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    success = save_credentials(str(user.id), request.service, request.credentials)
    return {"success": success, "service": request.service}


@app.get("/api/credentials")
async def list_user_credentials(authorization: Optional[str] = Header(None)):
    """List connected services."""
    user = await get_user(authorization)
    if not user:
        return {"services": {}}

    return {"services": list_credentials(str(user.id))}


@app.delete("/api/credentials/{service}")
async def remove_credentials(
    service: str,
    authorization: Optional[str] = Header(None),
):
    """Disconnect a service."""
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    success = disconnect_service(str(user.id), service)
    return {"success": success}


# ============================================================
# CONVERSATIONS
# ============================================================

@app.get("/api/conversations")
async def list_conversations(authorization: Optional[str] = Header(None)):
    user = await get_user(authorization)
    if not user:
        return {"conversations": []}

    admin = get_admin_client()
    if not admin:
        return {"conversations": []}

    try:
        result = (
            admin.table("conversations")
            .select("*")
            .eq("user_id", str(user.id))
            .eq("archived", False)
            .order("last_message_at", desc=True)
            .limit(50)
            .execute()
        )
        return {"conversations": result.data}
    except Exception as e:
        logger.error(f"List conversations failed: {e}")
        return {"conversations": []}


@app.post("/api/conversations")
async def create_conversation(authorization: Optional[str] = Header(None)):
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    admin = get_admin_client()
    try:
        result = admin.table("conversations").insert({
            "user_id": str(user.id),
            "title": "New Conversation",
        }).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        logger.error(f"Create conversation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{conversation_id}/messages")
async def get_messages(
    conversation_id: str,
    authorization: Optional[str] = Header(None),
):
    user = await get_user(authorization)
    if not user:
        return {"messages": []}

    admin = get_admin_client()
    try:
        result = (
            admin.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .eq("user_id", str(user.id))
            .order("created_at")
            .execute()
        )
        return {"messages": result.data}
    except Exception as e:
        logger.error(f"Get messages failed: {e}")
        return {"messages": []}


# ============================================================
# PROJECTS
# ============================================================

@app.get("/api/projects")
async def list_projects(authorization: Optional[str] = Header(None)):
    user = await get_user(authorization)
    if not user:
        return {"projects": []}

    admin = get_admin_client()
    try:
        result = (
            admin.table("projects")
            .select("*")
            .eq("user_id", str(user.id))
            .eq("archived", False)
            .order("updated_at", desc=True)
            .execute()
        )
        return {"projects": result.data}
    except Exception as e:
        return {"projects": []}


@app.post("/api/projects")
async def create_project(
    request: ProjectRequest,
    authorization: Optional[str] = Header(None),
):
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")

    admin = get_admin_client()
    try:
        result = admin.table("projects").insert({
            "user_id": str(user.id),
            "name": request.name,
            "description": request.description,
            "website_url": request.website_url,
        }).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# SIGNALS
# ============================================================

@app.get("/api/signals")
async def list_signals(
    project_id: Optional[str] = None,
    status: str = "active",
    limit: int = 50,
    authorization: Optional[str] = Header(None),
):
    """List signals for the current user."""
    user = await get_user(authorization)
    if not user:
        return {"signals": []}

    admin = get_admin_client()
    if not admin:
        return {"signals": []}

    try:
        query = admin.table("signals") \
            .select("*") \
            .eq("user_id", str(user.id)) \
            .order("detected_at", desc=True) \
            .limit(limit)

        if project_id:
            query = query.eq("project_id", project_id)
        if status != "all":
            query = query.eq("status", status)

        result = query.execute()
        return {"signals": result.data or []}
    except Exception as e:
        logger.error(f"List signals failed: {e}")
        return {"signals": []}


@app.patch("/api/signals/{signal_id}")
async def update_signal(
    signal_id: str,
    request: dict,
    authorization: Optional[str] = Header(None),
):
    """Mark signal as seen / addressed / dismissed."""
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401)

    admin = get_admin_client()
    if not admin:
        raise HTTPException(status_code=500)

    updates = {}
    if "seen" in request:
        updates["seen"] = bool(request["seen"])
    if "status" in request and request["status"] in ["active", "addressed", "dismissed"]:
        updates["status"] = request["status"]

    try:
        admin.table("signals") \
            .update(updates) \
            .eq("id", signal_id) \
            .eq("user_id", str(user.id)) \
            .execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# OPPORTUNITIES
# ============================================================

@app.get("/api/opportunities")
async def list_opportunities(
    project_id: Optional[str] = None,
    status: str = "active",
    limit: int = 50,
    authorization: Optional[str] = Header(None),
):
    """List opportunities ranked by RICE score."""
    user = await get_user(authorization)
    if not user:
        return {"opportunities": []}

    admin = get_admin_client()
    if not admin:
        return {"opportunities": []}

    try:
        query = admin.table("opportunities") \
            .select("*") \
            .eq("user_id", str(user.id)) \
            .order("rice_score", desc=True) \
            .limit(limit)

        if project_id:
            query = query.eq("project_id", project_id)
        if status != "all":
            query = query.eq("status", status)

        result = query.execute()
        return {"opportunities": result.data or []}
    except Exception as e:
        logger.error(f"List opportunities failed: {e}")
        return {"opportunities": []}


@app.patch("/api/opportunities/{opportunity_id}")
async def update_opportunity(
    opportunity_id: str,
    request: dict,
    authorization: Optional[str] = Header(None),
):
    """Mark opportunity as in_progress / completed / dismissed."""
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401)

    admin = get_admin_client()

    updates = {}
    if "status" in request and request["status"] in ["active", "in_progress", "completed", "dismissed"]:
        updates["status"] = request["status"]
    if "user_action" in request:
        updates["user_action"] = request["user_action"][:500]

    try:
        admin.table("opportunities") \
            .update(updates) \
            .eq("id", opportunity_id) \
            .eq("user_id", str(user.id)) \
            .execute()
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# SCAN TRIGGERS
# ============================================================

@app.post("/api/scan")
async def trigger_scan(
    request: dict = {},
    authorization: Optional[str] = Header(None),
):
    """
    Trigger an immediate scan for the current user.
    Used when user adds website URL or wants to refresh.
    """
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401)

    project_id = request.get("project_id") if request else None
    force = request.get("force", True) if request else True
    result = run_scans_for_user(str(user.id), project_id, force=force)
    return result


@app.post("/api/scan/all")
async def trigger_all_scans(authorization: Optional[str] = Header(None)):
    """
    Run scans for ALL users. Called by cron job (e.g. Render cron).
    Protected by CRON_SECRET env var if set.
    """
    cron_secret = os.environ.get("CRON_SECRET")
    if cron_secret:
        provided = authorization.replace("Bearer ", "") if authorization else ""
        if provided != cron_secret:
            raise HTTPException(status_code=403)

    result = run_all_scans()
    return result


# ============================================================
# PERSISTENT MEMORIES AND STRATEGY BRIEFS
# ============================================================

from typing import List
from core.memory import create_project_memory, list_project_memories, delete_project_memory

class MemoryCreateRequest(BaseModel):
    memory_type: str
    title: str
    summary: str
    source: Optional[str] = "user"
    tags: Optional[List[str]] = []

class BriefGenerateRequest(BaseModel):
    user_directive: Optional[str] = ""

@app.get("/api/projects/{project_id}/memories")
async def get_project_memories_endpoint(
    project_id: str,
    authorization: Optional[str] = Header(None)
):
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    memories = list_project_memories(project_id)
    return {"memories": memories}

@app.post("/api/projects/{project_id}/memories")
async def create_project_memory_endpoint(
    project_id: str,
    request: MemoryCreateRequest,
    authorization: Optional[str] = Header(None)
):
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    res = create_project_memory(
        user_id=str(user.id),
        project_id=project_id,
        memory_type=request.memory_type,
        title=request.title,
        summary=request.summary,
        source=request.source,
        confidence=0.9,
        tags=request.tags
    )
    return res

@app.delete("/api/memories/{memory_id}")
async def delete_project_memory_endpoint(
    memory_id: str,
    authorization: Optional[str] = Header(None)
):
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    success = delete_project_memory(memory_id)
    return {"success": success}

# ============================================================
# STRATEGY BRIEFS GENERATION
# ============================================================

def generate_campaign_strategy_brief(project: dict, memories: list, opportunities: list, signals: list, user_directive: str = "") -> str:
    project_text = f"Project Name: {project.get('name')}\nWebsite: {project.get('website_url')}\nDescription: {project.get('description', '')}"
    
    memories_text = "No prior strategic memories stored yet."
    if memories:
        m_lines = []
        for m in memories:
            m_lines.append(f"- [{m.get('memory_type').upper()}]: {m.get('title')} -> {m.get('summary')}")
        memories_text = "\n".join(m_lines)
        
    opps_text = "No active opportunity signals found."
    if opportunities:
        o_lines = []
        for o in opportunities[:4]:
            o_lines.append(f"- Opportunity: {o.get('title')} (RICE: {o.get('rice_score')}) -> recommended: {o.get('recommended_action')}")
        opps_text = "\n".join(o_lines)
        
    sigs_text = "No active warning signals."
    if signals:
        s_lines = []
        for s in signals[:4]:
            s_lines.append(f"- Signal [{s.get('severity').upper()}]: {s.get('title')} -> {s.get('description')}")
        sigs_text = "\n".join(s_lines)

    prompt = f"""You are the boardroom Chief Marketing Strategist (Nexus) at SwarmOps.
Your task is to compile a highly professional, client-ready, and execution-ready Campaign Strategy Brief.

=== BRAND & CONTEXT ===
{project_text}

=== PERSISTENT STRATEGIC MEMORY ===
{memories_text}

=== ACTIVE OPPORTUNITIES (RICE RANKED) ===
{opps_text}

=== DETECTED AUDIT SIGNALS ===
{sigs_text}

=== USER DIRECTIVE / REQUESTED FOCUS ===
{user_directive or "Generate a comprehensive growth campaign brief."}

You MUST produce a comprehensive Strategy Brief in clean, highly structured Markdown. Avoid introductory conversational fluff (e.g. "Sure, here is your brief").

Your brief MUST contain these exact sections:
# STRATEGY BRIEF: [Strategic Campaign Name]

## 1. Executive Summary
## 2. ICP / Target Audience
## 3. Current Signals & Opportunities (crawled telemetry)
## 4. Proposed Campaign Strategy & positioning angle
## 5. Multi-Channel Execution Plan (SEO, Content, Creative Hooks, PPC, AEO)
## 6. Landing Page & CRO recommendations (MECLABS seq)
## 7. Lifecycle Drip & Retention flows (abandoned cart, reactivation)
## 8. North Star KPIs & Measurement Matrix
## 9. RICE-Ranked Experiment Roadmap
## 10. Next 7-Day Action Plan

Make every recommendation hyper-specific (which keyword, which segment, which trigger, which ad hook) and completely action-ready. Let's make it brilliant!"""

    try:
        response = call_model(
            prompt=prompt,
            agent_id="nexus",
            system="Always output professional marketing briefs in clean markdown only.",
            max_tokens=3000,
            temperature=0.7
        )
        return response
    except Exception as e:
        logger.error(f"Failed to generate strategy brief: {e}")
        return f"# Strategy Brief Generation Failed\n\nError: {e}"

@app.post("/api/projects/{project_id}/briefs")
async def generate_strategy_brief_endpoint(
    project_id: str,
    request: BriefGenerateRequest,
    authorization: Optional[str] = Header(None)
):
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    admin = get_admin_client()
    if not admin:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        # 1. Fetch project
        proj_res = admin.table("projects").select("*").eq("id", project_id).execute()
        if not proj_res.data:
            raise HTTPException(status_code=404, detail="Project not found")
        project = proj_res.data[0]
        
        # 2. Fetch data context
        memories = list_project_memories(project_id)
        
        opps_res = admin.table("opportunities").select("*").eq("project_id", project_id).eq("status", "active").execute()
        opportunities = opps_res.data or []
        
        sigs_res = admin.table("signals").select("*").eq("project_id", project_id).eq("status", "active").execute()
        signals = sigs_res.data or []
        
        # 3. Call generator
        markdown_content = generate_campaign_strategy_brief(
            project=project,
            memories=memories,
            opportunities=opportunities,
            signals=signals,
            user_directive=request.user_directive
        )
        
        # Extract title from first line
        title = "Strategic Campaign Brief"
        for line in markdown_content.split("\n"):
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                break
                
        # 4. Save to artifacts table
        artifact_res = admin.table("artifacts").insert({
            "user_id": str(user.id),
            "project_id": project_id,
            "artifact_type": "strategy_brief",
            "title": title,
            "content": {
                "markdown": markdown_content,
                "user_directive": request.user_directive
            },
            "status": "pending"
        }).execute()
        
        return artifact_res.data[0] if artifact_res.data else {}
        
    except Exception as e:
        logger.error(f"Strategy brief generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/projects/{project_id}/briefs")
async def list_strategy_briefs_endpoint(
    project_id: str,
    authorization: Optional[str] = Header(None)
):
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    admin = get_admin_client()
    if not admin:
        return {"briefs": []}
        
    try:
        res = admin.table("artifacts") \
            .select("*") \
            .eq("project_id", project_id) \
            .eq("artifact_type", "strategy_brief") \
            .order("created_at", desc=True) \
            .execute()
        return {"briefs": res.data or []}
    except Exception as e:
        logger.error(f"Failed to list briefs: {e}")
        return {"briefs": []}

@app.get("/api/briefs/{brief_id}")
async def get_strategy_brief_endpoint(
    brief_id: str,
    authorization: Optional[str] = Header(None)
):
    user = await get_user(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
        
    admin = get_admin_client()
    if not admin:
        raise HTTPException(status_code=500, detail="Database not configured")
        
    try:
        res = admin.table("artifacts").select("*").eq("id", brief_id).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Brief not found")
        return res.data[0]
    except Exception as e:
        logger.error(f"Failed to fetch brief: {e}")
        raise HTTPException(status_code=500, detail=str(e))

