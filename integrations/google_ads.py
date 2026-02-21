"""
Google Ads Integration - SwarmOps
Create and manage real Google Ads search campaigns.

Requires:
  - google-auth package (pip install google-auth)
  - Same service account JSON as GA4 (needs Google Ads API access)
  - GOOGLE_ADS_CUSTOMER_ID and GOOGLE_ADS_DEVELOPER_TOKEN in .env
  - Developer token must be approved by Google
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class GoogleAds:
    BASE_URL = "https://googleads.googleapis.com/v16"

    def __init__(self):
        self.available = False
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
        self.developer_token = os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN", "")
        self.sa_file = os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_JSON", "google_service_account.json"
        )
        self.access_token = None
        self._initialize()

    def _initialize(self):
        if not self.customer_id:
            print("⚠️  [Google Ads] GOOGLE_ADS_CUSTOMER_ID not set")
            return
        if not self.developer_token:
            print("⚠️  [Google Ads] GOOGLE_ADS_DEVELOPER_TOKEN not set")
            return
        if not os.path.exists(self.sa_file):
            print(f"⚠️  [Google Ads] Service account file not found: {self.sa_file}")
            return
        try:
            from google.oauth2 import service_account
            import google.auth.transport.requests

            creds = service_account.Credentials.from_service_account_file(
                self.sa_file,
                scopes=["https://www.googleapis.com/auth/adwords"],
            )
            creds.refresh(google.auth.transport.requests.Request())
            self.access_token = creds.token
            self.available = True
            print("✅ [Google Ads] Connected")
        except ImportError:
            print("⚠️  [Google Ads] Install: pip install google-auth")
        except Exception as e:
            print(f"⚠️  [Google Ads] Connection failed: {e}")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "developer-token": self.developer_token,
            "Content-Type": "application/json",
        }

    def _search(self, query):
        """Execute a GAQL search query."""
        try:
            resp = requests.post(
                f"{self.BASE_URL}/customers/{self.customer_id}/googleads/search",
                headers=self._headers(),
                json={"query": query},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"❌ [Google Ads] Search error: {e}")
            return None

    # ------------------------------------------------------------------

    def get_campaign_performance(self, days=30):
        """
        All active campaigns with key performance metrics.
        Returns: list[dict] or None
        """
        if not self.available:
            return None

        query = (
            "SELECT campaign.name, campaign.id, campaign.status, "
            "metrics.clicks, metrics.impressions, metrics.conversions, "
            "metrics.cost_micros, metrics.average_cpc "
            f"FROM campaign WHERE campaign.status = 'ENABLED' "
            f"DURING LAST_{days}_DAYS"
        )
        data = self._search(query)
        if not data:
            return None

        campaigns = []
        for row in data.get("results", []):
            cost_micros = row.get("metrics", {}).get("costMicros", 0)
            clicks = row.get("metrics", {}).get("clicks", 0)
            conversions = row.get("metrics", {}).get("conversions", 0)
            cost_usd = int(cost_micros) / 1_000_000

            campaigns.append(
                {
                    "name": row.get("campaign", {}).get("name", ""),
                    "id": row.get("campaign", {}).get("id", ""),
                    "status": row.get("campaign", {}).get("status", ""),
                    "clicks": int(clicks),
                    "impressions": int(row.get("metrics", {}).get("impressions", 0)),
                    "conversions": float(conversions),
                    "cost_usd": round(cost_usd, 2),
                    "cpc_usd": round(cost_usd / int(clicks), 2) if int(clicks) else 0,
                    "roas": round(0, 2),  # Requires revenue tracking setup
                    "cpa_usd": round(cost_usd / float(conversions), 2)
                    if float(conversions)
                    else 0,
                }
            )
        return campaigns

    def create_search_campaign(
        self, name, daily_budget, keywords, ad_headlines, ad_descriptions, final_url
    ):
        """
        Create a Google Search campaign via the REST API.

        Args:
            name: Campaign name
            daily_budget: Daily budget in USD (e.g. 50.0)
            keywords: list of keyword strings
            ad_headlines: list of headlines (max 15, each ≤30 chars)
            ad_descriptions: list of descriptions (max 4, each ≤90 chars)
            final_url: landing page URL

        Returns: dict with campaign details or None
        """
        if not self.available:
            return None

        budget_micros = int(daily_budget * 1_000_000)

        # Step 1: Create campaign budget
        budget_payload = {
            "amountMicros": budget_micros,
            "name": f"{name} Budget",
            "deliveryMethod": "STANDARD",
        }
        try:
            resp = requests.post(
                f"{self.BASE_URL}/customers/{self.customer_id}/campaignBudgets:mutate",
                headers=self._headers(),
                json={"operations": [{"create": budget_payload}]},
                timeout=30,
            )
            resp.raise_for_status()
            budget_resource = resp.json().get("results", [{}])[0].get(
                "resourceName", ""
            )
        except Exception as e:
            print(f"❌ [Google Ads] Budget creation failed: {e}")
            return None

        # Step 2: Create campaign
        campaign_payload = {
            "name": name,
            "status": "ENABLED",
            "campaignBudget": budget_resource,
            "advertisingChannelType": "SEARCH",
            "targetCpa": {"targetCpaMicros": 1_000_000},
        }
        try:
            resp = requests.post(
                f"{self.BASE_URL}/customers/{self.customer_id}/campaigns:mutate",
                headers=self._headers(),
                json={"operations": [{"create": campaign_payload}]},
                timeout=30,
            )
            resp.raise_for_status()
            campaign_resource = resp.json().get("results", [{}])[0].get(
                "resourceName", ""
            )
        except Exception as e:
            print(f"❌ [Google Ads] Campaign creation failed: {e}")
            return None

        return {
            "status": "created",
            "campaign_name": name,
            "campaign_resource": campaign_resource,
            "daily_budget_usd": daily_budget,
            "keywords_count": len(keywords),
            "headlines_count": len(ad_headlines),
            "note": "Campaign created. Ad groups and ads require additional mutate calls.",
        }

    def pause_campaign(self, campaign_id):
        """Pause a campaign by resource name or ID."""
        if not self.available:
            return None

        resource = campaign_id
        if not campaign_id.startswith("customers/"):
            resource = f"customers/{self.customer_id}/campaigns/{campaign_id}"

        try:
            resp = requests.post(
                f"{self.BASE_URL}/customers/{self.customer_id}/campaigns:mutate",
                headers=self._headers(),
                json={
                    "operations": [
                        {"update": {"resourceName": resource, "status": "PAUSED"}}
                    ],
                    "updateMask": {"paths": ["status"]},
                },
                timeout=30,
            )
            resp.raise_for_status()
            return {"status": "paused", "campaign": campaign_id}
        except Exception as e:
            print(f"❌ [Google Ads] Pause failed: {e}")
            return None

    def update_daily_budget(self, budget_resource, new_budget_usd):
        """Update a campaign budget. budget_resource = the budget resource name."""
        if not self.available:
            return None

        try:
            resp = requests.post(
                f"{self.BASE_URL}/customers/{self.customer_id}/campaignBudgets:mutate",
                headers=self._headers(),
                json={
                    "operations": [
                        {
                            "update": {
                                "resourceName": budget_resource,
                                "amountMicros": int(new_budget_usd * 1_000_000),
                            }
                        }
                    ],
                    "updateMask": {"paths": ["amountMicros"]},
                },
                timeout=30,
            )
            resp.raise_for_status()
            return {"status": "updated", "new_budget_usd": new_budget_usd}
        except Exception as e:
            print(f"❌ [Google Ads] Budget update failed: {e}")
            return None
