"""
SwarmOps - Integration Layer
Real API connections to marketing platforms.

Each integration checks for credentials at init time.
If credentials are missing, self.available = False and all methods return None gracefully.
Agents check this flag and fall back to LLM-only mode automatically.
"""
