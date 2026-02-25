"""Check exact EQ response content for the panicking test case."""
import requests, json

BASE = "http://localhost:8000"

# The exact acceptance criteria test case
message = "I'm panicking, I have no signups"
print(f"Input: {message}\n")

r = requests.post(f"{BASE}/api/chat",
                  json={"message": message, "agent": "nexus"},
                  timeout=90)
d = r.json()

print(f"HTTP: {r.status_code}")
print(f"Success: {d.get('success')}")
print(f"Model: {d.get('model')} / {d.get('provider')}")
print(f"Quality confidence: {d.get('quality', {}).get('confidence', 'n/a')}")

result = d.get("result", "")
print(f"\n=== FULL NEXUS RESPONSE ({len(result)} chars) ===\n")
print(result)
