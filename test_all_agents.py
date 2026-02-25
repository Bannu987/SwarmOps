"""
MarketingOS 2.0 — Comprehensive Test Suite
Tests all agents, endpoints, memory, and pipelines.
"""
import requests
import json
import time
import sys

BASE = "http://localhost:8000"
TIMEOUT = 120  # some agents take a while
PASS = 0
FAIL = 0
RESULTS = []

def test(name, method, url, payload=None, expect_key="result"):
    global PASS, FAIL
    print(f"\n{'='*60}")
    print(f"🧪 TEST: {name}")
    print(f"   {method} {url}")
    if payload:
        print(f"   Payload: {json.dumps(payload)[:100]}...")
    print("-"*60)

    try:
        start = time.time()
        if method == "GET":
            r = requests.get(f"{BASE}{url}", timeout=TIMEOUT)
        elif method == "POST":
            r = requests.post(f"{BASE}{url}", json=payload, timeout=TIMEOUT)
        elif method == "DELETE":
            r = requests.delete(f"{BASE}{url}", timeout=TIMEOUT)
        else:
            raise ValueError(f"Unknown method: {method}")
        elapsed = round((time.time() - start) * 1000)

        if r.status_code != 200:
            print(f"   ❌ FAIL — HTTP {r.status_code}")
            print(f"   Response: {r.text[:300]}")
            FAIL += 1
            RESULTS.append({"test": name, "status": "FAIL", "reason": f"HTTP {r.status_code}", "ms": elapsed})
            return None

        data = r.json()
        success = data.get("success", True)
        has_result = expect_key in data or expect_key == "any"

        if not has_result and not success:
            print(f"   ❌ FAIL — success=false or no '{expect_key}' key")
            print(f"   Response keys: {list(data.keys())}")
            FAIL += 1
            RESULTS.append({"test": name, "status": "FAIL", "reason": "no result key", "ms": elapsed})
            return data

        # Show result preview
        result = data.get(expect_key, data.get("result", ""))
        if isinstance(result, str):
            preview = result[:200].replace("\n", " ")
        elif isinstance(result, dict):
            preview = json.dumps(result, indent=2)[:200]
        else:
            preview = str(result)[:200]

        model = data.get("model", "n/a")
        provider = data.get("provider", "n/a")
        quality = data.get("quality", {})
        confidence = quality.get("confidence", "n/a") if quality else "n/a"

        print(f"   ✅ PASS ({elapsed}ms)")
        print(f"   Model: {model} | Provider: {provider} | Confidence: {confidence}")
        print(f"   Result preview: {preview}...")
        PASS += 1
        RESULTS.append({"test": name, "status": "PASS", "ms": elapsed, "model": model, "provider": provider})
        return data

    except requests.exceptions.Timeout:
        print(f"   ❌ FAIL — TIMEOUT ({TIMEOUT}s)")
        FAIL += 1
        RESULTS.append({"test": name, "status": "FAIL", "reason": "timeout"})
        return None
    except Exception as e:
        print(f"   ❌ FAIL — {e}")
        FAIL += 1
        RESULTS.append({"test": name, "status": "FAIL", "reason": str(e)})
        return None


def main():
    global PASS, FAIL

    print("=" * 60)
    print("🚀 MarketingOS 2.0 — COMPREHENSIVE TEST SUITE")
    print("=" * 60)

    # ================================================================
    # PHASE 2: All Agents via /api/chat
    # ================================================================
    print("\n\n" + "🤖" * 30)
    print("PHASE 2: TESTING ALL AGENTS VIA /api/chat")
    print("🤖" * 30)

    chat_tests = [
        ("Content Agent", {"message": "Write a 3-sentence blog intro about AI in marketing", "agent": "content"}),
        ("SEO Agent", {"message": "Find keyword opportunities for SaaS project management", "agent": "seo"}),
        ("Analytics Agent", {"message": "Analyze: 5000 visitors, 150 conversions, $2000 spend last month", "agent": "analytics"}),
        ("PPC Agent", {"message": "Create a Google Ads strategy for online fitness coaching, $500/month budget", "agent": "ppc"}),
        ("CRM Agent", {"message": "Create a 3-email welcome sequence for SaaS onboarding", "agent": "crm"}),
        ("SMM Agent", {"message": "Write an Instagram post about productivity tips for entrepreneurs", "agent": "smm"}),
        ("Brand Agent", {"message": "Create brand positioning for an eco-friendly water bottle company", "agent": "brand"}),
        ("Web/UX Agent", {"message": "Design a landing page for an AI writing assistant tool", "agent": "webux"}),
        ("CRO Agent", {"message": "Analyze checkout funnel: 10000 visitors, 3000 cart, 800 checkout, 200 purchase", "agent": "cro"}),
        ("Research Agent", {"message": "Research AI in digital marketing 2025", "agent": "research"}),
    ]

    for name, payload in chat_tests:
        test(f"Chat: {name}", "POST", "/api/chat", payload)

    # ================================================================
    # PHASE 3: Nexus Smart Routing & Pipelines
    # ================================================================
    print("\n\n" + "🧠" * 30)
    print("PHASE 3: NEXUS SMART ROUTING & PIPELINES")
    print("🧠" * 30)

    test("Nexus: Smart Route (should detect SEO)",
         "POST", "/api/chat",
         {"message": "What are the best keywords for my bakery website?", "agent": "nexus"})

    test("Nexus: Pipeline (multi-agent)",
         "POST", "/api/chat",
         {"message": "Research AI marketing trends then create content about it", "agent": "nexus"})

    test("Agent Debate",
         "POST", "/api/debate",
         {"topic": "SEO vs PPC for a new startup", "agent_positions": {"seo": "SEO provides long-term ROI at lower cost", "ppc": "PPC delivers immediate traffic and leads"}})

    # ================================================================
    # PHASE 4: Direct Agent Endpoints
    # ================================================================
    print("\n\n" + "🔌" * 30)
    print("PHASE 4: DIRECT AGENT ENDPOINTS")
    print("🔌" * 30)

    test("Content Generate", "POST", "/api/content/generate",
         {"prompt": "Write 2 sentences about email marketing tips"})

    test("Analytics Dashboard", "GET", "/api/analytics/dashboard")

    test("SEO Rankings", "GET", "/api/seo/rankings")

    test("SEO Keywords", "GET", "/api/seo/keywords/ai%20marketing")

    test("PPC Campaigns", "GET", "/api/ppc/campaigns")

    test("SMM Trends", "GET", "/api/smm/trends?industry=technology")

    test("SMM Post", "POST", "/api/smm/post",
         {"platform": "linkedin", "topic": "AI tools for marketers", "brand_voice": "Professional", "goal": "engagement", "brand_name": "TechCo"})

    test("Brand Strategy", "POST", "/api/brand/strategy",
         {"company_name": "EcoBottle", "industry": "Consumer goods", "target_audience": "Millennials", "unique_value": "100% recyclable"})

    test("Web/UX Landing Page", "POST", "/api/webux/landing-page",
         {"product": "AI Assistant", "target_audience": "Developers", "goal": "signups"})

    test("CRO Funnel", "POST", "/api/cro/analyze-funnel",
         {"funnel_steps": "Visit > Sign up > Activate > Subscribe", "conversion_data": "50% drop at activation", "goal": "reduce churn"})

    test("Research Topic", "POST", "/api/research/topic",
         {"topic": "voice search optimization"})

    # ================================================================
    # PHASE 5: Memory & Profile System
    # ================================================================
    print("\n\n" + "💾" * 30)
    print("PHASE 5: MEMORY & PROFILE SYSTEM")
    print("💾" * 30)

    test("Set Profile Key", "POST", "/api/business-profile",
         {"key": "industry", "value": "SaaS"})

    test("Get Profile", "GET", "/api/business-profile", expect_key="profile")

    test("Get Stats", "GET", "/api/stats", expect_key="any")

    test("Get History", "GET", "/api/history", expect_key="tasks")

    test("Get Memory (SEO)", "GET", "/api/memory/seo", expect_key="memories")

    test("Export Memory", "POST", "/api/memory/export", expect_key="any")

    test("Get Insights", "GET", "/api/insights/seo", expect_key="insights")

    # ================================================================
    # PHASE 6: Integration Endpoints
    # ================================================================
    print("\n\n" + "🔗" * 30)
    print("PHASE 6: INTEGRATION ENDPOINTS")
    print("🔗" * 30)

    test("CRM Contacts (HubSpot)", "GET", "/api/crm/contacts")
    test("Email Performance", "GET", "/api/crm/email-performance")
    test("Analytics Anomalies", "GET", "/api/analytics/anomalies")
    test("CRM Email Sequence", "POST", "/api/crm/email-sequence",
         {"topic": "Welcome to our product", "num_emails": 2})

    # ================================================================
    # FINAL SUMMARY
    # ================================================================
    print("\n\n" + "=" * 60)
    print("📊 FINAL TEST RESULTS")
    print("=" * 60)
    print(f"\n   ✅ PASSED: {PASS}")
    print(f"   ❌ FAILED: {FAIL}")
    print(f"   📊 TOTAL:  {PASS + FAIL}")
    print(f"   📈 PASS RATE: {round(PASS / (PASS + FAIL) * 100, 1) if (PASS + FAIL) > 0 else 0}%")

    print("\n" + "-" * 60)
    print("DETAILED RESULTS:")
    print("-" * 60)
    for r in RESULTS:
        status_icon = "✅" if r["status"] == "PASS" else "❌"
        ms = f" ({r.get('ms', '?')}ms)" if "ms" in r else ""
        reason = f" — {r.get('reason', '')}" if r.get("reason") else ""
        print(f"   {status_icon} {r['test']}{ms}{reason}")

    print("\n" + "=" * 60)

    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump({"pass": PASS, "fail": FAIL, "results": RESULTS}, f, indent=2)
    print("📁 Results saved to test_results.json")

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
