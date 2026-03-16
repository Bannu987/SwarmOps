"""
SEO Agent - Multi-Provider SEO Expert
Uses model_router (multi-provider AI) + Web Search for SEO analysis
"""

import os
from dotenv import load_dotenv
from web_search import WebSearch
from model_router import call_model_sync

# Load environment variables
load_dotenv()

print("🔧 Initializing SEO Agent...")
search = WebSearch()
print("✅ SEO Agent ready! (Multi-Provider Router)")

# ---------------------------------------------------------------------------
# AGENT CONVERSATIONAL RULES — appended to all prompts
# ---------------------------------------------------------------------------
AGENT_CONVERSATIONAL_RULES = """
RULES (follow these above all other instructions):
1. Answer the user's question immediately. Never delay with setup requests.
2. Say "you/your", never "we/our". You advise the business, you are not the business.
3. Never invent data. If no website has been analyzed, give general best practices.
4. Never fabricate percentages. Only use numbers from real user data.
5. Keep responses to 4-8 sentences. Use bullet lists (3-5 items) for recommendations.
6. Be specific. "Write a guide on 'SEO audit checklist'" not "improve your SEO".
7. No consulting templates or section headers. Write conversationally.
"""

# SEO Analysis Prompt
seo_analysis_template = AGENT_CONVERSATIONAL_RULES + """You are a senior SEO strategist. Analyze the task and search results below, then provide specific, actionable keyword and SEO recommendations.

Task: {task}
Search Results: {search_results}

RESPONSE FORMAT:
Present keyword findings conversationally. Lead with the top 3 opportunities and explain WHY each matters for this brand. Include search intent and competition level in natural language.
Example: "Your highest-opportunity keyword is [keyword] — it has strong commercial intent and aligns with your positioning. Competition is moderate, making it achievable within 3-6 months."
End with: "**Next step:** [specific action]"
"""

def _seo_call(prompt_text, tier=2, max_tokens=4096, temperature=0.7):
    """Route through model_router with automatic fallback."""
    result = call_model_sync(prompt=prompt_text, tier=tier, max_tokens=max_tokens, temperature=temperature)
    return result["content"]


def analyze_seo(topic, num_results=5):
    """
    Comprehensive SEO analysis for a topic
    
    Args:
        topic (str): The topic/niche to analyze
        num_results (int): Number of search results to analyze
        
    Returns:
        dict: SEO analysis with keywords, opportunities, and recommendations
    """
    print(f"\n🔍 SEO Agent analyzing: '{topic}'")
    print(f"📡 Step 1: Researching SEO landscape...")
    
    # Search for SEO-related queries
    queries = [
        f"{topic} keywords",
        f"{topic} SEO",
        f"best {topic} content"
    ]
    
    all_results = []
    for query in queries:
        results = search.search(query, max_results=3)
        all_results.extend(results)
    
    if not all_results:
        return {
            'topic': topic,
            'analysis': "Unable to gather SEO data. Please try a different topic."
        }
    
    # Format search results
    formatted_results = ""
    for i, result in enumerate(all_results, 1):
        formatted_results += f"\n{i}. {result['title']}\n"
        formatted_results += f"   {result['description']}\n"
        formatted_results += f"   URL: {result['url']}\n"
    
    print(f"✅ Gathered {len(all_results)} data points")
    print(f"🤖 Step 2: Analyzing with Gemini AI...")
    
    # Analyze with AI (tier 4 = deep research)
    task = f"Perform comprehensive SEO analysis for: {topic}"
    full_prompt = seo_analysis_template.format(task=task, search_results=formatted_results)
    analysis = _seo_call(full_prompt, tier=4)
    
    print(f"✅ SEO analysis complete!")
    
    return {
        'topic': topic,
        'num_sources': len(all_results),
        'analysis': analysis
    }


def find_keywords(topic, num_keywords=10):
    """
    Find keyword opportunities for a topic
    
    Args:
        topic (str): The topic to find keywords for
        num_keywords (int): Target number of keywords
        
    Returns:
        str: List of keywords with analysis
    """
    print(f"\n🔑 Finding keywords for: '{topic}'")
    
    # Search for keyword-related content
    query = f"{topic} keywords SEO"
    results = search.search(query, max_results=5)
    
    if not results:
        print("⚠️  Search unavailable — using AI knowledge base for keyword research")
        formatted_results = "(No live search data available — generate keywords from your training knowledge and industry expertise)"
    else:
        # Format for LLM
        formatted_results = "\n".join([
            f"- {r['title']}: {r['description']}"
            for r in results
        ])
    
    # Check memory for past keyword research on this topic
    past_context = ""
    try:
        from memory_store import get_memory_store
        past = get_memory_store().search_memories("seo", topic, limit=3)
        if past:
            past_lines = "\n".join(f"  - {m['content']}" for m in past)
            past_context = f"\n\nPREVIOUS KEYWORD RESEARCH:\n{past_lines}\nFind NEW angles and keywords we haven't targeted yet.\n"
    except Exception:
        pass

    keyword_prompt = AGENT_CONVERSATIONAL_RULES + f"""You are a senior SEO strategist. Find keyword opportunities for the topic below.

Task: Find {num_keywords} keyword opportunities for {topic}
Search Results: {formatted_results}
{past_context}

RESPONSE FORMAT:
Present keyword findings conversationally. Lead with the top 3 opportunities and explain WHY each matters. Include search intent and competition level in natural language.
Example: "Your highest-opportunity keyword is [keyword] — it has strong commercial intent and aligns with your positioning. Competition is moderate, making it achievable within 3-6 months."
End with: "**Next step:** [specific action]"
"""

    result = _seo_call(keyword_prompt, tier=2)

    print(f"✅ Found keyword opportunities!")
    return result


def competitor_analysis(niche, num_competitors=5):
    """
    Analyze top competitors in a niche
    
    Args:
        niche (str): The niche/industry to analyze
        num_competitors (int): Number of competitors to analyze
        
    Returns:
        str: Competitor analysis report
    """
    print(f"\n🎯 Analyzing competitors in: '{niche}'")
    
    # Search for top players
    query = f"best {niche} websites top companies"
    results = search.search(query, max_results=num_competitors)
    
    if not results:
        return "No competitor data found."
    
    # Format competitor data
    competitor_data = "\n".join([
        f"{r['rank']}. {r['title']}\n   URL: {r['url']}\n   {r['description']}"
        for r in results
    ])
    
    analysis_prompt = AGENT_CONVERSATIONAL_RULES + f"""You are a senior SEO strategist. Analyze top competitors in the {niche} space.

Task: Analyze top {num_competitors} competitors in the {niche} space
Competitors Data: {competitor_data}

RESPONSE FORMAT:
Present competitor analysis conversationally. Highlight each competitor's key strengths, target keywords, and where gaps exist for differentiation. Be specific and actionable.
End with: "**Next step:** [specific action]"
"""

    result = _seo_call(analysis_prompt, tier=4)

    print(f"✅ Competitor analysis complete!")
    return result


def content_gap_analysis(topic):
    """
    Find content gaps and opportunities
    
    Args:
        topic (str): The topic to analyze
        
    Returns:
        str: Content gap analysis
    """
    print(f"\n📝 Finding content gaps for: '{topic}'")
    
    # Search for existing content
    query = f"{topic} guide tutorial how to"
    results = search.search(query, max_results=5)
    
    if not results:
        return "Unable to analyze content gaps."
    
    existing_content = "\n".join([
        f"- {r['title']}: {r['description'][:100]}..."
        for r in results
    ])
    
    gap_prompt = AGENT_CONVERSATIONAL_RULES + f"""You are a senior SEO strategist. Identify content gaps and opportunities for the topic below.

Task: Identify content gaps and opportunities for {topic}
Existing Content: {existing_content}

RESPONSE FORMAT:
Present content gap findings conversationally. Highlight underserved questions and topics, recommend specific content formats, and explain the traffic potential for each gap.
End with: "**Next step:** [specific action]"
"""

    result = _seo_call(gap_prompt, tier=2)

    print(f"✅ Content gap analysis complete!")
    return result


# ==============================================================
# REAL DATA LAYER — SwarmOps Upgrade
# Pulls LIVE data from Google Search Console + DataForSEO.
# Falls back to web-search mode if not configured.
# ==============================================================


def get_real_rankings(days=28):
    """
    Pull actual keyword rankings from Google Search Console.
    Returns: dict{queries, pages, opportunities, report} or None
    """
    try:
        from integrations.google_search_console import GoogleSearchConsole

        gsc = GoogleSearchConsole()

        if not gsc.available:
            print("⚠️  Search Console not configured — use analyze_seo() for web-search mode.")
            return None

        print("\n📡 Pulling real rankings from Google Search Console...")

        queries = gsc.get_top_queries(days=days, limit=50)
        pages = gsc.get_page_rankings(days=days, limit=50)
        opportunities = gsc.get_keyword_opportunities(days=days)

        report = "=== REAL SEARCH PERFORMANCE ===\n"
        if queries:
            report += "\nTOP KEYWORDS (by clicks):\n"
            for q in queries[:15]:
                report += (
                    f"  #{q['position']} | {q['query']} | "
                    f"{q['clicks']} clicks | {q['impressions']} impressions | {q['ctr']}% CTR\n"
                )
        if pages:
            report += "\nTOP PAGES (by clicks):\n"
            for p in pages[:10]:
                report += f"  {p['url']} | {p['clicks']} clicks | Avg pos: {p['position']}\n"
        if opportunities:
            report += "\nKEYWORD OPPORTUNITIES (high impressions, low clicks):\n"
            for o in opportunities[:10]:
                report += (
                    f"  🎯 \"{o['query']}\" | {o['impressions']} impressions | "
                    f"Pos: {o['position']} | Score: {o['opportunity_score']}\n"
                )

        print("✅ Real rankings pulled!")
        print(report)
        return {"queries": queries, "pages": pages, "opportunities": opportunities, "report": report}

    except Exception as e:
        print(f"❌ Real rankings error: {e}")
        return None


def get_real_keyword_data(keyword, location_code="2840"):
    """
    Get real search volume, competition, and CPC from DataForSEO.
    Returns: dict or None
    """
    try:
        from integrations.dataforseo import DataForSEO

        dfs = DataForSEO()

        if not dfs.available:
            print("⚠️  DataForSEO not configured — using web-search estimates.")
            return None

        print(f"\n📡 Pulling real data for: \"{keyword}\"")

        kw_data = dfs.get_keyword_data(keyword, location_code)
        related = dfs.get_related_keywords(keyword, location_code, limit=20)
        serp = dfs.get_serp_results(keyword, location_code)

        if kw_data:
            print(f"  Search Volume : {kw_data.get('search_volume', 0):,}")
            print(f"  Competition   : {kw_data.get('competition', 'N/A')}")
            print(f"  CPC           : ${kw_data.get('cpc', 0)}")

        return {"keyword": keyword, "data": kw_data, "related_keywords": related, "serp_results": serp}

    except Exception as e:
        print(f"❌ Real keyword data error: {e}")
        return None


def find_keyword_opportunities(topic, location_code="2840"):
    """
    Combined: Search Console gaps + DataForSEO volume.
    Returns real keyword targets with AI analysis.
    """
    try:
        from integrations.google_search_console import GoogleSearchConsole
        from integrations.dataforseo import DataForSEO

        gsc = GoogleSearchConsole()
        dfs = DataForSEO()

        if not gsc.available and not dfs.available:
            print("⚠️  Neither Search Console nor DataForSEO configured.")
            return find_keywords(topic)

        print(f"\n🔎 Finding real keyword opportunities for: \"{topic}\"")
        opportunities = []

        if gsc.available:
            gsc_opps = gsc.get_keyword_opportunities()
            if gsc_opps:
                print(f"  Search Console: {len(gsc_opps)} opportunities found")
                for o in gsc_opps[:10]:
                    opportunities.append({
                        "keyword": o["query"],
                        "source": "search_console",
                        "current_position": o["position"],
                        "impressions": o["impressions"],
                        "opportunity_score": o["opportunity_score"],
                        "note": "Already showing — optimize to rank higher",
                    })

        if dfs.available:
            related = dfs.get_related_keywords(topic, location_code, limit=30)
            if related:
                print(f"  DataForSEO: {len(related)} keywords found")
                for kw in related[:10]:
                    opportunities.append({
                        "keyword": kw["keyword"],
                        "source": "dataforseo",
                        "search_volume": kw["search_volume"],
                        "competition": kw["competition"],
                        "cpc": kw["cpc"],
                        "note": "New keyword target",
                    })

        opportunities.sort(
            key=lambda x: x.get("search_volume", 0) + x.get("opportunity_score", 0) * 100,
            reverse=True,
        )

        opps_text = "\n".join([
            f"  - {o['keyword']}: {o['note']} | "
            f"Volume: {o.get('search_volume', 'N/A')} | "
            f"Position: {o.get('current_position', 'N/A')}"
            for o in opportunities[:15]
        ])

        ai_analysis = find_keywords(
            f"{topic}\n\nReal data:\n{opps_text}"
        )

        print(f"✅ Found {len(opportunities)} real keyword opportunities!")
        return {"opportunities": opportunities, "ai_analysis": ai_analysis}

    except Exception as e:
        print(f"❌ Keyword opportunities error: {e}")
        return None


# Test the SEO Agent
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING SEO AGENT (GEMINI-POWERED)")
    print("="*60)
    
    try:
        # Test 1: Full SEO Analysis
        print("\n--- Test 1: Full SEO Analysis ---")
        test_topic = "organic coffee shop"
        result = analyze_seo(test_topic, num_results=3)
        
        print("\n" + "="*60)
        print("📊 SEO ANALYSIS REPORT")
        print("="*60)
        print(f"Topic: {result['topic']}")
        print(f"Data sources: {result['num_sources']}")
        print("\n" + "-"*60)
        print(result['analysis'])
        print("="*60)
        
        # Test 2: Keyword Research
        print("\n--- Test 2: Keyword Research ---")
        keywords = find_keywords("email marketing", num_keywords=8)
        print("\n" + "="*60)
        print("🔑 KEYWORD OPPORTUNITIES")
        print("="*60)
        print(keywords)
        print("="*60)
        
        # Test 3: Competitor Analysis
        print("\n--- Test 3: Competitor Analysis ---")
        competitors = competitor_analysis("sustainable fashion", num_competitors=3)
        print("\n" + "="*60)
        print("🎯 COMPETITOR ANALYSIS")
        print("="*60)
        print(competitors)
        print("="*60)
        
        # Test 4: Content Gap Analysis
        print("\n--- Test 4: Content Gap Analysis ---")
        gaps = content_gap_analysis("AI marketing tools")
        print("\n" + "="*60)
        print("📝 CONTENT GAP ANALYSIS")
        print("="*60)
        print(gaps)
        print("="*60)
        
        print("\n✅ All SEO Agent tests complete!")
        
    except ValueError as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure:")
        print("1. GEMINI_API_KEY is in your .env file")
        print("2. BRAVE_API_KEY is in your .env file")
        print("3. Both API keys are correct")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()