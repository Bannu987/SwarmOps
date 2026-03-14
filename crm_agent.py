"""
CRM Agent - SwarmOps
Email sequences and customer relationship management
Uses model_router for multi-provider AI with automatic fallback
"""

import os
from dotenv import load_dotenv
from model_router import call_model_sync

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# AGENT CONVERSATIONAL RULES — appended to all prompts
# ---------------------------------------------------------------------------
AGENT_CONVERSATIONAL_RULES = """

RESPONSE STYLE RULES:
- Write in clear, professional prose — not as a data dump or raw report
- Always explain WHY a finding matters, not just WHAT it is
- Reference the brand/business by name when brand context is provided
- Keep responses between 150-250 words unless more detail is clearly needed
- Suggest ONE specific next step at the end of every response
- Never output raw JSON, raw metrics tables, or unformatted lists as your main response
- If data is unavailable, say so honestly and provide strategic guidance instead
- Format key insights with **bold** for scannability
- End every response with: "**Next step:** [specific action]"
"""


class CRMAgent:
    """
    CRM Agent - Specialized in email marketing and customer nurture
    Uses multi-provider model router with automatic fallback
    """

    def __init__(self):
        """Initialize the CRM Agent"""
        print("📧 Initializing CRM Agent...")
        print("✅ CRM Agent ready (Multi-Provider Router)!")
    
    def create_email_sequence(self, topic: str, num_emails: int = 3) -> str:
        """
        Create an email nurture sequence
        
        Args:
            topic: What the email sequence is about
            num_emails: Number of emails in sequence
            
        Returns:
            Complete email sequence
        """
        print(f"\n📧 Creating {num_emails}-email sequence about: {topic}")
        
        prompt = f"""You are a senior email marketing strategist. Create a {num_emails}-email nurture sequence for the following topic.

Topic: {topic}
Number of Emails: {num_emails}

RESPONSE FORMAT:
Present email/CRM recommendations conversationally. Suggest specific sequences with subject lines, timing, and expected engagement. Explain the strategy behind each step.
End with: "**Next step:** [specific action]"
""" + AGENT_CONVERSATIONAL_RULES

        try:
            result_data = call_model_sync(prompt=prompt, tier=2, max_tokens=2000, temperature=0.7)
            result = result_data["content"]
            print("✅ Email sequence created!")
            return result

        except Exception as e:
            error_msg = f"❌ Error creating sequence: {str(e)}"
            print(error_msg)
            return error_msg

    def write_single_email(self, purpose: str) -> str:
        """
        Write a single email

        Args:
            purpose: Purpose of the email

        Returns:
            Complete email
        """
        print(f"\n✉️ Writing email: {purpose}")

        prompt = f"""You are an expert email copywriter. Write a professional email for this purpose: {purpose}

Include:
- Compelling subject line
- Professional greeting
- Engaging body (150-200 words)
- Clear call-to-action
- Professional closing

Write the email now:"""

        try:
            result_data = call_model_sync(prompt=prompt, tier=1, max_tokens=1000, temperature=0.7)
            result = result_data["content"]
            print("✅ Email written!")
            return result

        except Exception as e:
            error_msg = f"❌ Error writing email: {str(e)}"
            print(error_msg)
            return error_msg


# Simplified functions for easy use
def create_email_sequence(topic: str, num_emails: int = 3) -> str:
    """Create email nurture sequence"""
    agent = CRMAgent()
    return agent.create_email_sequence(topic, num_emails)


def write_single_email(purpose: str) -> str:
    """Write a single email"""
    agent = CRMAgent()
    return agent.write_single_email(purpose)


# ==============================================================
# REAL EXECUTION LAYER — SwarmOps Upgrade
# Sends emails and manages contacts via HubSpot.
# Falls back to text-only mode if HubSpot is not configured.
# ==============================================================


def get_real_contacts(limit=100, filter_by=None):
    """
    Pull real contacts from HubSpot CRM.
    filter_by: optional dict like {'property': 'lifecyclestage', 'value': 'lead'}
    Returns: list[dict] or None
    """
    try:
        from integrations.hubspot import HubSpot

        hs = HubSpot()
        if not hs.available:
            print("⚠️  HubSpot not configured — strategy-only mode.")
            return None

        print("\n📡 Pulling contacts from HubSpot...")
        fp = fv = None
        if filter_by and isinstance(filter_by, dict):
            fp = filter_by.get("property")
            fv = filter_by.get("value")

        contacts = hs.get_contacts(limit=limit, filter_property=fp, filter_value=fv)
        if contacts:
            print(f"✅ Retrieved {len(contacts)} contacts")
        return contacts or []

    except Exception as e:
        print(f"❌ Get contacts error: {e}")
        return None


def send_real_email(contact_id, email_template_id, template_variables=None):
    """
    Send a REAL email via HubSpot.

    Args:
        contact_id: HubSpot contact ID
        email_template_id: HubSpot email template ID
        template_variables: optional dict of template vars
    Returns: dict or None
    """
    try:
        from integrations.hubspot import HubSpot

        hs = HubSpot()
        if not hs.available:
            print("⚠️  HubSpot not configured — cannot send emails.")
            return None

        print(f"\n📤 Sending email to contact {contact_id}...")
        result = hs.send_email(
            contact_id=contact_id,
            email_id=email_template_id,
            email_properties=template_variables,
        )
        if result:
            print("✅ Email sent!")
        return result

    except Exception as e:
        print(f"❌ Send email error: {e}")
        return None


def add_contact_to_hubspot(email, first_name="", last_name="", company="", **extra):
    """
    Add a new contact to HubSpot CRM.
    Returns: {id, email, status} or None
    """
    try:
        from integrations.hubspot import HubSpot

        hs = HubSpot()
        if not hs.available:
            print("⚠️  HubSpot not configured.")
            return None

        print(f"\n👤 Adding contact: {email}")
        result = hs.create_contact(
            email=email, first_name=first_name, last_name=last_name, company=company, **extra
        )
        if result:
            print(f"✅ Contact added! ID: {result.get('id', 'N/A')}")
        return result

    except Exception as e:
        print(f"❌ Add contact error: {e}")
        return None


def get_real_email_performance():
    """Get real email marketing stats from HubSpot. Returns: dict or None"""
    try:
        from integrations.hubspot import HubSpot

        hs = HubSpot()
        if not hs.available:
            print("⚠️  HubSpot not configured.")
            return None

        print("\n📊 Pulling email stats from HubSpot...")
        stats = hs.get_email_stats()
        if stats:
            print("✅ Email stats retrieved!")
        return stats

    except Exception as e:
        print(f"❌ Email performance error: {e}")
        return None


# Test the agent
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING CRM AGENT (GROQ)")
    print("="*60)
    
    # Test 1: Single email
    print("\n--- Test 1: Single Email ---")
    email = write_single_email("Welcome new customers to our SaaS platform")
    print(email[:300] + "...")
    
    # Test 2: Email sequence
    print("\n--- Test 2: Email Sequence ---")
    sequence = create_email_sequence("onboarding for project management tool", num_emails=3)
    print(sequence[:400] + "...")
    
    print("\n✅ CRM Agent test complete!")