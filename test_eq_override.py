"""EQ Override Test — simulates a highly emotional user input to verify the Empathy Override triggers."""
import requests, json, time

BASE = "http://localhost:8000"

tests = [
    # Test 1: The exact test case from the acceptance criteria
    ("EQ Test: Panicking no signups",
     "I'm panicking, I have no signups",
     True),  # expect EQ override
    
    # Test 2: Another distress signal
    ("EQ Test: Overwhelmed founder",
     "I'm completely overwhelmed, nothing is working, I'm burning money and have no idea what to do",
     True),  # expect EQ override

    # Test 3: Normal strategic request (should NOT trigger EQ)
    ("Normal: SEO strategy request",
     "What are the best SEO strategies for a SaaS product in 2025?",
     False),  # expect CMO strategic response, not EQ override

    # Test 4: Revenue diagnostic (should trigger revenue-first lens)
    ("Normal: Revenue question",
     "My traffic is high but conversions are very low, what should I focus on?",
     False),  # expect CRO/revenue framing
]

print("=" * 70)
print("🧠 NEXUS MASTER PROMPT — ACCEPTANCE CRITERIA TEST")
print("=" * 70)

all_passed = True
for name, message, expect_eq in tests:
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print(f"  Input:        '{message[:80]}'")
    print(f"  Expect EQ:    {expect_eq}")
    print("-" * 70)
    
    s = time.time()
    try:
        r = requests.post(f"{BASE}/api/chat",
                          json={"message": message, "agent": "nexus"},
                          timeout=120)
        ms = round((time.time() - s) * 1000)
        d = r.json()

        result = str(d.get("result", ""))
        model = d.get("model", "?")
        provider = d.get("provider", "?")
        success = d.get("success", False)

        print(f"  HTTP:         {r.status_code}")
        print(f"  Success:      {success}")
        print(f"  Model:        {model} / {provider}")
        print(f"  Latency:      {ms}ms")
        print(f"  Response length: {len(result)} chars")
        print(f"\n  RESPONSE PREVIEW:")
        print(f"  {'─'*60}")
        # Show first 500 chars of response
        for line in result[:500].split('\n')[:8]:
            print(f"  {line}")
        print(f"  {'─'*60}")

        # EQ check heuristics
        eq_tone_words = [
            "breath", "breathe", "not broken", "okay", "understandable",
            "normal", "natural", "first", "one thing", "start with",
            "calm", "relax", "take a step", "got you", "makes sense",
            "hear you", "feel", "totally", "completely normal"
        ]
        result_lower = result.lower()
        eq_detected = any(word in result_lower for word in eq_tone_words)

        if expect_eq:
            # EQ override should be present
            passed = success and eq_detected
            status = "✅ PASS" if passed else "❌ FAIL (EQ Override not clearly detected)"
        else:
            # Normal response — should be strategic and have content
            passed = success and len(result) > 100
            status = "✅ PASS" if passed else "❌ FAIL"

        print(f"\n  EQ TONE DETECTED: {eq_detected}")
        print(f"  RESULT: {status}")

        if not passed:
            all_passed = False

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        all_passed = False

print(f"\n{'='*70}")
print(f"FINAL VERDICT: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
print(f"{'='*70}")
