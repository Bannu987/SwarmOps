"""
DataForSEO Integration - MarketingOS 2.0
Real keyword research: search volume, competition, CPC, SERP snapshots.

Requires:
  - DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD in .env
  - Sign up at dataforseo.com (free tier: 10 requests/day)
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class DataForSEO:
    BASE_URL = "https://api.dataforseo.com/v3"

    def __init__(self):
        self.available = False
        self.login = os.getenv("DATAFORSEO_LOGIN", "")
        self.password = os.getenv("DATAFORSEO_PASSWORD", "")
        self._initialize()

    def _initialize(self):
        if not self.login or not self.password:
            print("⚠️  [DataForSEO] DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not set")
            return
        try:
            # Light validation — a GET to any endpoint returns 400 if auth is valid
            resp = requests.get(
                f"{self.BASE_URL}/serp/google/organic/live/first",
                auth=(self.login, self.password),
                timeout=8,
            )
            if resp.status_code in (200, 400):
                self.available = True
                print("✅ [DataForSEO] Connected")
            else:
                print(f"⚠️  [DataForSEO] Auth check returned {resp.status_code}")
        except Exception as e:
            print(f"⚠️  [DataForSEO] Connection check failed: {e}")

    def _post(self, endpoint, payload):
        """Authenticated POST helper."""
        try:
            resp = requests.post(
                f"{self.BASE_URL}{endpoint}",
                auth=(self.login, self.password),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"❌ [DataForSEO] {endpoint} → {e}")
            return None

    # ------------------------------------------------------------------

    def get_keyword_data(self, keyword, location_code="2840", language_code="en"):
        """
        Search volume, competition level, and CPC for a keyword.
        location_code 2840 = USA.
        Returns: dict or None
        """
        if not self.available:
            return None

        data = self._post(
            "/keywords_data/google_ads/keywords_for_keywords/live",
            [
                {
                    "keyword": keyword,
                    "location_code": int(location_code),
                    "language_code": language_code,
                }
            ],
        )
        if not data:
            return None

        try:
            results = data["tasks"][0].get("result", [])
            # Prefer exact match
            for r in results:
                if r.get("keyword", "").lower() == keyword.lower():
                    return self._format_kw(r)
            # Fall back to first result
            if results:
                return self._format_kw(results[0])
            return None
        except (KeyError, IndexError) as e:
            print(f"❌ [DataForSEO] Parse error: {e}")
            return None

    @staticmethod
    def _format_kw(r):
        return {
            "keyword": r.get("keyword", ""),
            "search_volume": r.get("search_volume", 0),
            "competition": r.get("competition", "unknown"),
            "cpc": r.get("cpc", 0),
            "monthly_searches": r.get("monthly_searches", {}),
        }

    def get_related_keywords(self, keyword, location_code="2840", limit=20):
        """
        Related keywords with search volume, sorted descending.
        Returns: list[dict] or None
        """
        if not self.available:
            return None

        data = self._post(
            "/keywords_data/google_ads/keywords_for_keywords/live",
            [
                {
                    "keyword": keyword,
                    "location_code": int(location_code),
                    "language_code": "en",
                }
            ],
        )
        if not data:
            return None

        try:
            results = data["tasks"][0].get("result", [])
            keywords = [self._format_kw(r) for r in results[:limit]]
            keywords.sort(key=lambda x: x["search_volume"], reverse=True)
            return keywords
        except Exception as e:
            print(f"❌ [DataForSEO] Related keywords error: {e}")
            return None

    def get_serp_results(self, keyword, location_code="2840"):
        """
        Live SERP snapshot — top 10 organic results for a keyword.
        Returns: list[{rank, title, url, description, domain}] or None
        """
        if not self.available:
            return None

        data = self._post(
            "/serp/google/organic/live/advanced",
            [
                {
                    "keyword": keyword,
                    "location_code": int(location_code),
                    "language_code": "en",
                    "device": "desktop",
                }
            ],
        )
        if not data:
            return None

        try:
            items = data["tasks"][0].get("result", [{}])[0].get("items", [])
            return [
                {
                    "rank": item.get("rank_absolute"),
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("description", ""),
                    "domain": item.get("domain", ""),
                }
                for item in items[:10]
                if item.get("type") == "organic"
            ]
        except Exception as e:
            print(f"❌ [DataForSEO] SERP results error: {e}")
            return None

    def get_backlink_overview(self, domain):
        """
        Backlink summary for a domain.
        Returns: dict or None
        """
        if not self.available:
            return None

        data = self._post("/backlinks/summary/live", [{"target": domain}])
        if not data:
            return None

        try:
            result = data["tasks"][0].get("result", [{}])[0]
            return {
                "domain": domain,
                "backlinks_total": result.get("backlinks_total", 0),
                "referring_domains": result.get("referring_domains", 0),
                "domain_authority": result.get("domain_authority", 0),
                "organic_keywords": result.get("organic_keywords", 0),
            }
        except Exception as e:
            print(f"❌ [DataForSEO] Backlink overview error: {e}")
            return None
