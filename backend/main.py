"""
SwarmOps Backend v2 — FastAPI App
All routes consolidated. Auth optional (graceful fallback).
"""
import os
import re
import logging
from typing import Optional
from fastapi import FastAPI, Header, HTTPException, UploadFile, File as FastAPIFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.supabase_client import get_user_from_token, get_admin_client, is_available as supabase_available
from core.workflow_engine import detect_workflow, run_workflow, run_single_agent
from core.context import get_context
from core.memory import get_memory
from integrations.file_processor import process_file
from integrations.credentials import save_credentials, get_credentials, list_credentials, disconnect_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="SwarmOps", version="2.0.0")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "https://*.vercel.app",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return {"status": "ok", "service": "SwarmOps Backend v2"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "supabase": supabase_available(),
        "openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
    }


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
        ctx = get_context(conversation_id or "default")
        ctx.add_upload({
            "filename": result["filename"],
            "content": result["content"],
            "file_type": result["file_type"],
        })

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
