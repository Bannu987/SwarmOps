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

import hashlib

def normalize_url(url: Optional[str]) -> str:
    """Normalize URL by lowering hostname, stripping trailing slashes, and removing common fragments."""
    if not url:
        return ""
    url = url.strip().lower()
    if url.endswith("/"):
        url = url[:-1]
    return url


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

        project_id = project.get("id")

        if not force and not self.should_run(user_id, project):
            logger.info(f"[{self.name}] skipping for {user_id} (too soon)")
            return 0

        # Record scan start
        scan_id = None
        try:
            scan_record = admin.table("scan_history").insert({
                "user_id": user_id,
                "project_id": project_id,
                "scanner_name": self.name,
                "status": "running",
            }).execute()
            scan_id = scan_record.data[0]["id"] if scan_record.data else None
        except Exception as e:
            logger.warning(f"Failed to record scan start in scan_history: {e}")

        # Also insert into scan_runs if table exists
        scan_run_id = None
        try:
            scan_run_record = admin.table("scan_runs").insert({
                "user_id": user_id,
                "project_id": project_id,
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            scan_run_id = scan_run_record.data[0]["id"] if scan_run_record.data else None
        except Exception as e:
            logger.info(f"scan_runs table not migrated yet: {e}")

        start = time.time()
        signals_created = 0
        error_msg = None
        status = "success"
        detected_fingerprints = []
        detected_titles = []

        try:
            signals = self.scan(user_id, project)

            # Insert or update active signals
            for signal in signals:
                # Add default signal key into raw_data for registry mapping
                if "signal_key" not in signal.raw_data:
                    # e.g. if we have a title match, or use signal_type
                    from .scoring import map_signal_to_registry_key
                    reg_key = map_signal_to_registry_key(signal.title, signal.signal_type)
                    if reg_key:
                        signal.raw_data["signal_key"] = reg_key

                fingerprint = self._persist_signal(user_id, project_id, signal, scan_run_id)
                if fingerprint:
                    detected_fingerprints.append(fingerprint)
                detected_titles.append(signal.title)
                signals_created += 1

            # Resolve signals that were NOT detected in the current run
            self._resolve_undetected_signals(user_id, project_id, detected_fingerprints, detected_titles)

            if signals_created == 0:
                status = "no_change"

            logger.info(f"[{self.name}] created/updated {signals_created} signals for {user_id}")

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

        # Update scan_runs if table exists
        if scan_run_id:
            try:
                admin.table("scan_runs").update({
                    "status": "success" if status in ["success", "no_change"] else "failed",
                    "total_pages_scanned": 1, # Homepage
                    "total_signals_detected": signals_created,
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "error_message": error_msg
                }).eq("id", scan_run_id).execute()
            except Exception as e:
                logger.warning(f"Failed to update scan_runs: {e}")

        # Recalculate and update the overall and category health scores
        if project_id:
            try:
                from .scoring import recalculate_project_health
                recalculate_project_health(project_id, user_id)
            except Exception as e:
                logger.warning(f"Failed to recalculate project health: {e}")

        return signals_created

    def _persist_signal(self, user_id: str, project_id: Optional[str], signal: Signal, scan_run_id: Optional[str] = None) -> Optional[str]:
        """Save a signal to Supabase with robust active signal deduplication and fingerprinting."""
        admin = get_admin_client()
        if not admin:
            return None

        from datetime import timedelta
        expires_at = None
        if signal.expires_in_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=signal.expires_in_hours)

        # Calculate deterministic fingerprint: md5(project_id:normalized_url:signal_type_or_key)
        normalized_url = normalize_url(signal.source_detail or project_id or "")
        # Use specific signal key inside raw_data if available to make it precise
        sig_key = signal.raw_data.get("signal_key", signal.title)
        raw_fp = f"{project_id or 'no_project'}:{normalized_url}:{sig_key}"
        fingerprint = hashlib.md5(raw_fp.encode("utf-8")).hexdigest()

        # Resilient duplicate active signal check
        existing_id = None
        existing_occurrence_count = 1
        
        # 1. Try fingerprint lookup first
        try:
            if project_id:
                existing = admin.table("signals") \
                    .select("id, occurrence_count") \
                    .eq("project_id", project_id) \
                    .eq("fingerprint", fingerprint) \
                    .eq("status", "active") \
                    .execute()
                
                if existing.data:
                    existing_id = existing.data[0]["id"]
                    existing_occurrence_count = existing.data[0].get("occurrence_count") or 1
        except Exception as fp_err:
            logger.info(f"[signals.base] Fingerprint search failed (column may not exist yet, falling back to title lookup): {fp_err}")

        # 2. Fall back to title + project_id lookup if fingerprint lookup didn't find anything
        if not existing_id and project_id:
            try:
                existing = admin.table("signals") \
                    .select("id") \
                    .eq("project_id", project_id) \
                    .eq("title", signal.title) \
                    .eq("status", "active") \
                    .execute()
                if existing.data:
                    existing_id = existing.data[0]["id"]
            except Exception as title_err:
                logger.warning(f"[signals.base] Title fallback search failed: {title_err}")

        # Update in-place if duplicate exists
        if existing_id:
            logger.info(f"[signals.base] Deduplication matched active signal '{signal.title}' (ID: {existing_id}). Updating...")
            update_data = {
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "description": signal.description,
                "severity": signal.severity,
                "evidence": signal.evidence,
                "raw_data": signal.raw_data,
                "expires_at": expires_at.isoformat() if expires_at else None,
            }
            
            # Conditionally add fingerprint, occurrence_count, and last_seen_at
            try:
                # Test updating fingerprint and occurrence_count
                temp_data = {
                    **update_data,
                    "fingerprint": fingerprint,
                    "occurrence_count": existing_occurrence_count + 1,
                    "last_seen_at": datetime.now(timezone.utc).isoformat()
                }
                admin.table("signals").update(temp_data).eq("id", existing_id).execute()
            except Exception:
                # If update with new columns failed, fall back to basic update
                try:
                    admin.table("signals").update(update_data).eq("id", existing_id).execute()
                except Exception as update_err:
                    logger.warning(f"Fallback update failed: {update_err}")

            # Insert signal occurrence & evidence if scan_run_id and tables exist
            self._insert_occurrence_and_evidence(admin, existing_id, scan_run_id, signal)
            return fingerprint

        # Insert new signal
        insert_data = {
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
        }

        new_sig_id = None
        try:
            # Try inserting with fingerprint and tracking columns
            temp_data = {
                **insert_data,
                "fingerprint": fingerprint,
                "occurrence_count": 1,
                "last_seen_at": datetime.now(timezone.utc).isoformat()
            }
            res = admin.table("signals").insert(temp_data).execute()
            new_sig_id = res.data[0]["id"] if res.data else None
        except Exception:
            # Fall back to standard columns insert
            try:
                res = admin.table("signals").insert(insert_data).execute()
                new_sig_id = res.data[0]["id"] if res.data else None
            except Exception as ins_err:
                logger.error(f"Failed to insert new signal: {ins_err}")

        if new_sig_id:
            self._insert_occurrence_and_evidence(admin, new_sig_id, scan_run_id, signal)

        return fingerprint

    def _insert_occurrence_and_evidence(self, admin, signal_id: str, scan_run_id: Optional[str], signal: Signal):
        """Insert records to signal_occurrences and signal_evidence if they exist."""
        if not scan_run_id:
            return
        
        # 1. Signal occurrences
        try:
            admin.table("signal_occurrences").insert({
                "signal_id": signal_id,
                "scan_run_id": scan_run_id,
                "page_url": signal.source_detail or ""
            }).execute()
        except Exception as e:
            logger.debug(f"signal_occurrences insert failed: {e}")

        # 2. Signal evidence
        if signal.evidence:
            for ev in signal.evidence:
                try:
                    admin.table("signal_evidence").insert({
                        "signal_id": signal_id,
                        "scan_run_id": scan_run_id,
                        "url": signal.source_detail or "",
                        "detector_source": ev.get("source", "scanner"),
                        "http_status": signal.raw_data.get("status_code"),
                        "dom_evidence": str(ev.get("claim", "")),
                        "extracted_tag": str(ev.get("value", "")),
                        "condition": "missing" if "missing" in str(ev.get("claim", "")).lower() else "present",
                        "confidence": 1.0,
                        "source_type": "crawler"
                    }).execute()
                except Exception as e:
                    logger.debug(f"signal_evidence insert failed: {e}")

    def _resolve_undetected_signals(self, user_id: str, project_id: Optional[str], detected_fps: List[str], detected_titles: List[str]):
        """Mark active signals that were no longer detected on this scan run as resolved."""
        admin = get_admin_client()
        if not admin or not project_id:
            return

        try:
            # Get all currently active signals for this project and scanner
            res = admin.table("signals") \
                .select("id, fingerprint, title") \
                .eq("project_id", project_id) \
                .eq("source_agent", self.name) \
                .eq("status", "active") \
                .execute()
            
            active_db_signals = res.data or []
        except Exception as e:
            logger.warning(f"Could not query active signals for resolution: {e}")
            return

        for db_sig in active_db_signals:
            sig_id = db_sig["id"]
            fp = db_sig.get("fingerprint")
            title = db_sig.get("title")

            # Check if this signal was NOT detected in the current run
            is_detected = False
            if fp and detected_fps:
                is_detected = (fp in detected_fps)
            else:
                is_detected = (title in detected_titles)

            if not is_detected:
                logger.info(f"[signals.base] Signal '{title}' (ID: {sig_id}) was not detected in this scan. Marking as resolved...")
                resolve_data = {
                    "status": "resolved",
                    "resolved_at": datetime.now(timezone.utc).isoformat()
                }
                
                try:
                    # Attempt to update status to 'resolved' and set resolved_at
                    admin.table("signals").update(resolve_data).eq("id", sig_id).execute()
                except Exception as e:
                    # Fallback to status = 'addressed' if 'resolved' check constraint is violated
                    logger.info(f"[signals.base] 'resolved' status check constraint failed. Falling back to 'addressed': {e}")
                    fallback_data = {
                        "status": "addressed",
                        "resolved_at": datetime.now(timezone.utc).isoformat()
                    }
                    try:
                        admin.table("signals").update(fallback_data).eq("id", sig_id).execute()
                    except Exception as fallback_err:
                        logger.warning(f"Failed to update status to addressed: {fallback_err}")


