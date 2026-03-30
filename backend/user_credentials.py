"""
User Credentials Manager — SwarmOps
Stores API keys per-session in SQLite.
Falls back to environment variables if no user-supplied credentials.
"""
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Env-var fallback mapping: service → {field: ENV_VAR_NAME}
ENV_FALLBACK = {
    "ga4": {
        "property_id":       "GA4_PROPERTY_ID",
        "credentials_json":  "GOOGLE_APPLICATION_CREDENTIALS",
    },
    "gsc": {
        "site_url":          "GSC_SITE_URL",
        "credentials_json":  "GOOGLE_APPLICATION_CREDENTIALS",
    },
    "hubspot": {
        "api_key":           "HUBSPOT_API_KEY",
    },
    "google_ads": {
        "developer_token":   "GOOGLE_ADS_DEVELOPER_TOKEN",
        "customer_id":       "GOOGLE_ADS_CUSTOMER_ID",
    },
}

VALID_SERVICES = list(ENV_FALLBACK.keys())


class UserCredentials:
    """Manage user API credentials in SQLite with env-var fallback."""

    def __init__(self):
        self._init_db()

    def _init_db(self):
        try:
            from db import get_connection
            with get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS user_credentials (
                        service      TEXT PRIMARY KEY,
                        credentials  TEXT NOT NULL,
                        connected_at TEXT NOT NULL,
                        status       TEXT DEFAULT 'active'
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"[credentials] DB init failed: {e}")

    # ── Write ──────────────────────────────────────────────────────────────

    def save(self, service: str, credentials: dict) -> bool:
        """Save or replace credentials for a service."""
        if service not in VALID_SERVICES:
            return False
        try:
            from db import get_connection
            with get_connection() as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO user_credentials
                       (service, credentials, connected_at, status)
                       VALUES (?, ?, ?, 'active')""",
                    (service, json.dumps(credentials), datetime.utcnow().isoformat()),
                )
                conn.commit()
            logger.info(f"[credentials] Saved {service}")
            return True
        except Exception as e:
            logger.error(f"[credentials] Save {service} failed: {e}")
            return False

    def disconnect(self, service: str) -> bool:
        """Delete stored credentials for a service."""
        try:
            from db import get_connection
            with get_connection() as conn:
                conn.execute("DELETE FROM user_credentials WHERE service = ?", (service,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[credentials] Disconnect {service} failed: {e}")
            return False

    # ── Read ───────────────────────────────────────────────────────────────

    def get(self, service: str) -> dict | None:
        """
        Return credentials dict for a service.
        Checks DB first; falls back to env vars.
        """
        # 1. DB
        try:
            from db import get_connection
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT credentials FROM user_credentials WHERE service=? AND status='active'",
                    (service,),
                ).fetchone()
            if row:
                return json.loads(row[0])
        except Exception as e:
            logger.error(f"[credentials] Read {service} failed: {e}")

        # 2. Env vars
        mapping = ENV_FALLBACK.get(service, {})
        creds = {field: os.environ.get(env_var, "") for field, env_var in mapping.items()}
        if any(v for v in creds.values()):
            return creds

        return None

    def is_connected(self, service: str) -> bool:
        """True if the service has at least one credential value."""
        creds = self.get(service)
        return bool(creds and any(v for v in creds.values()))

    def _has_db_creds(self, service: str) -> bool:
        """True if credentials exist in DB (not just env vars)."""
        try:
            from db import get_connection
            with get_connection() as conn:
                row = conn.execute(
                    "SELECT 1 FROM user_credentials WHERE service=? AND status='active'",
                    (service,),
                ).fetchone()
            return row is not None
        except Exception:
            return False

    def all_status(self) -> dict:
        """Return connection status for every service."""
        result = {}
        for service in VALID_SERVICES:
            connected = self.is_connected(service)
            source = "none"
            if connected:
                source = "database" if self._has_db_creds(service) else "env_var"
            result[service] = {"connected": connected, "source": source}
        return result


# ── Singleton ──────────────────────────────────────────────────────────────
_instance: UserCredentials | None = None

def get_credential_manager() -> UserCredentials:
    global _instance
    if _instance is None:
        _instance = UserCredentials()
    return _instance
