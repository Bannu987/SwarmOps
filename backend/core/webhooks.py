import os
import json
import hmac
import hashlib
import logging
import threading
import httpx

logger = logging.getLogger(__name__)

def trigger_n8n_webhook(action_plan: dict):
    """
    Triggers the n8n webhook for SwarmOps action plan events.
    Runs asynchronously in a background thread to prevent blocking requests.
    """
    webhook_url = os.environ.get("N8N_WEBHOOK_URL")
    if not webhook_url:
        logger.info("[WEBHOOK] N8N_WEBHOOK_URL is not configured. Skipping webhook trigger.")
        return

    secret = os.environ.get("N8N_WEBHOOK_SECRET", "swarmops-default-secret")

    payload = {
        "action_plan_id": str(action_plan.get("id")),
        "project_id": str(action_plan.get("project_id")),
        "user_id": str(action_plan.get("user_id")),
        "signal_title": action_plan.get("title", ""),
        "category": action_plan.get("plan_type", "general_strategy"),
        "priority": action_plan.get("priority", "medium"),
        "owner": action_plan.get("owner_label") or "nexus",
        "recommended_fix": action_plan.get("objective", ""),
        "checklist": action_plan.get("tasks") or [],
        "expected_impact": action_plan.get("expected_impact", "medium"),
        "effort": action_plan.get("estimated_effort", "medium")
    }

    def worker():
        try:
            payload_bytes = json.dumps(payload).encode("utf-8")
            signature = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

            headers = {
                "Content-Type": "application/json",
                "X-SwarmOps-Signature": signature,
                "HTTP-Referer": "https://swarmops.ai",
                "X-Title": "SwarmOps"
            }

            logger.info(f"[WEBHOOK] Sending action plan trigger to n8n: {webhook_url}")
            response = httpx.post(webhook_url, data=payload_bytes, headers=headers, timeout=10.0)
            logger.info(f"[WEBHOOK] n8n responded with status code: {response.status_code}")
        except Exception as e:
            logger.error(f"[WEBHOOK] Failed to send webhook to n8n: {e}")

    threading.Thread(target=worker, daemon=True).start()
