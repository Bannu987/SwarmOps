"""
Supabase Client — SwarmOps
==========================
Optional Supabase integration. If env vars are not set or the package is not
installed, all functions return graceful no-op values so the rest of the app
continues working with SQLite.

Usage:
    from supabase_client import get_supabase, get_admin_supabase, HAS_SUPABASE
"""

import os
import logging

logger = logging.getLogger(__name__)

SUPABASE_URL      = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

HAS_SUPABASE = bool(SUPABASE_URL and SUPABASE_ANON_KEY)

_public_client  = None
_admin_client   = None


def get_supabase():
    """
    Returns an authenticated Supabase client (anon key, respects RLS).
    Returns None if Supabase is not configured.
    """
    global _public_client
    if not HAS_SUPABASE:
        return None
    if _public_client is not None:
        return _public_client
    try:
        from supabase import create_client
        _public_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        logger.info("[supabase] Public client initialized")
        return _public_client
    except ImportError:
        logger.warning("[supabase] supabase package not installed — run: pip install supabase")
        return None
    except Exception as e:
        logger.error(f"[supabase] Failed to create client: {e}")
        return None


def get_admin_supabase():
    """
    Returns a Supabase client using the service role key (bypasses RLS).
    Use ONLY for server-side writes that need to bypass row-level security.
    Returns None if not configured.
    """
    global _admin_client
    if not HAS_SUPABASE or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    if _admin_client is not None:
        return _admin_client
    try:
        from supabase import create_client
        _admin_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("[supabase] Admin client initialized")
        return _admin_client
    except ImportError:
        return None
    except Exception as e:
        logger.error(f"[supabase] Failed to create admin client: {e}")
        return None


# ─────────────────────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────────────────────

def sign_up(email: str, password: str) -> dict:
    """
    Create a new user account.
    Returns {"user": {...}, "session": {...}} or {"error": "message"}
    """
    sb = get_supabase()
    if not sb:
        return {"error": "Supabase not configured"}
    try:
        response = sb.auth.sign_up({"email": email, "password": password})
        if response.user:
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "created_at": str(response.user.created_at),
                },
                "session": {
                    "access_token":  response.session.access_token  if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None,
                },
            }
        return {"error": "Sign up failed — no user returned"}
    except Exception as e:
        logger.error(f"[supabase] sign_up error: {e}")
        return {"error": str(e)}


def sign_in(email: str, password: str) -> dict:
    """
    Sign in with email + password.
    Returns {"user": {...}, "session": {...}} or {"error": "message"}
    """
    sb = get_supabase()
    if not sb:
        return {"error": "Supabase not configured"}
    try:
        response = sb.auth.sign_in_with_password({"email": email, "password": password})
        if response.user and response.session:
            return {
                "user": {
                    "id":    response.user.id,
                    "email": response.user.email,
                },
                "session": {
                    "access_token":  response.session.access_token,
                    "refresh_token": response.session.refresh_token,
                },
            }
        return {"error": "Sign in failed"}
    except Exception as e:
        logger.error(f"[supabase] sign_in error: {e}")
        return {"error": str(e)}


def sign_out(access_token: str) -> dict:
    """Sign out a user by invalidating their session token."""
    sb = get_supabase()
    if not sb:
        return {"error": "Supabase not configured"}
    try:
        sb.auth.sign_out()
        return {"success": True}
    except Exception as e:
        logger.error(f"[supabase] sign_out error: {e}")
        return {"error": str(e)}


def get_user(access_token: str) -> dict | None:
    """
    Validate an access token and return the user dict, or None if invalid.
    """
    sb = get_supabase()
    if not sb:
        return None
    try:
        sb.auth.set_session(access_token, "")
        response = sb.auth.get_user(access_token)
        if response and response.user:
            return {
                "id":    response.user.id,
                "email": response.user.email,
            }
        return None
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────
# MESSAGE PERSISTENCE (optional)
# ─────────────────────────────────────────────────────────────

def persist_message(conversation_id: str, role: str, content: str,
                    agent: str = "nexus", user_id: str | None = None) -> bool:
    """
    Save a chat message to Supabase `messages` table.
    Returns True on success, False if Supabase is unavailable.
    """
    sb = get_admin_supabase()
    if not sb:
        return False
    try:
        sb.table("messages").insert({
            "conversation_id": conversation_id,
            "role":            role,
            "content":         content,
            "agent":           agent,
            "user_id":         user_id,
        }).execute()
        return True
    except Exception as e:
        logger.warning(f"[supabase] persist_message failed: {e}")
        return False
