"""
Agent Helpers - Enable Agent-to-Agent Communication
Allows agents to call other agents directly without going through Nexus
"""

from research_agent import research_topic, quick_research
from seo_agent import find_keywords, analyze_seo, competitor_analysis
from content_agent import generate_content
from ppc_agent import create_campaign_strategy, write_ad_copy
from crm_agent import create_email_sequence, write_single_email
from analytics_agent import analyze_performance, calculate_roi

class AgentHelper:
    """
    Helper class that allows agents to communicate with each other
    Provides a unified interface for agent-to-agent calls
    """
    
    def __init__(self):
        """Initialize the agent helper"""
        print("🔗 Agent Helper initialized - Agents can now communicate!")
    
    # Research Agent helpers
    def get_research(self, topic, num_results=5):
        """
        Call Research Agent to get information
        
        Args:
            topic (str): Topic to research
            num_results (int): Number of sources
            
        Returns:
            dict: Research results
        """
        print(f"  📞 Calling Research Agent: '{topic}'")
        result = research_topic(topic, num_results)
        print(f"  ✅ Research Agent responded")
        return result
    
    def quick_search(self, query):
        """
        Quick research query
        
        Args:
            query (str): Quick search query
            
        Returns:
            str: Quick research result
        """
        print(f"  📞 Quick call to Research Agent: '{query}'")
        result = quick_research(query)
        print(f"  ✅ Research Agent responded")
        return result
    
    # SEO Agent helpers
    def get_keywords(self, topic, num_keywords=10):
        """
        Call SEO Agent to get keywords
        
        Args:
            topic (str): Topic for keywords
            num_keywords (int): Number of keywords
            
        Returns:
            str: Keywords
        """
        print(f"  📞 Calling SEO Agent for keywords: '{topic}'")
        result = find_keywords(topic, num_keywords)
        print(f"  ✅ SEO Agent responded with keywords")
        return result
    
    def get_seo_analysis(self, topic):
        """
        Call SEO Agent for full analysis
        
        Args:
            topic (str): Topic to analyze
            
        Returns:
            dict: SEO analysis
        """
        print(f"  📞 Calling SEO Agent for analysis: '{topic}'")
        result = analyze_seo(topic)
        print(f"  ✅ SEO Agent responded")
        return result
    
    def get_competitor_analysis(self, niche):
        """
        Call SEO Agent for competitor analysis
        
        Args:
            niche (str): Niche/market to analyze
            
        Returns:
            str: Competitor analysis
        """
        print(f"  📞 Calling SEO Agent for competitors: '{niche}'")
        result = competitor_analysis(niche)
        print(f"  ✅ SEO Agent responded")
        return result
    
    # Content Agent helpers
    def get_content(self, prompt):
        """
        Call Content Agent to generate content
        
        Args:
            prompt (str): Content generation prompt
            
        Returns:
            str: Generated content
        """
        print(f"  📞 Calling Content Agent")
        result = generate_content(prompt)
        print(f"  ✅ Content Agent responded")
        return result
    
    # PPC Agent helpers
    def get_ad_strategy(self, campaign_request, budget=None):
        """
        Call PPC Agent for campaign strategy
        
        Args:
            campaign_request (str): Campaign details
            budget (float): Optional budget
            
        Returns:
            str: Campaign strategy
        """
        print(f"  📞 Calling PPC Agent for strategy: '{campaign_request}'")
        result = create_campaign_strategy(campaign_request, budget)
        print(f"  ✅ PPC Agent responded")
        return result
    
    def get_ad_copy(self, product, audience=None, num_variations=5):
        """
        Call PPC Agent for ad copy
        
        Args:
            product (str): Product/service
            audience (str): Target audience
            num_variations (int): Number of variations
            
        Returns:
            str: Ad copy variations
        """
        print(f"  📞 Calling PPC Agent for ad copy: '{product}'")
        result = write_ad_copy(product, audience, num_variations)
        print(f"  ✅ PPC Agent responded")
        return result
    
    # CRM Agent helpers
    def get_email_sequence(self, purpose, num_emails=5, audience="general"):
        """
        Call CRM Agent for email sequence
        
        Args:
            purpose (str): Purpose of sequence
            num_emails (int): Number of emails
            audience (str): Target audience
            
        Returns:
            str: Email sequence
        """
        print(f"  📞 Calling CRM Agent for email sequence: '{purpose}'")
        result = create_email_sequence(purpose, num_emails, audience)
        print(f"  ✅ CRM Agent responded")
        return result
    
    def get_single_email(self, purpose, tone="professional", length="medium"):
        """
        Call CRM Agent for single email
        
        Args:
            purpose (str): Purpose of email
            tone (str): Email tone
            length (str): Email length
            
        Returns:
            str: Email content
        """
        print(f"  📞 Calling CRM Agent for email: '{purpose}'")
        result = write_single_email(purpose, tone, length)
        print(f"  ✅ CRM Agent responded")
        return result
    
    # Analytics Agent helpers
    def get_performance_analysis(self, description, data):
        """
        Call Analytics Agent for analysis
        
        Args:
            description (str): What to analyze
            data: The data to analyze
            
        Returns:
            str: Analysis
        """
        print(f"  📞 Calling Analytics Agent for analysis")
        result = analyze_performance(description, data)
        print(f"  ✅ Analytics Agent responded")
        return result
    
    def get_roi_analysis(self, investment, revenue, additional_metrics=None):
        """
        Call Analytics Agent for ROI calculation
        
        Args:
            investment (float): Investment amount
            revenue (float): Revenue amount
            additional_metrics (dict): Optional metrics
            
        Returns:
            str: ROI analysis
        """
        print(f"  📞 Calling Analytics Agent for ROI")
        result = calculate_roi(investment, revenue, additional_metrics)
        print(f"  ✅ Analytics Agent responded")
        return result


class SmartContentAgent:
    """
    Enhanced Content Agent that can call other agents when needed
    Example of agent-to-agent communication
    """
    
    def __init__(self):
        """Initialize with agent helper"""
        self.helper = AgentHelper()
        print("✨ Smart Content Agent initialized (can call other agents)")
    
    def create_seo_optimized_content(self, topic):
        """
        Create SEO-optimized content by calling SEO Agent first
        
        Args:
            topic (str): Topic to write about
            
        Returns:
            dict: Content with keywords and SEO data
        """
        print("\n📝 Smart Content Agent: Creating SEO-optimized content")
        print(f"Topic: {topic}")
        
        # Step 1: Get keywords from SEO Agent
        print("\n--- Getting SEO keywords ---")
        keywords = self.helper.get_keywords(topic, num_keywords=10)
        
        # Step 2: Create content using those keywords
        print("\n--- Creating optimized content ---")
        prompt = f"""Write SEO-optimized content about: {topic}

Use these keywords naturally throughout:
{keywords[:300]}

Create engaging, well-structured content."""
        
        content = self.helper.get_content(prompt)
        
        return {
            'keywords': keywords,
            'content': content,
            'topic': topic
        }
    
    def create_research_based_content(self, topic):
        """
        Create well-researched content by calling Research Agent first
        
        Args:
            topic (str): Topic to write about
            
        Returns:
            dict: Content with research
        """
        print("\n📝 Smart Content Agent: Creating research-based content")
        print(f"Topic: {topic}")
        
        # Step 1: Get research from Research Agent
        print("\n--- Gathering research ---")
        research = self.helper.get_research(topic, num_results=5)
        
        # Step 2: Create content using research
        print("\n--- Writing content based on research ---")
        prompt = f"""Based on this research:

{research['analysis'][:500]}

Write a comprehensive article about: {topic}

Use the research findings to create accurate, informative content."""
        
        content = self.helper.get_content(prompt)
        
        return {
            'research': research['analysis'],
            'content': content,
            'sources': research['num_sources']
        }
    
    def create_complete_content_package(self, topic):
        """
        Create a complete content package by coordinating multiple agents
        
        Args:
            topic (str): Topic for content package
            
        Returns:
            dict: Complete package with research, keywords, content, and email
        """
        print("\n📦 Smart Content Agent: Creating complete content package")
        print(f"Topic: {topic}")
        
        # Step 1: Research
        print("\n--- Step 1: Research ---")
        research = self.helper.get_research(topic, num_results=5)
        
        # Step 2: SEO Keywords
        print("\n--- Step 2: SEO Keywords ---")
        keywords = self.helper.get_keywords(topic, num_keywords=10)
        
        # Step 3: Main Content
        print("\n--- Step 3: Main Content ---")
        content_prompt = f"""Research: {research['analysis'][:300]}
Keywords: {keywords[:200]}

Write comprehensive content about: {topic}"""
        
        content = self.helper.get_content(content_prompt)
        
        # Step 4: Promotional Email
        print("\n--- Step 4: Promotional Email ---")
        email = self.helper.get_single_email(
            purpose=f"Promote new content about {topic}",
            tone="friendly and engaging",
            length="medium"
        )
        
        print("\n✅ Complete content package ready!")
        
        return {
            'topic': topic,
            'research': research['analysis'][:500] + "...",
            'keywords': keywords[:300] + "...",
            'content': content[:500] + "...",
            'promotional_email': email[:300] + "...",
            'package_complete': True
        }


# Test agent-to-agent communication
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING AGENT-TO-AGENT COMMUNICATION")
    print("="*60)
    
    # Test 1: Agent Helper
    print("\n--- Test 1: Basic Agent Helper ---")
    helper = AgentHelper()
    
    print("\n✅ Agent Helper can coordinate:")
    print("  - Research Agent")
    print("  - SEO Agent")
    print("  - Content Agent")
    print("  - PPC Agent")
    print("  - CRM Agent")
    print("  - Analytics Agent")
    
    # Test 2: Smart Content Agent
    print("\n--- Test 2: Smart Content Agent (Example Usage) ---")
    smart_agent = SmartContentAgent()
    
    print("\n✅ Smart Content Agent can:")
    print("  - Call SEO Agent for keywords")
    print("  - Call Research Agent for data")
    print("  - Call CRM Agent for emails")
    print("  - Coordinate multiple agents automatically")
    
    print("\n" + "="*60)
    print("✅ Agent-to-Agent Communication Ready!")
    print("="*60)
    
    print("\nExample usage:")
    print("  smart = SmartContentAgent()")
    print("  result = smart.create_complete_content_package('AI marketing')")