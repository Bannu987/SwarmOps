"""Per-user API credentials manager (uses Supabase)."""
import logging
from typing import Dict, Optional
from core.supabase_client import get_admin_client

logger = logging.getLogger(__name__)


def save_credentials(user_id: str, service: str, credentials: Dict) -> bool:
    """Save user credentials for a service."""
    admin = get_admin_client()
    if not admin:
        return False

    try:
        admin.table("user_credentials").upsert({
            "user_id": user_id,
            "service": service,
            "credentials": credentials,
            "status": "active",
        }, on_conflict="user_id,service").execute()
        return True
    except Exception as e:
        logger.error(f"Save credentials failed: {e}")
        return False


def get_credentials(user_id: str, service: str) -> Optional[Dict]:
    """Get user credentials for a service."""
    admin = get_admin_client()
    if not admin:
        return None

    try:
        result = (
            admin.table("user_credentials")
            .select("credentials")
            .eq("user_id", user_id)
            .eq("service", service)
            .eq("status", "active")
            .execute()
        )
        if result.data and len(result.data) > 0:
            return result.data[0]["credentials"]
    except Exception as e:
        logger.error(f"Get credentials failed: {e}")
    return None


def list_credentials(user_id: str) -> Dict:
    """List all services with their connection status."""
    admin = get_admin_client()
    if not admin:
        return {}

    try:
        result = (
            admin.table("user_credentials")
            .select("service, status, last_used_at")
            .eq("user_id", user_id)
            .execute()
        )
        return {row["service"]: row for row in result.data}
    except Exception as e:
        logger.error(f"List credentials failed: {e}")
        return {}


def disconnect_service(user_id: str, service: str) -> bool:
    """Remove credentials for a service."""
    admin = get_admin_client()
    if not admin:
        return False

    try:
        admin.table("user_credentials").delete().eq("user_id", user_id).eq("service", service).execute()
        return True
    except Exception as e:
        logger.error(f"Disconnect failed: {e}")
        return False
