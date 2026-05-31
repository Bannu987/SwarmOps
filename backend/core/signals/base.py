"""
Base scanner. Each detector subclasses this and implements scan().
Scanners are pluggable — add new ones by creating new files.
"""
import logging
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime, timezone

from ..supabase_client import get_admin_client

logger = logging.getLogger(__name__)


class Signal:
    """A single detected change."""
    def __init__(
        self,
        signal_type: str,
        title: str,
        description: str = "",
        severity: str = "medium",
        category: str = "market",
        source_agent: str = "system",
        source_detail: Optional[str] = None,
        evidence: Optional[List[Dict]] = None,
        raw_data: Optional[Dict] = None,
        expires_in_hours: Optional[int] = 168,  # 1 week default
    ):
        self.signal_type = signal_type
        self.title = title
        self.description = description
        self.severity = severity
        self.category = category
        self.source_agent = source_agent
        self.source_detail = source_detail
        self.evidence = evidence or []
        self.raw_data = raw_data or {}
        self.expires_in_hours = expires_in_hours


class BaseScanner(ABC):
    """
    Base class for all signal detectors.

    Subclasses must implement:
    - name: scanner identifier
    - interval_hours: how often this scanner should run
    - scan(user_id, project): return list of Signal objects
    """

    name: str = "base"
    interval_hours: int = 24
    requires_url: bool = False
    requires_integration: Optional[str] = None  # e.g. 'ga4', 'gsc', None

    @abstractmethod
    def scan(self, user_id: str, project: Dict) -> List[Signal]:
        """Run the scanner. Return list of detected signals."""
        pass

    def should_run(self, user_id: str, project: Dict) -> bool:
        """Check if this scanner should run now (interval + prerequisites)."""
        if self.requires_url and not project.get("website_url"):
            return False

        admin = get_admin_client()
        if not admin:
            return False

        try:
            result = admin.table("scan_history") \
                .select("started_at") \
                .eq("user_id", user_id) \
                .eq("scanner_name", self.name) \
                .order("started_at", desc=True) \
                .limit(1) \
                .execute()

            if not result.data:
                return True  # never run before

            last_run = result.data[0]["started_at"]
            last_dt = datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            hours_since = (now - last_dt).total_seconds() / 3600

            return hours_since >= self.interval_hours
        except Exception as e:
            logger.warning(f"[{self.name}] should_run check failed: {e}")
            return False

    def run_for_user(self, user_id: str, project: Dict, force: bool = False) -> int:
        """
        Run scanner and persist signals. Returns number of signals created.
        Wraps scan() with timing + history tracking.
        """
        admin = get_admin_client()
        if not admin:
            return 0

        if not force and not self.should_run(user_id, project):
            logger.info(f"[{self.name}] skipping for {user_id} (too soon)")
            return 0

        # Record scan start
        scan_record = admin.table("scan_history").insert({
            "user_id": user_id,
            "project_id": project.get("id"),
            "scanner_name": self.name,
            "status": "running",
        }).execute()
        scan_id = scan_record.data[0]["id"] if scan_record.data else None

        start = time.time()
        signals_created = 0
        error_msg = None
        status = "success"

        try:
            signals = self.scan(user_id, project)

            for signal in signals:
                self._persist_signal(user_id, project.get("id"), signal)
                signals_created += 1

            if signals_created == 0:
                status = "no_change"

            logger.info(f"[{self.name}] created {signals_created} signals for {user_id}")

        except Exception as e:
            logger.error(f"[{self.name}] failed: {e}")
            status = "failed"
            error_msg = str(e)[:500]

        # Update scan history
        if scan_id:
            try:
                admin.table("scan_history").update({
                    "status": status,
                    "signals_created": signals_created,
                    "duration_ms": int((time.time() - start) * 1000),
                    "error_message": error_msg,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                }).eq("id", scan_id).execute()
            except Exception as e:
                logger.warning(f"Failed to update scan history: {e}")

        return signals_created

    def _persist_signal(self, user_id: str, project_id: Optional[str], signal: Signal):
        """Save a signal to Supabase."""
        admin = get_admin_client()
        if not admin:
            return

        from datetime import timedelta
        expires_at = None
        if signal.expires_in_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=signal.expires_in_hours)

        admin.table("signals").insert({
            "user_id": user_id,
            "project_id": project_id,
            "signal_type": signal.signal_type,
            "title": signal.title,
            "description": signal.description,
            "severity": signal.severity,
            "category": signal.category,
            "source_agent": signal.source_agent,
            "source_detail": signal.source_detail,
            "evidence": signal.evidence,
            "raw_data": signal.raw_data,
            "expires_at": expires_at.isoformat() if expires_at else None,
        }).execute()
