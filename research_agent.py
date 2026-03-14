"""
Research Agent - Web-Powered Information Gatherer
Uses web search + model_router for multi-provider AI analysis
"""

import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from web_search import WebSearch
from model_router import call_model_sync

load_dotenv()

print("🔧 Initializing Research Agent...")
search = WebSearch()
print("✅ Research Agent ready! (Multi-Provider Router)")

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

# Create research prompt template
research_template = """You are a senior market researcher. Research the topic below and provide clear, actionable business insights.

Task: {topic}
Search Results: {search_results}

RESPONSE FORMAT:
Present research findings conversationally. Summarize key insights with business implications. Cite specific data points when available.
End with: "**Next step:** [specific action]"
""" + AGENT_CONVERSATIONAL_RULES

prompt = PromptTemplate(
    input_variables=["topic", "search_results"],
    template=research_template
)


def _groq_analyze(prompt_text):
    """Use model router (tier 4 = deep research) for analysis"""
    result = call_model_sync(prompt=prompt_text, tier=4, max_tokens=2000, temperature=0.7)
    return result["content"]


def research_topic(topic, num_results=5):
    """
    Research a topic using multi-angle web search + AI synthesis.
    Performs 3 searches from different angles to get comprehensive coverage.

    Args:
        topic (str): The topic to research
        num_results (int): Number of search results per query

    Returns:
        dict: Research results with search data and analysis
    """
    print(f"\n🔬 Research Agent researching: '{topic}'")
    print(f"📡 Step 1: Multi-angle web search (3 queries)...")

    # Multi-angle search: main topic + stats/data + competitive landscape
    search_queries = [
        topic,
        f"{topic} statistics data 2024 2025",
        f"{topic} best practices examples case study",
    ]

    all_results = []
    seen_urls = set()
    for i, query in enumerate(search_queries, 1):
        print(f"   Query {i}/3: {query}")
        results = search.search(query, max_results=max(3, num_results // 2))
        for r in results:
            url = r.get('url', '')
            if url not in seen_urls:
                seen_urls.add(url)
                all_results.append(r)

    if not all_results:
        return {
            'topic': topic,
            'search_results': [],
            'analysis': "No search results found. Unable to research this topic."
        }

    # Step 2: Format search results for analysis — group by query angle
    formatted_results = f"=== MAIN TOPIC RESULTS ===\n"
    for result in all_results[:num_results]:
        formatted_results += f"\n{result.get('rank', '?')}. {result['title']}\n"
        formatted_results += f"   {result['description']}\n"
        formatted_results += f"   Source: {result['url']}\n"

    if len(all_results) > num_results:
        formatted_results += f"\n=== ADDITIONAL SOURCES (stats + case studies) ===\n"
        for result in all_results[num_results:num_results + 6]:
            formatted_results += f"\n- {result['title']}\n"
            formatted_results += f"  {result['description']}\n"
            formatted_results += f"  Source: {result['url']}\n"

    print(f"✅ Found {len(all_results)} unique sources across 3 search angles")
    print(f"🤖 Step 2: Synthesizing with AI (Tier 4 deep research)...")

    # Check memory for past research on this topic
    past_context = ""
    try:
        from memory_store import get_memory_store
        past = get_memory_store().search_memories("research", topic, limit=3)
        if past:
            past_lines = "\n".join(f"  - {m['content']}" for m in past)
            past_context = f"\n\nPREVIOUS RESEARCH ON THIS TOPIC:\n{past_lines}\nBuild on this — find NEW angles not covered before.\n"
    except Exception:
        pass

    # Step 3: Analyze with AI
    filled_prompt = prompt.format(topic=topic, search_results=formatted_results) + past_context
    analysis = _groq_analyze(filled_prompt)

    print(f"✅ Research complete! ({len(all_results)} sources synthesized)")

    return {
        'topic': topic,
        'search_results': all_results,
        'analysis': analysis,
        'num_sources': len(all_results)
    }


def quick_research(question):
    """
    Quick research for simple questions
    
    Args:
        question (str): The question to research
        
    Returns:
        str: Simple answer based on search results
    """
    print(f"\n❓ Quick research: '{question}'")
    
    # Search with fewer results
    results = search.search(question, max_results=3)
    
    if not results:
        return "No information found."
    
    # Create simple summary
    summary = f"Based on recent web search:\n\n"
    
    for result in results:
        summary += f"• {result['title']}\n"
        summary += f"  {result['description'][:150]}...\n"
        summary += f"  (Source: {result['url']})\n\n"
    
    return summary


def research_news(topic, num_results=5):
    """
    Research recent news about a topic
    
    Args:
        topic (str): The topic to find news about
        num_results (int): Number of news articles to find
        
    Returns:
        str: Summary of news articles
    """
    print(f"\n📰 Researching news: '{topic}'")
    
    # Get news results
    news_results = search.get_news(topic, max_results=num_results)
    
    if not news_results:
        return "No recent news found on this topic."
    
    # Format news summary
    summary = f"Recent News: {topic}\n\n"
    
    for article in news_results:
        summary += f"{article['rank']}. {article['title']}\n"
        summary += f"   Published: {article['age']}\n"
        summary += f"   {article['description']}\n"
        summary += f"   Read more: {article['url']}\n\n"
    
    return summary


# Test the research agent
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING RESEARCH AGENT")
    print("="*60)
    
    # Test 1: Full research
    print("\n--- Test 1: Full Topic Research ---")
    test_topic = "best AI tools for startups"
    result = research_topic(test_topic, num_results=3)
    
    print("\n" + "="*60)
    print("📊 RESEARCH REPORT")
    print("="*60)
    print(f"Topic: {result['topic']}")
    print(f"Sources analyzed: {result['num_sources']}")
    print("\n" + "-"*60)
    print("ANALYSIS:")
    print("-"*60)
    print(result['analysis'])
    print("="*60)
    
    # Test 2: Quick research
    print("\n--- Test 2: Quick Research ---")
    quick_question = "What is the best time to send marketing emails?"
    quick_result = quick_research(quick_question)
    print(quick_result)
    
    # Test 3: News research
    print("\n--- Test 3: News Research ---")
    news_topic = "artificial intelligence marketing"
    news_result = research_news(news_topic, num_results=3)
    print(news_result)
    
    print("="*60)
    print("✅ Research Agent test complete!")