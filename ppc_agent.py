"""
PPC Agent - Paid Advertising Specialist
Uses model_router (multi-provider AI) + Web Search for ad campaign strategy
"""

import os
from dotenv import load_dotenv
from web_search import WebSearch
from model_router import call_model_sync

# Load environment variables
load_dotenv()

print("🔧 Initializing PPC Agent...")
search = WebSearch()
print("✅ PPC Agent ready! (Multi-Provider Router)")

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
""" + """
RESPONSE QUALITY RULES:

LENGTH:
- Default: 4-8 sentences. Do not exceed this unless the user asks for a detailed plan, audit, or full analysis.
- Short questions → 2-4 sentences
- Normal requests → 4-8 sentences

FORMAT:
- Use short bullet lists (3-5 items) for recommendations.
- Each bullet = one specific, actionable sentence.
- Short numbered lists (1-5 items) are encouraged for clarity.

SPECIFICITY:
- Never give vague advice. Every recommendation must be specific.
- BAD: 'Improve your SEO' → GOOD: 'Write a guide targeting the keyword "AI marketing tools"'
- BAD: 'Create good content' → GOOD: 'Publish a case study on how AI tools increased client traffic by 40%'
- If you cannot be specific without more info, say exactly what info you need.

NO TEMPLATES:
- Avoid: 'Critical Issues', 'Strategic Roadmap', 'Heuristic Evaluation', 'Assessment Matrix', 'Action Architecture'
- Short numbered lists (1-5 items) ARE allowed and encouraged.
"""

# PPC Campaign Strategy Prompt
ppc_strategy_template = """You are a senior PPC strategist. Analyze the campaign request and research below, then provide specific, actionable paid advertising recommendations.

Request: {request}
Search Results: {search_results}

RESPONSE FORMAT:
Present PPC strategy conversationally. Recommend specific keywords, budget allocation, and ad copy ideas. Explain the reasoning behind each recommendation.
End with: "**Next step:** [specific action]"
""" + AGENT_CONVERSATIONAL_RULES

def _ppc_call(prompt_text, tier=2, max_tokens=4096, temperature=0.7):
    """Route through model_router with automatic fallback."""
    result = call_model_sync(prompt=prompt_text, tier=tier, max_tokens=max_tokens, temperature=temperature)
    return result["content"]


def create_campaign_strategy(campaign_request, budget=None):
    """
    Create a comprehensive PPC campaign strategy
    
    Args:
        campaign_request (str): Description of the campaign need
        budget (float): Optional budget constraint
        
    Returns:
        str: Detailed campaign strategy
    """
    print(f"\n💰 PPC Agent creating strategy for: '{campaign_request}'")
    
    if budget:
        print(f"💵 Budget constraint: ${budget}")
        campaign_request = f"{campaign_request} (Budget: ${budget})"
    
    print(f"📡 Researching competitive landscape...")
    
    # Research competitor ads and strategies
    search_query = f"{campaign_request} advertising strategy ppc ads"
    results = search.search(search_query, max_results=5)
    
    if not results:
        print("⚠️  Search unavailable — using AI knowledge base for PPC strategy")
        formatted_results = "(No live search data available — generate strategy from your training knowledge and industry benchmarks)"
    else:
        # Format search results
        formatted_results = "\n".join([
            f"{r['rank']}. {r['title']}\n   {r['description']}\n   {r['url']}"
            for r in results
        ])
    
    print(f"✅ Research complete")
    print(f"🤖 Generating campaign strategy with Gemini...")
    
    # Generate strategy (tier 3 = strategic reasoning)
    full_prompt = ppc_strategy_template.format(request=campaign_request, search_results=formatted_results)
    result = _ppc_call(full_prompt, tier=3)
    
    print(f"✅ Campaign strategy created!")
    return result


def write_ad_copy(product_or_service, target_audience=None, num_variations=5):
    """
    Generate ad copy variations
    
    Args:
        product_or_service (str): What's being advertised
        target_audience (str): Who the ads target
        num_variations (int): Number of ad variations to create
        
    Returns:
        str: Ad copy variations
    """
    print(f"\n✍️ Writing ad copy for: '{product_or_service}'")
    
    if target_audience:
        print(f"🎯 Target audience: {target_audience}")
    
    prompt = f"""Create {num_variations} Google Ads variations for: {product_or_service}

Target Audience: {target_audience or 'General audience'}

For each ad variation, provide:
- 3 headlines (max 30 characters each)
- 2 descriptions (max 90 characters each)
- 1 call-to-action

Format as:

**Ad Variation 1:**
Headlines:
1. [headline]
2. [headline]
3. [headline]

Descriptions:
1. [description]
2. [description]

CTA: [call-to-action]

Make each variation test different angles (price, quality, urgency, benefit, etc.)."""

    result = _ppc_call(prompt, tier=2)
    
    print(f"✅ Created {num_variations} ad variations!")
    return result


def suggest_targeting(business_type, location=None):
    """
    Suggest targeting parameters for a campaign
    
    Args:
        business_type (str): Type of business
        location (str): Geographic location
        
    Returns:
        str: Targeting recommendations
    """
    print(f"\n🎯 Generating targeting strategy for: '{business_type}'")
    
    # Research audience insights
    search_query = f"{business_type} target audience demographics"
    results = search.search(search_query, max_results=3)
    
    audience_data = "\n".join([
        f"- {r['title']}: {r['description'][:100]}..."
        for r in results
    ]) if results else "Limited audience data available"
    
    prompt = f"""Based on this audience research for {business_type}:

{audience_data}

Provide detailed targeting recommendations:

1. **Demographics:**
   - Age range
   - Gender split
   - Income level
   - Education level

2. **Geographic Targeting:**
   - Location: {location or 'Not specified - recommend optimal locations'}
   - Radius recommendations
   - Urban vs suburban vs rural

3. **Interests & Behaviors:**
   - Key interests to target
   - Online behaviors
   - Purchase intent signals

4. **Device & Platform:**
   - Desktop vs mobile split
   - Specific platforms (Google Search, Display, Facebook, Instagram, etc.)

5. **Timing:**
   - Best days of week
   - Best times of day
   - Seasonal considerations

Be specific and data-driven."""

    result = _ppc_call(prompt, tier=2)
    
    print(f"✅ Targeting strategy ready!")
    return result


def optimize_campaign(campaign_data):
    """
    Analyze campaign performance and suggest optimizations
    
    Args:
        campaign_data (str): Description of campaign performance
        
    Returns:
        str: Optimization recommendations
    """
    print(f"\n📊 Analyzing campaign for optimization...")
    
    prompt = f"""Campaign Performance Data:
{campaign_data}

As a PPC expert, provide:

1. **Performance Analysis:**
   - What's working well
   - What's underperforming
   - Key issues identified

2. **Immediate Actions:**
   - Top 3 changes to make today
   - Expected impact of each

3. **Testing Recommendations:**
   - What to A/B test
   - How to structure tests
   - What to measure

4. **Budget Optimization:**
   - Where to increase spend
   - Where to decrease/pause
   - Reallocation strategy

5. **Long-term Strategy:**
   - Scaling recommendations
   - New opportunities to explore

Be specific and prioritize actions by potential impact."""

    result = _ppc_call(prompt, tier=2)
    
    print(f"✅ Optimization plan ready!")
    return result


# ==============================================================
# REAL EXECUTION LAYER — SwarmOps Upgrade
# Creates and manages real Google Ads campaigns.
# Falls back to strategy-only mode if Google Ads is not configured.
# ==============================================================


def get_real_campaign_performance(days=30):
    """
    Pull LIVE campaign performance from Google Ads.
    Returns: list[dict] or None
    """
    try:
        from integrations.google_ads import GoogleAds

        ads = GoogleAds()
        if not ads.available:
            print("⚠️  Google Ads not configured — strategy-only mode.")
            return None

        print("\n📡 Pulling live campaign data from Google Ads...")
        performance = ads.get_campaign_performance(days=days)

        if performance:
            print(f"✅ Retrieved {len(performance)} campaigns")
            for c in performance:
                print(
                    f"  {c['name']}: {c['clicks']} clicks | "
                    f"{c['conversions']} conv | ${c['cost_usd']} spent | CPA: ${c['cpa_usd']}"
                )
        return performance

    except Exception as e:
        print(f"❌ Real campaign performance error: {e}")
        return None


def execute_campaign(campaign_name, daily_budget, keywords, headlines, descriptions, landing_url):
    """
    Create a REAL Google Ads search campaign.

    Args:
        campaign_name: Name for the campaign
        daily_budget: USD per day (e.g. 50.0)
        keywords: list of keyword strings
        headlines: list of up to 15 headlines (≤30 chars each)
        descriptions: list of up to 4 descriptions (≤90 chars each)
        landing_url: landing page URL
    Returns: dict with result
    """
    try:
        from integrations.google_ads import GoogleAds

        ads = GoogleAds()

        if not ads.available:
            print("⚠️  Google Ads not configured — generating strategy instead...")
            strategy = create_campaign_strategy(
                f"Campaign: {campaign_name} | Keywords: {', '.join(keywords)} | Budget: ${daily_budget}/day",
                budget=daily_budget,
            )
            return {
                "status": "strategy_only",
                "strategy": strategy,
                "note": "Connect Google Ads to execute campaigns.",
            }

        print(f"\n🚀 Creating Google Ads campaign: {campaign_name}")
        print(f"   Budget: ${daily_budget}/day | Keywords: {len(keywords)}")

        result = ads.create_search_campaign(
            name=campaign_name,
            daily_budget=daily_budget,
            keywords=keywords,
            ad_headlines=headlines,
            ad_descriptions=descriptions,
            final_url=landing_url,
        )

        if result:
            print("✅ Campaign created successfully!")
        return result or {"status": "error", "note": "Campaign creation failed."}

    except Exception as e:
        return {"status": "error", "error": str(e)}


def auto_optimize_campaigns(days=30):
    """
    Read real campaign data from Google Ads and run AI-powered optimization analysis.
    Returns: str — optimization recommendations based on live data
    """
    try:
        from integrations.google_ads import GoogleAds

        ads = GoogleAds()

        if not ads.available:
            print("⚠️  Google Ads not configured — cannot auto-optimize.")
            return optimize_campaign("No live data. Connect Google Ads for real optimization.")

        print("\n🤖 Auto-optimizing based on live Google Ads data...")

        performance = ads.get_campaign_performance(days=days)
        if not performance:
            return "No campaign data available."

        # Format for the AI
        perf_lines = []
        for c in performance:
            perf_lines.append(
                f"Campaign: {c['name']} | Clicks: {c['clicks']} | "
                f"Impressions: {c['impressions']} | Conversions: {c['conversions']} | "
                f"Cost: ${c['cost_usd']} | CPC: ${c['cpc_usd']} | CPA: ${c['cpa_usd']}"
            )

        perf_text = f"=== LIVE GOOGLE ADS DATA (last {days} days) ===\n" + "\n".join(perf_lines)
        return optimize_campaign(perf_text)

    except Exception as e:
        print(f"❌ Auto-optimize error: {e}")
        return None


# Test the PPC Agent
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING PPC AGENT")
    print("="*60)
    
    try:
        # Test 1: Campaign Strategy
        print("\n--- Test 1: Campaign Strategy ---")
        strategy = create_campaign_strategy(
            "organic coffee shop local marketing",
            budget=500
        )
        
        print("\n" + "="*60)
        print("💰 CAMPAIGN STRATEGY")
        print("="*60)
        print(strategy)
        print("="*60)
        
        # Test 2: Ad Copy
        print("\n--- Test 2: Ad Copy Generation ---")
        ad_copy = write_ad_copy(
            "organic fair-trade coffee beans",
            target_audience="health-conscious millennials",
            num_variations=3
        )
        
        print("\n" + "="*60)
        print("✍️ AD COPY VARIATIONS")
        print("="*60)
        print(ad_copy)
        print("="*60)
        
        # Test 3: Targeting
        print("\n--- Test 3: Targeting Strategy ---")
        targeting = suggest_targeting(
            "yoga studio",
            location="Los Angeles"
        )
        
        print("\n" + "="*60)
        print("🎯 TARGETING RECOMMENDATIONS")
        print("="*60)
        print(targeting)
        print("="*60)
        
        print("\n✅ All PPC Agent tests complete!")
        
    except ValueError as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure GEMINI_API_KEY is in your .env file")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()