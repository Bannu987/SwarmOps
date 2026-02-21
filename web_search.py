"""
Web Search Utility - Using Brave Search API
Provides high-quality web search capabilities to agents
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class WebSearch:
    """
    Web search using Brave Search API
    Free tier: 2,000 queries/month
    """
    
    def __init__(self):
        """Initialize Brave Search with API key"""
        self.api_key = os.getenv('BRAVE_API_KEY')
        
        if not self.api_key:
            raise ValueError("BRAVE_API_KEY not found in .env file!")
        
        self.base_url = "https://api.search.brave.com/res/v1/web/search"
        print("🔍 Web Search initialized (Brave Search)")
    
    def search(self, query, max_results=5):
        """
        Search the web using Brave Search API
        
        Args:
            query (str): The search query
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of search results with title, url, and description
        """
        try:
            print(f"🔎 Searching: '{query}'")
            
            # Prepare request
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.api_key
            }
            
            params = {
                "q": query,
                "count": max_results
            }
            
            # Make request
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params
            )
            
            # Check if successful
            if response.status_code != 200:
                print(f"❌ Search failed: {response.status_code}")
                return []
            
            # Parse results
            data = response.json()
            web_results = data.get('web', {}).get('results', [])
            
            # Format results
            formatted_results = []
            for i, result in enumerate(web_results[:max_results], 1):
                formatted_results.append({
                    'rank': i,
                    'title': result.get('title', 'No title'),
                    'url': result.get('url', ''),
                    'description': result.get('description', 'No description')
                })
            
            print(f"✅ Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def search_and_summarize(self, query, max_results=3):
        """
        Search and return a text summary of results
        
        Args:
            query (str): The search query
            max_results (int): Maximum number of results
            
        Returns:
            str: Formatted text summary of search results
        """
        results = self.search(query, max_results)
        
        if not results:
            return "No results found."
        
        # Create summary
        summary = f"Search Results for: '{query}'\n\n"
        
        for result in results:
            summary += f"{result['rank']}. {result['title']}\n"
            summary += f"   {result['description']}\n"
            summary += f"   URL: {result['url']}\n\n"
        
        return summary
    
    def get_news(self, query, max_results=5):
        """
        Search for news articles
        
        Args:
            query (str): Search query
            max_results (int): Maximum results
            
        Returns:
            list: News results
        """
        try:
            print(f"📰 Searching news: '{query}'")
            
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.api_key
            }
            
            params = {
                "q": query,
                "count": max_results,
                "freshness": "day"  # Recent news only
            }
            
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            news_results = data.get('news', {}).get('results', [])
            
            formatted_results = []
            for i, result in enumerate(news_results[:max_results], 1):
                formatted_results.append({
                    'rank': i,
                    'title': result.get('title', 'No title'),
                    'url': result.get('url', ''),
                    'description': result.get('description', ''),
                    'age': result.get('age', 'Unknown')
                })
            
            print(f"✅ Found {len(formatted_results)} news results")
            return formatted_results
            
        except Exception as e:
            print(f"❌ News search error: {e}")
            return []


# Test Brave Search
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING BRAVE SEARCH")
    print("="*60)
    
    try:
        # Create search instance
        search = WebSearch()
        
        # Test basic search
        print("\n--- Test 1: Basic Search ---")
        results = search.search("AI trends 2025", max_results=3)
        
        if results:
            print(f"\nFound {len(results)} results:")
            for r in results:
                print(f"\n{r['rank']}. {r['title']}")
                print(f"   {r['description'][:100]}...")
                print(f"   {r['url']}")
        else:
            print("No results found!")
        
        # Test summarize
        print("\n--- Test 2: Search and Summarize ---")
        summary = search.search_and_summarize("email marketing tips", max_results=3)
        print(summary)
        
        # Test news search
        print("\n--- Test 3: News Search ---")
        news = search.get_news("artificial intelligence", max_results=3)
        
        if news:
            print(f"\nFound {len(news)} news articles:")
            for n in news:
                print(f"\n{n['rank']}. {n['title']}")
                print(f"   Age: {n['age']}")
                print(f"   {n['url']}")
        
        print("\n" + "="*60)
        print("✅ Brave Search test complete!")
        print("="*60)
        
    except ValueError as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure you:")
        print("1. Have BRAVE_API_KEY in your .env file")
        print("2. The API key is correct")
        print("3. You're in the SwarmOps folder")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")