import sys
import os
import asyncio
import logging
from unittest import mock

logging.basicConfig(level=logging.INFO)

# Append backend path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.swarm_workflow import run_swarm_signal_workflow
from core.signals.scoring import calculate_priority_score, get_priority_bucket
from core.signals.base import normalize_url

def test_normalization():
    assert normalize_url("https://example.com/") == "https://example.com"
    assert normalize_url("http://example.com/path/") == "http://example.com/path"
    print("URL Normalization test passed!")

def test_scoring():
    # priority_score = ((impact * 0.45) + (urgency * 0.25) + (confidence * 0.20) + (business_relevance * 0.10)) / max(effort, 1)
    score = calculate_priority_score(
        impact=3.0,
        urgency=2.0,
        confidence=9.5,
        business_relevance=3.0,
        effort=1.0
    )
    # Expected: ((3.0 * 0.45) + (2.0 * 0.25) + (9.5 * 0.20) + (3.0 * 0.10)) / 1.0 = (1.35 + 0.5 + 1.9 + 0.3) = 4.05
    assert score == 4.05
    assert get_priority_bucket(score) == "Medium"
    print("Priority Scoring test passed!")

def test_crawl_safety():
    # Let's verify that private IP resolver blocks private range
    import socket
    from core.signals.website_health import WebsiteHealthScanner
    scanner = WebsiteHealthScanner()
    
    # Mock project
    project_local = {"website_url": "http://127.0.0.1"}
    res = scanner.scan("test_user", project_local)
    assert res == []
    
    project_private = {"website_url": "http://192.168.1.1"}
    res = scanner.scan("test_user", project_private)
    assert res == []
    
    print("Crawl Safety Guard test passed!")

async def test_workflow():
    from core.events import EventBus
    import concurrent.futures

    clicked_signal = {
        "signal_id": "test-sig-id",
        "signal_type": "missing_robots_txt",
        "title": "No robots.txt file",
        "description": "A robots.txt file gives you control over how search engines crawl your site.",
        "detector": "seo",
        "category": "seo",
        "severity": "low",
        "url": "https://shravanpayyavula.me/",
        "evidence": "404 not found",
        "project_id": "test-project-id",
        "workspace_id": "test-project-id"
    }

    print("Running supervisor workflow streaming for No robots.txt file...")
    bus = EventBus()
    loop = asyncio.get_running_loop()
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    
    # Run in thread executor
    def run_thread():
        from unittest.mock import patch, MagicMock
        with patch("core.swarm_workflow.get_admin_client") as mock_admin:
            mock_admin.return_value = MagicMock()
            return run_swarm_signal_workflow(
                clicked_signal=clicked_signal,
                message="Analyze and address this signal: No robots.txt file",
                conversation_id="test_conv",
                bus=bus
            )
    
    future = loop.run_in_executor(executor, run_thread)
    
    events_received = []
    async for sse in bus.stream():
        events_received.append(sse)
        print(f"[TEST SSE EVENT]: {sse.strip()}")

    result = await future
    response = result["response"]
    print("\n--- WORKFLOW RESPONSE ---")
    print(response)
    print("-------------------------\n")

    # Assertions on emitted SSE events
    event_types = [e.split("\n")[0].replace("event: ", "").strip() for e in events_received if "event: " in e]
    print(f"Emitted event types: {event_types}")
    assert "workflow.started" in event_types, "Missing workflow.started event"
    assert "decision.reached" in event_types, "Missing decision.reached event"
    assert "final.answer" in event_types, "Missing final.answer event"
    assert "stream.end" in event_types, "Missing stream.end event"

    # Assertions based on requirement 8 & 14
    assert "User-agent: *" in response, "Missing user-agent rule"
    assert "Allow: /" in response, "Missing allow rule"
    assert "Sitemap: https://shravanpayyavula.me/sitemap.xml" in response, "Missing sitemap rule"
    assert "controls crawler access, not indexing" in response, "Inaccurate robots.txt explanation"
    assert "public/robots.txt" in response, "Missing public/robots.txt path recommendation"
    assert "HTTP 200" in response or "http 200" in response.lower(), "Missing HTTP 200 verification check"
    assert "crawl delay" not in response.lower() and "crawl-delay" not in response.lower(), "Crawl delay recommended by default"
    
    # Priority-language guard assertions
    assert "immediately" not in response.lower(), "Low priority signal contains 'immediately'"
    assert "urgent" not in response.lower(), "Low priority signal contains 'urgent'"
    assert "critical" not in response.lower(), "Low priority signal contains 'critical'"
    assert "ranking drops" not in response.lower(), "Low priority signal contains 'ranking drops'"
    assert "crawl budget loss" not in response.lower(), "Low priority signal contains 'crawl budget loss'"
    assert "severe" not in response.lower(), "Low priority signal contains 'severe'"
    
    # Generic placeholder assertions
    assert "Standard technical opportunity detected." not in response, "Contains generic placeholder"
    assert "Visit /robots.txt or inspect HTML head or check headers..." not in response, "Contains generic placeholder"
    assert "Implement configuration fix." not in response, "Contains generic placeholder"
    
    # Verify no rate-limiting or backup alerts
    assert "rate limit" not in response.lower()
    assert "offline" not in response.lower()
    assert "fallback" not in response.lower()
    
    # Verify no inaccurate CTR or citations claims
    assert "30%" not in response
    assert "critical for chatgpt" not in response.lower()

    # Test the follow-up handler
    print("Testing follow-up handler for create robots.txt...")
    from unittest.mock import patch, MagicMock
    with patch("core.swarm_workflow.get_admin_client") as mock_admin:
        mock_admin.return_value = MagicMock()
        follow_up_res = run_swarm_signal_workflow(
            clicked_signal=clicked_signal,
            message="create robots.txt file",
            conversation_id="test_conv"
        )
    follow_up_out = follow_up_res["response"]
    assert "public/robots.txt" in follow_up_out, "Follow-up failed to return file path"
    assert "User-agent: *" in follow_up_out, "Follow-up failed to return file contents"
    print("Follow-up handler test passed successfully!")

    print("Workflow validation test passed successfully!")

def test_webhook_trigger():
    from unittest.mock import patch
    from core.webhooks import trigger_n8n_webhook
    import os
    import time
    
    mock_plan = {
        "id": "test-plan-id",
        "project_id": "test-proj-id",
        "user_id": "test-user-id",
        "title": "Test Plan Title",
        "plan_type": "seo_growth",
        "priority": "low",
        "owner_label": "nexus",
        "objective": "Test Objective",
        "tasks": ["Task 1", "Task 2"],
        "expected_impact": "medium",
        "estimated_effort": "low"
    }
    
    # Mock N8N_WEBHOOK_URL env variable
    with patch.dict(os.environ, {"N8N_WEBHOOK_URL": "https://n8n.test.local/webhook", "N8N_WEBHOOK_SECRET": "testsecret"}):
        with patch("httpx.post") as mock_post:
            trigger_n8n_webhook(mock_plan)
            # Webhook triggers in a thread, so let's sleep a short moment
            time.sleep(0.5)
            
            assert mock_post.called, "httpx.post was not called"
            args, kwargs = mock_post.call_args
            assert args[0] == "https://n8n.test.local/webhook"
            assert "X-SwarmOps-Signature" in kwargs["headers"]
            print("Webhook trigger test passed successfully!")

def test_action_plans_api():
    from fastapi.testclient import TestClient
    from main import app
    from unittest.mock import patch, MagicMock

    client = TestClient(app)

    # Mock user object
    mock_user = MagicMock()
    mock_user.id = "test-user-id"

    with patch("main.get_user_from_token", return_value=mock_user) as mock_get_user, \
         patch("main.get_admin_client") as mock_get_admin:
         
         # Mock admin client database interactions
         mock_db = MagicMock()
         mock_get_admin.return_value = mock_db
         
         # 1. Test POST /api/action-plans/from-boardroom - Successful creation
         mock_select_res = MagicMock()
         mock_select_res.data = [] # No duplicate
         
         mock_insert_res = MagicMock()
         mock_insert_res.data = [{"id": "new-plan-id", "title": "Test Robots.txt"}]
         
         mock_table_plan = MagicMock()
         mock_table_projects = MagicMock()
         
         def mock_table(table_name):
             if table_name == "action_plans":
                 return mock_table_plan
             elif table_name == "projects":
                 return mock_table_projects
             return MagicMock()
             
         mock_db.table.side_effect = mock_table
         
         mock_table_plan.select.return_value = mock_table_plan
         mock_table_plan.eq.return_value = mock_table_plan
         mock_table_plan.insert.return_value = mock_table_plan
         
         # Mock projects query so that project ownership check succeeds
         mock_proj_res = MagicMock()
         mock_proj_res.data = [{"id": "test-project-id"}]
         mock_table_projects.select.return_value = mock_table_projects
         mock_table_projects.eq.return_value = mock_table_projects
         mock_table_projects.execute.return_value = mock_proj_res
         
         def mock_execute(*args, **kwargs):
             if mock_table_plan.insert.called:
                 return mock_insert_res
             return mock_select_res
             
         mock_table_plan.execute.side_effect = mock_execute
         
         payload = {
             "project_id": "test-project-id",
             "signal_id": "test-signal-id",
             "signal_key": "missing_robots_txt",
             "title": "Add robots.txt file",
             "priority_bucket": "Low",
             "priority_score": 1.5,
             "owner": "SEO Specialist",
             "recommended_fix": "Add robots.txt",
             "evidence": "404 not found",
             "implementation_steps": "Create file",
             "verification_steps": "Check /robots.txt",
             "checklist_items": ["Create file", "Deploy file"],
             "expected_impact": "low",
             "effort": "low"
         }
         
         resp = client.post(
             "/api/action-plans/from-boardroom",
             json=payload,
             headers={"Authorization": "Bearer test-token"}
         )
         
         assert resp.status_code == 200
         data = resp.json()
         assert data["id"] == "new-plan-id"
         print("POST /api/action-plans/from-boardroom success test passed!")
         
         # Reset mocks for duplicate check
         mock_table_plan.insert.reset_mock()
         mock_select_res.data = [{"id": "existing-plan-id"}] # Duplicate exists
         
         resp = client.post(
             "/api/action-plans/from-boardroom",
             json=payload,
             headers={"Authorization": "Bearer test-token"}
         )
         
         assert resp.status_code == 409
         print("POST /api/action-plans/from-boardroom duplicate (409) test passed!")

         # 2. Test POST /api/action-plans/{plan_id}/verify
         mock_table_plan.insert.reset_mock()
         mock_table_plan.select.reset_mock()
         mock_table_plan.eq.reset_mock()
         mock_table_plan.execute.side_effect = None
         
         mock_plan_data = {
             "id": "new-plan-id",
             "project_id": "test-project-id",
             "user_id": "test-user-id",
             "title": "Add robots.txt file",
             "signal_key": "missing_robots_txt",
             "tasks": [{"id": "task1", "title": "Create robots.txt", "status": "pending"}]
         }
         mock_project_data = {
             "website_url": "https://shravanpayyavula.me"
         }
         
         mock_select_res_plan = MagicMock()
         mock_select_res_plan.data = [mock_plan_data]
         
         mock_select_res_proj = MagicMock()
         mock_select_res_proj.data = [mock_project_data]
         
         mock_table_projects = MagicMock()
         
         def mock_table(table_name):
             if table_name == "action_plans":
                 return mock_table_plan
             elif table_name == "projects":
                 return mock_table_projects
             return MagicMock()
             
         mock_db.table.side_effect = mock_table
         
         mock_table_plan.select.return_value = mock_table_plan
         mock_table_plan.update.return_value = mock_table_plan
         mock_table_plan.eq.return_value = mock_table_plan
         mock_table_plan.execute.return_value = mock_select_res_plan
         
         mock_table_projects.select.return_value = mock_table_projects
         mock_table_projects.eq.return_value = mock_table_projects
         mock_table_projects.execute.return_value = mock_select_res_proj
         
         with patch("httpx.AsyncClient.get") as mock_http_get:
             mock_http_resp = MagicMock()
             mock_http_resp.status_code = 200
             mock_http_get.return_value = mock_http_resp
             
             resp = client.post(
                 "/api/action-plans/new-plan-id/verify",
                 headers={"Authorization": "Bearer test-token"}
             )
             
             assert resp.status_code == 200
             data = resp.json()
             assert data["success"] is True
             assert data["status"] == "verified"
             
             # Check that tasks status was updated to completed
             mock_table_plan.update.assert_called_once()
             args, kwargs = mock_table_plan.update.call_args
             assert args[0]["status"] == "verified"
             assert args[0]["tasks"][0]["status"] == "completed"
             
             print("POST /api/action-plans/{plan_id}/verify success test passed!")

def test_phase_2_5_observability():
    print("Running Phase 2.5 Observability & Feature Flags tests...")
    from fastapi.testclient import TestClient
    from main import app
    from unittest.mock import patch, MagicMock
    import os

    client = TestClient(app)

    # Mock user object
    mock_user = MagicMock()
    mock_user.id = "test-user-id"

    with patch("main.get_user_from_token", return_value=mock_user) as mock_get_user, \
         patch("main.get_admin_client") as mock_get_admin:
         
         # 1. Test ENABLE_ACTION_PLAN_CREATION feature flag = False
         with patch.dict(os.environ, {"ENABLE_ACTION_PLAN_CREATION": "false"}):
             payload = {
                 "project_id": "test-project-id",
                 "signal_id": "test-signal-id",
                 "signal_key": "missing_robots_txt",
                 "title": "Add robots.txt file",
                 "priority_bucket": "Low",
                 "priority_score": 1.5,
                 "owner": "SEO Specialist",
                 "recommended_fix": "Add robots.txt",
                 "evidence": "404 not found",
                 "implementation_steps": "Create file",
                 "verification_steps": "Check /robots.txt",
                 "checklist_items": ["Create file", "Deploy file"],
                 "expected_impact": "low",
                 "effort": "low",
                 "trace_id": "test-trace-id-123"
             }
             resp = client.post(
                 "/api/action-plans/from-boardroom",
                 json=payload,
                 headers={"Authorization": "Bearer test-token"}
             )
             assert resp.status_code == 400
             assert "disabled" in resp.json()["detail"].lower()
             print("Feature flag ENABLE_ACTION_PLAN_CREATION=false test passed!")

         # 2. Test ENABLE_AUTO_VERIFICATION feature flag = False
         with patch.dict(os.environ, {"ENABLE_AUTO_VERIFICATION": "false"}):
             resp = client.post(
                 "/api/action-plans/new-plan-id/verify",
                 headers={"Authorization": "Bearer test-token"}
             )
             assert resp.status_code == 400
             assert "disabled" in resp.json()["detail"].lower()
             print("Feature flag ENABLE_AUTO_VERIFICATION=false test passed!")

         # 3. Test version constants are present
         from core.observability import BOARDROOM_PROMPT_VERSION, SIGNAL_RULES_VERSION, ACTION_PLAN_SCHEMA_VERSION, VERIFICATION_RULES_VERSION, WORKFLOW_VERSION
         assert BOARDROOM_PROMPT_VERSION is not None
         assert SIGNAL_RULES_VERSION is not None
         assert ACTION_PLAN_SCHEMA_VERSION is not None
         assert VERIFICATION_RULES_VERSION is not None
         assert WORKFLOW_VERSION is not None
         print("Version constants validation passed!")

if __name__ == "__main__":
    test_normalization()
    test_scoring()
    test_crawl_safety()
    test_webhook_trigger()
    test_action_plans_api()
    test_phase_2_5_observability()
    asyncio.run(test_workflow())
