"""
Supabase client for auth, database, and storage.
Two clients: public (RLS-respecting) and admin (RLS-bypassing).
"""
import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env from backend/ directory regardless of working directory
load_dotenv(Path(__file__).parent.parent / ".env")

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_KEY") or ""

# Helper to safely mask keys for startup diagnostics
def _mask_key(key: str) -> str:
    if not key:
        return "MISSING"
    if len(key) <= 10:
        return "****"
    return f"{key[:6]}...{key[-4:]}"

# Diagnose environment variables on startup safely
logger.info("=== SUPABASE BACKEND DIAGNOSTICS ===")
logger.info(f"SUPABASE_URL: {SUPABASE_URL if SUPABASE_URL else 'MISSING'}")
logger.info(f"SUPABASE_ANON_KEY (masked): {_mask_key(SUPABASE_ANON_KEY)}")
logger.info(f"SUPABASE_SERVICE_ROLE_KEY (masked): {_mask_key(SUPABASE_SERVICE_KEY)}")

# Add startup validation warnings
if not SUPABASE_URL:
    logger.error("CRITICAL CONFIGURATION WARNING: SUPABASE_URL environment variable is missing!")
if not SUPABASE_ANON_KEY:
    logger.error("CRITICAL CONFIGURATION WARNING: SUPABASE_ANON_KEY environment variable is missing!")
if not SUPABASE_SERVICE_KEY:
    logger.error("CRITICAL CONFIGURATION WARNING: SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_SERVICE_KEY) environment variable is missing!")
logger.info("====================================")

try:
    from supabase import create_client, Client

    _public: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_ANON_KEY) if SUPABASE_URL else None
    _admin: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if (SUPABASE_URL and SUPABASE_SERVICE_KEY) else None

    AVAILABLE = _public is not None
    logger.info(f"Supabase: {'connected' if AVAILABLE else 'not configured'}")

except ImportError:
    _public = None
    _admin = None
    AVAILABLE = False
    logger.warning("supabase package not installed")


def get_client():
    return _public


def get_admin_client():
    return _admin


def is_available():
    return AVAILABLE


def get_user_from_token(token: str):
    """Validate JWT and return user object."""
    if not _public or not token:
        return None
    try:
        result = _public.auth.get_user(token)
        return result.user if result else None
    except Exception as e:
        logger.warning(f"Token validation failed: {e}")
        return None
