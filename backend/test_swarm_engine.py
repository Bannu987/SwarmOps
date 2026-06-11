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

    # Assertions based on requirement 14
    assert "User-agent: *" in response, "Missing user-agent rule"
    assert "Allow: /" in response, "Missing allow rule"
    assert "Sitemap: https://shravanpayyavula.me/sitemap.xml" in response, "Missing sitemap rule"
    assert "controls crawler access, not indexing" in response, "Inaccurate robots.txt explanation"
    assert "visit /robots.txt" in response.lower(), "Missing verification step"
    
    # Verify no rate-limiting or backup alerts
    assert "rate limit" not in response.lower()
    assert "offline" not in response.lower()
    assert "fallback" not in response.lower()
    
    # Verify no inaccurate CTR or citations claims
    assert "30%" not in response
    assert "critical for chatgpt" not in response.lower()

    print("Workflow validation test passed successfully!")

if __name__ == "__main__":
    test_normalization()
    test_scoring()
    test_crawl_safety()
    asyncio.run(test_workflow())
