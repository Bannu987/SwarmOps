"""
Research Agent - Web-Powered Information Gatherer
Uses Brave Search + Ollama to research topics
"""

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from web_search import WebSearch

# Initialize Ollama for analysis
print("🔧 Initializing Research Agent...")
llm = OllamaLLM(model="llama3.2")
search = WebSearch()
print("✅ Research Agent ready!")

# Create research prompt template
research_template = """You are a research analyst who synthesizes web search results into clear, actionable insights.

Research Topic: {topic}

Web Search Results:
{search_results}

Please analyze these search results and provide:
1. A clear summary of the key findings (2-3 paragraphs)
2. The most important insights (3-5 bullet points)
3. Any actionable recommendations

Keep your response concise but comprehensive. Focus on the most relevant and recent information.

Your Analysis:"""

prompt = PromptTemplate(
    input_variables=["topic", "search_results"],
    template=research_template
)

# Create the research chain
research_chain = prompt | llm


def research_topic(topic, num_results=5):
    """
    Research a topic using web search + AI analysis
    
    Args:
        topic (str): The topic to research
        num_results (int): Number of search results to analyze
        
    Returns:
        dict: Research results with search data and analysis
    """
    print(f"\n🔬 Research Agent researching: '{topic}'")
    print(f"📡 Step 1: Searching the web...")
    
    # Step 1: Search the web
    search_results = search.search(topic, max_results=num_results)
    
    if not search_results:
        return {
            'topic': topic,
            'search_results': [],
            'analysis': "No search results found. Unable to research this topic."
        }
    
    # Step 2: Format search results for analysis
    formatted_results = ""
    for result in search_results:
        formatted_results += f"\n{result['rank']}. {result['title']}\n"
        formatted_results += f"   {result['description']}\n"
        formatted_results += f"   Source: {result['url']}\n"
    
    print(f"✅ Found {len(search_results)} sources")
    print(f"🤖 Step 2: Analyzing findings with AI...")
    
    # Step 3: Analyze with AI
    analysis = research_chain.invoke({
        "topic": topic,
        "search_results": formatted_results
    })
    
    print(f"✅ Research complete!")
    
    return {
        'topic': topic,
        'search_results': search_results,
        'analysis': analysis,
        'num_sources': len(search_results)
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