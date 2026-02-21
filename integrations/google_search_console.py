"""
Google Search Console Integration - SwarmOps
Pulls real organic search performance: rankings, clicks, impressions, CTR.

Requires:
  - google-api-python-client (pip install google-api-python-client)
  - Same service account JSON as GA4 (needs Search Console API enabled)
  - SEARCH_CONSOLE_SITE_URL in .env
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class GoogleSearchConsole:
    def __init__(self):
        self.available = False
        self.service = None
        self.site_url = os.getenv("SEARCH_CONSOLE_SITE_URL", "")
        self.sa_file = os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_JSON", "google_service_account.json"
        )
        self._initialize()

    def _initialize(self):
        if not os.path.exists(self.sa_file):
            print(f"⚠️  [GSC] Service account file not found: {self.sa_file}")
            return
        if not self.site_url:
            print("⚠️  [GSC] SEARCH_CONSOLE_SITE_URL not set in .env")
            return
        try:
            from googleapiclient.discovery import build
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                self.sa_file,
                scopes=["https://www.googleapis.com/auth/webmasters.readonly"],
            )
            self.service = build("searchconsole", "v1", credentials=credentials)
            self.available = True
            print("✅ [GSC] Google Search Console connected")
        except ImportError:
            print("⚠️  [GSC] Install: pip install google-api-python-client")
        except Exception as e:
            print(f"⚠️  [GSC] Connection failed: {e}")

    def _query(self, body):
        """Execute a Search Analytics query."""
        return (
            self.service.searchAnalytics()
            .query(propertyUrl=self.site_url, body=body)
            .execute()
        )

    # ------------------------------------------------------------------

    def get_top_queries(self, days=28, limit=50):
        """
        Top search queries ranked by clicks.
        Returns: list[{query, clicks, impressions, ctr, position}] or None
        """
        if not self.available:
            return None
        try:
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            resp = self._query(
                {
                    "startDate": start,
                    "endDate": end,
                    "dimensions": ["query"],
                    "rowLimit": limit,
                    "orderby": [{"field": "clicks", "direction": "descending"}],
                }
            )

            return [
                {
                    "query": row["keys"][0],
                    "clicks": row["clicks"],
                    "impressions": row["impressions"],
                    "ctr": round(row["ctr"] * 100, 1),
                    "position": round(row["position"], 1),
                }
                for row in resp.get("rows", [])
            ]
        except Exception as e:
            print(f"❌ [GSC] Top queries error: {e}")
            return None

    def get_page_rankings(self, days=28, limit=50):
        """
        Top pages by clicks with avg position.
        Returns: list[{url, clicks, impressions, ctr, position}] or None
        """
        if not self.available:
            return None
        try:
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            resp = self._query(
                {
                    "startDate": start,
                    "endDate": end,
                    "dimensions": ["page"],
                    "rowLimit": limit,
                    "orderby": [{"field": "clicks", "direction": "descending"}],
                }
            )

            return [
                {
                    "url": row["keys"][0],
                    "clicks": row["clicks"],
                    "impressions": row["impressions"],
                    "ctr": round(row["ctr"] * 100, 1),
                    "position": round(row["position"], 1),
                }
                for row in resp.get("rows", [])
            ]
        except Exception as e:
            print(f"❌ [GSC] Page rankings error: {e}")
            return None

    def get_keyword_opportunities(self, days=28):
        """
        Keywords we already appear for but don't rank well on.
        Criteria: impressions > 50 AND (CTR < 2% OR position > 10).
        Sorted by opportunity_score descending.
        Returns: list[dict] or None
        """
        if not self.available:
            return None

        queries = self.get_top_queries(days=days, limit=200)
        if not queries:
            return None

        opportunities = []
        for q in queries:
            if q["impressions"] > 50 and (q["ctr"] < 2.0 or q["position"] > 10):
                opportunities.append(
                    {
                        **q,
                        "opportunity_score": round(
                            (q["impressions"] * (1 - q["ctr"] / 100))
                            / max(q["position"], 1),
                            1,
                        ),
                    }
                )

        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return opportunities[:20]

    def get_search_trends(self, days=90):
        """
        Daily search performance over last N days (for trend analysis).
        Returns: list[{date, clicks, impressions, ctr, position}] or None
        """
        if not self.available:
            return None
        try:
            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            resp = self._query(
                {
                    "startDate": start,
                    "endDate": end,
                    "dimensions": ["date"],
                    "rowLimit": 1000,
                }
            )

            return [
                {
                    "date": row["keys"][0],
                    "clicks": row["clicks"],
                    "impressions": row["impressions"],
                    "ctr": round(row["ctr"] * 100, 1),
                    "position": round(row["position"], 1),
                }
                for row in resp.get("rows", [])
            ]
        except Exception as e:
            print(f"❌ [GSC] Search trends error: {e}")
            return None
