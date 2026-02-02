"""
SEO Agent - Gemini-Powered SEO Expert
Uses Gemini AI + Web Search for SEO analysis and recommendations
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from web_search import WebSearch

# Load environment variables
load_dotenv()

# Initialize Gemini
print("🔧 Initializing SEO Agent...")
gemini_api_key = os.getenv('GEMINI_API_KEY')

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file!")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=gemini_api_key,
    temperature=0.7
)

search = WebSearch()
print("✅ SEO Agent ready! (Powered by Gemini)")

# SEO Analysis Prompt
seo_analysis_template = """You are an expert SEO consultant with deep knowledge of search engine optimization, keyword research, and content strategy.

Task: {task}

Web Search Results:
{search_results}

Based on these search results, provide:

1. **Keyword Analysis:**
   - List 5-10 relevant keywords with estimated search intent
   - Categorize by difficulty (Easy/Medium/Hard)
   - Note search volume indicators from the results

2. **Content Opportunities:**
   - What content gaps exist?
   - What topics are trending?
   - What questions are people asking?

3. **Competition Analysis:**
   - Who are the top-ranking competitors?
   - What are they doing well?
   - Where are the opportunities?

4. **Actionable Recommendations:**
   - Top 3 immediate actions to take
   - Long-term SEO strategy suggestions

Be specific, data-driven, and actionable. Format your response clearly with headers and bullet points.

Your SEO Analysis:"""

prompt = PromptTemplate(
    input_variables=["task", "search_results"],
    template=seo_analysis_template
)

# Create SEO analysis chain
seo_chain = prompt | llm


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
    
    # Analyze with Gemini
    task = f"Perform comprehensive SEO analysis for: {topic}"
    
    response = seo_chain.invoke({
        "task": task,
        "search_results": formatted_results
    })
    
    # Extract text from response
    analysis = response.content if hasattr(response, 'content') else str(response)
    
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
        return "No keyword data found."
    
    # Format for Gemini
    formatted_results = "\n".join([
        f"- {r['title']}: {r['description']}" 
        for r in results
    ])
    
    keyword_prompt = f"""Based on these search results about "{topic}":

{formatted_results}

Provide a list of {num_keywords} SEO keywords for {topic}, formatted as:

**Primary Keywords (High Priority):**
1. [keyword] - Search Intent: [intent] - Difficulty: [Easy/Medium/Hard]

**Secondary Keywords (Medium Priority):**
...

**Long-tail Keywords (Low Competition):**
...

Include realistic search volume estimates and practical difficulty assessments."""

    response = llm.invoke(keyword_prompt)
    result = response.content if hasattr(response, 'content') else str(response)
    
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
    
    analysis_prompt = f"""Analyze these top competitors in the {niche} space:

{competitor_data}

Provide:
1. **Market Leaders:** Who are the dominant players?
2. **Their Strengths:** What are they doing well (based on descriptions)?
3. **Content Strategy:** What topics/keywords are they targeting?
4. **Opportunities:** Where can a new entrant compete?
5. **Differentiation Strategy:** How to stand out in this market?

Be specific and actionable."""

    response = llm.invoke(analysis_prompt)
    result = response.content if hasattr(response, 'content') else str(response)
    
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
    
    gap_prompt = f"""Based on existing content about "{topic}":

{existing_content}

Identify:
1. **Content Gaps:** What topics are NOT well covered?
2. **Underserved Questions:** What questions aren't being answered?
3. **Content Opportunities:** What new angles/approaches could work?
4. **Content Ideas:** 5 specific blog post titles that fill these gaps
5. **Format Suggestions:** What content formats would work best (guides, videos, infographics)?

Be creative and specific."""

    response = llm.invoke(gap_prompt)
    result = response.content if hasattr(response, 'content') else str(response)
    
    print(f"✅ Content gap analysis complete!")
    return result


# ==============================================================
# REAL DATA LAYER — MarketingOS 2.0 Upgrade
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