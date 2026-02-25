"""Quick single-agent test helper"""
import requests, json, time, sys

BASE = "http://localhost:8000"

def test_chat(agent, message):
    print(f"\n{'='*60}")
    print(f"Testing: {agent.upper()} Agent")
    print(f"{'='*60}")
    s = time.time()
    try:
        r = requests.post(f"{BASE}/api/chat", json={"message": message, "agent": agent}, timeout=120)
        ms = round((time.time() - s) * 1000)
        d = r.json()
        print(f"  HTTP:       {r.status_code}")
        print(f"  Success:    {d.get('success')}")
        print(f"  Agent:      {d.get('agent')}")
        print(f"  Model:      {d.get('model')}")
        print(f"  Provider:   {d.get('provider')}")
        print(f"  Latency:    {ms}ms")
        q = d.get("quality", {})
        if q:
            print(f"  Confidence: {q.get('confidence')}")
            print(f"  Approved:   {q.get('approved')}")
            print(f"  Revised:    {q.get('revised')}")
        result = str(d.get("result", ""))
        print(f"  Result:     {result[:250]}...")
        return "PASS" if d.get("success") else "FAIL"
    except Exception as e:
        print(f"  ERROR: {e}")
        return "FAIL"

def test_get(name, url):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    s = time.time()
    try:
        r = requests.get(f"{BASE}{url}", timeout=120)
        ms = round((time.time() - s) * 1000)
        d = r.json()
        print(f"  HTTP:    {r.status_code}")
        print(f"  Latency: {ms}ms")
        result = json.dumps(d, indent=2)[:400]
        print(f"  Result:  {result}")
        return "PASS" if r.status_code == 200 else "FAIL"
    except Exception as e:
        print(f"  ERROR: {e}")
        return "FAIL"

def test_post(name, url, payload):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    s = time.time()
    try:
        r = requests.post(f"{BASE}{url}", json=payload, timeout=120)
        ms = round((time.time() - s) * 1000)
        d = r.json()
        print(f"  HTTP:    {r.status_code}")
        print(f"  Success: {d.get('success')}")
        print(f"  Latency: {ms}ms")
        result = str(d.get("result", json.dumps(d, indent=2)))[:300]
        print(f"  Result:  {result}...")
        return "PASS" if d.get("success", r.status_code == 200) else "FAIL"
    except Exception as e:
        print(f"  ERROR: {e}")
        return "FAIL"

results = []

# Test whatever is passed as argument
mode = sys.argv[1] if len(sys.argv) > 1 else "agents"

if mode == "agents":
    # Phase 2: All agents
    agents = [
        ("content", "Write a 3-sentence blog intro about AI in marketing"),
        ("seo", "Find keyword opportunities for SaaS project management"),
        ("analytics", "Analyze: 5000 visitors, 150 conversions, $2000 spend"),
        ("ppc", "Create Google Ads strategy for fitness coaching, $500/month"),
        ("crm", "Create a 3-email welcome sequence for SaaS onboarding"),
        ("smm", "Write an Instagram post about productivity tips"),
        ("brand", "Brand positioning for eco-friendly water bottle company"),
        ("webux", "Design a landing page for an AI writing assistant"),
        ("cro", "Funnel: 10000 visitors, 3000 cart, 800 checkout, 200 buy"),
        ("research", "Research AI in digital marketing 2025"),
    ]
    for agent, msg in agents:
        r = test_chat(agent, msg)
        results.append((agent, r))

elif mode == "nexus":
    # Phase 3: Nexus + Pipeline
    r = test_chat("nexus", "What are the best keywords for my bakery website?")
    results.append(("nexus-route", r))
    r = test_chat("nexus", "Research AI trends then create SEO content about it")
    results.append(("nexus-pipeline", r))
    r = test_post("Agent Debate", "/api/debate",
        {"topic": "SEO vs PPC", "agent_positions": {"seo": "Long-term ROI", "ppc": "Immediate results"}})
    results.append(("debate", r))

elif mode == "endpoints":
    # Phase 4: Direct endpoints
    results.append(("content-gen", test_post("Content Generate", "/api/content/generate", {"prompt": "Email marketing tips"})))
    results.append(("analytics-dash", test_get("Analytics Dashboard", "/api/analytics/dashboard")))
    results.append(("seo-rankings", test_get("SEO Rankings", "/api/seo/rankings")))
    results.append(("seo-kw", test_get("SEO Keywords", "/api/seo/keywords/ai%20marketing")))
    results.append(("ppc-camps", test_get("PPC Campaigns", "/api/ppc/campaigns")))
    results.append(("smm-trends", test_get("SMM Trends", "/api/smm/trends?industry=technology")))
    results.append(("brand-strat", test_post("Brand Strategy", "/api/brand/strategy",
        {"company_name": "EcoBottle", "industry": "Consumer goods", "target_audience": "Millennials", "unique_value": "Recyclable"})))

elif mode == "memory":
    # Phase 5: Memory & Profile
    results.append(("set-profile", test_post("Set Profile", "/api/business-profile", {"key": "industry", "value": "SaaS"})))
    results.append(("get-profile", test_get("Get Profile", "/api/business-profile")))
    results.append(("stats", test_get("Stats", "/api/stats")))
    results.append(("history", test_get("History", "/api/history")))
    results.append(("memory-seo", test_get("Memory SEO", "/api/memory/seo")))
    results.append(("insights", test_get("Insights", "/api/insights/seo")))

elif mode == "integrations":
    # Phase 6: Integration endpoints
    results.append(("contacts", test_get("HubSpot Contacts", "/api/crm/contacts")))
    results.append(("email-perf", test_get("Email Performance", "/api/crm/email-performance")))
    results.append(("anomalies", test_get("GA4 Anomalies", "/api/analytics/anomalies")))

# Summary
print(f"\n\n{'='*60}")
print(f"SUMMARY: {mode.upper()}")
print(f"{'='*60}")
passed = sum(1 for _, r in results if r == "PASS")
failed = sum(1 for _, r in results if r == "FAIL")
for name, r in results:
    icon = "✅" if r == "PASS" else "❌"
    print(f"  {icon} {name}")
print(f"\n  PASSED: {passed} | FAILED: {failed} | TOTAL: {len(results)}")
