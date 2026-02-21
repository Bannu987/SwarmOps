"""
HubSpot Integration - SwarmOps
Contact management, email sending, and CRM data.

Requires:
  - HUBSPOT_ACCESS_TOKEN in .env
  - HubSpot Private App with contacts + emails scopes
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class HubSpot:
    BASE_URL = "https://api.hubapi.com"

    def __init__(self):
        self.available = False
        self.access_token = os.getenv("HUBSPOT_ACCESS_TOKEN", "")
        self._initialize()

    def _initialize(self):
        if not self.access_token:
            print("⚠️  [HubSpot] HUBSPOT_ACCESS_TOKEN not set")
            return
        try:
            resp = requests.get(
                f"{self.BASE_URL}/crm/v3/objects/contacts?limit=1",
                headers=self._headers(),
                timeout=10,
            )
            if resp.status_code == 200:
                self.available = True
                print("✅ [HubSpot] Connected")
            elif resp.status_code == 401:
                print("⚠️  [HubSpot] Invalid access token")
            else:
                print(f"⚠️  [HubSpot] Status {resp.status_code}")
        except Exception as e:
            print(f"⚠️  [HubSpot] Connection failed: {e}")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    # ------------------------------------------------------------------

    def create_contact(self, email, first_name="", last_name="", company="", **props):
        """
        Create a contact. Returns {id, email, status} or None.
        If the contact already exists, returns status='already_exists'.
        """
        if not self.available:
            return None

        properties = {"email": email}
        if first_name:
            properties["firstname"] = first_name
        if last_name:
            properties["lastname"] = last_name
        if company:
            properties["company"] = company
        properties.update(props)

        try:
            resp = requests.post(
                f"{self.BASE_URL}/crm/v3/objects/contacts",
                headers=self._headers(),
                json={"properties": properties},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return {"id": data.get("id"), "email": email, "status": "created"}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                return {"status": "already_exists", "email": email}
            print(f"❌ [HubSpot] Create contact: {e}")
            return None
        except Exception as e:
            print(f"❌ [HubSpot] Create contact: {e}")
            return None

    def get_contacts(self, limit=100, filter_property=None, filter_value=None):
        """
        Get contacts, optionally filtered.
        Returns: list[{id, email, name, company, created_at}] or None
        """
        if not self.available:
            return None
        try:
            if filter_property and filter_value:
                resp = requests.post(
                    f"{self.BASE_URL}/crm/v3/objects/contacts/search",
                    headers=self._headers(),
                    json={
                        "filterGroups": [
                            {
                                "filters": [
                                    {
                                        "propertyName": filter_property,
                                        "operator": "EQ",
                                        "value": str(filter_value),
                                    }
                                ]
                            }
                        ],
                        "limit": limit,
                        "sorts": [
                            {"propertyName": "createddate", "sortOrder": "DESCENDING"}
                        ],
                    },
                    timeout=10,
                )
            else:
                resp = requests.get(
                    f"{self.BASE_URL}/crm/v3/objects/contacts",
                    headers=self._headers(),
                    params={
                        "limit": limit,
                        "sort": "createdAt",
                        "order": "DESC",
                    },
                    timeout=10,
                )
            resp.raise_for_status()
            data = resp.json()

            contacts = []
            for obj in data.get("results", []):
                p = obj.get("properties", {})
                contacts.append(
                    {
                        "id": obj.get("id"),
                        "email": p.get("email", ""),
                        "name": f"{p.get('firstname', '')} {p.get('lastname', '')}".strip(),
                        "company": p.get("company", ""),
                        "created_at": p.get("createddate", ""),
                    }
                )
            return contacts
        except Exception as e:
            print(f"❌ [HubSpot] Get contacts: {e}")
            return None

    def send_email(self, contact_id, email_id, email_properties=None):
        """
        Send a single email using a HubSpot email template.
        email_id = the HubSpot email CTA template ID.
        Returns: {status, contact_id, email_id} or None
        """
        if not self.available:
            return None
        try:
            payload = {
                "emailId": int(email_id),
                "contactId": int(contact_id),
            }
            if email_properties:
                payload["emailProperties"] = email_properties

            resp = requests.post(
                f"{self.BASE_URL}/crm/v3/actions/emails/singleEmail/send",
                headers=self._headers(),
                json=payload,
                timeout=10,
            )
            resp.raise_for_status()
            return {"status": "sent", "contact_id": contact_id, "email_id": email_id}
        except Exception as e:
            print(f"❌ [HubSpot] Send email: {e}")
            return None

    def get_email_stats(self):
        """
        Email marketing performance stats.
        Returns: raw HubSpot response dict or None
        """
        if not self.available:
            return None
        try:
            resp = requests.get(
                f"{self.BASE_URL}/email/v1/statistics/daily",
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"❌ [HubSpot] Email stats: {e}")
            return None

    def get_deals_pipeline(self):
        """
        Current sales pipeline deals.
        Returns: list[{id, name, stage, amount, close_date}] or None
        """
        if not self.available:
            return None
        try:
            resp = requests.get(
                f"{self.BASE_URL}/crm/v3/objects/deals",
                headers=self._headers(),
                params={"limit": 100, "sort": "closedate", "order": "DESC"},
                timeout=10,
            )
            resp.raise_for_status()
            deals = []
            for obj in resp.json().get("results", []):
                p = obj.get("properties", {})
                deals.append(
                    {
                        "id": obj.get("id"),
                        "name": p.get("dealname", ""),
                        "stage": p.get("dealstage", ""),
                        "amount": p.get("amount", 0),
                        "close_date": p.get("closedate", ""),
                    }
                )
            return deals
        except Exception as e:
            print(f"❌ [HubSpot] Deals pipeline: {e}")
            return None
