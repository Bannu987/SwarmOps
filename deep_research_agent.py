"""
Deep Research Agent - Intensive web research + reasoning model synthesis
Uses multi-step research workflow with search aggregation and Kimi K2.5 analysis
"""

import asyncio
import time
from typing import Dict, List, Any
from model_router import call_model, call_model_sync

class DeepResearchAgent:
    """
    Advanced research agent that performs comprehensive multi-source research
    combining web search with reasoning model analysis.

    5-Step Research Process:
    1. Generate 3 smart search queries (using Tier 1 fast model)
    2. Execute searches on Brave + Serper simultaneously
    3. Compile and deduplicate search results
    4. Deep analysis with Tier 4 reasoning model (Kimi K2.5)
    5. Return structured data with summary, findings, sources, recommendations
    """

    def __init__(self, brave_api_key: str = None, serper_api_key: str = None):
        self.name = "Deep Research Agent"
        self.brave_api_key = brave_api_key
        self.serper_api_key = serper_api_key
        print(f"🔬 Initializing {self.name}...")

        # Initialize search tools
        if brave_api_key:
            from langchain_community.tools import BraveSearch
            self.brave_search = BraveSearch.from_api_key(
                api_key=brave_api_key,
                search_kwargs={"count": 10}
            )
            print("✅ Brave Search initialized")
        else:
            self.brave_search = None
            print("⚠️  Brave Search not available (no API key)")

        self.serper_available = bool(serper_api_key)
        if serper_api_key:
            print("✅ Serper Search initialized")
        else:
            print("⚠️  Serper Search not available (no API key)")

        print(f"✅ {self.name} ready! (Multi-Provider Router)\n")

    async def generate_search_queries(self, topic: str) -> List[str]:
        """
        Step 1: Generate 3 smart, diverse search queries using Tier 1 model
        """
        prompt = f"""You are a research query generator. Generate 3 diverse, high-quality search queries to comprehensively research this topic:

TOPIC: {topic}

Requirements:
- Query 1: Broad overview query
- Query 2: Deep dive into specific aspect
- Query 3: Alternative angle or recent developments

Return ONLY the 3 queries, one per line, no numbering or explanation.
Example format:
organic dog food benefits 2026
best organic dog food brands comparison
organic dog food vs conventional nutrition study"""

        response = await call_model(
            prompt=prompt,
            tier=1,  # Fast model for query generation
        )

        # Parse queries from response
        content = response.get("content", "") if isinstance(response, dict) else str(response)
        queries = [q.strip() for q in content.strip().split('\n') if q.strip()]
        return queries[:3]  # Ensure exactly 3 queries

    async def search_brave(self, query: str) -> List[Dict[str, Any]]:
        """Execute Brave search and return results"""
        if not self.brave_search:
            return []

        try:
            results = await asyncio.to_thread(self.brave_search.run, query)
            # Parse Brave results (returns as string)
            parsed = []
            for item in results.split('\n\n'):
                if item.strip():
                    parts = item.split('\n', 2)
                    if len(parts) >= 3:
                        parsed.append({
                            'title': parts[0].replace('[', '').replace(']', '').strip(),
                            'url': parts[1].replace('(', '').replace(')', '').strip(),
                            'snippet': parts[2].strip() if len(parts) > 2 else '',
                            'source': 'brave'
                        })
            return parsed[:5]  # Top 5 results
        except Exception as e:
            print(f"⚠️  Brave search failed: {e}")
            return []

    async def search_serper(self, query: str) -> List[Dict[str, Any]]:
        """Execute Serper search and return results"""
        if not self.serper_available or not self.serper_api_key:
            return []

        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://google.serper.dev/search",
                    headers={"X-API-KEY": self.serper_api_key, "Content-Type": "application/json"},
                    json={"q": query, "num": 5},
                    timeout=10.0
                )
                data = response.json()

                results = []
                for item in data.get('organic', [])[:5]:
                    results.append({
                        'title': item.get('title', ''),
                        'url': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                        'source': 'serper'
                    })
                return results
        except Exception as e:
            print(f"⚠️  Serper search failed: {e}")
            return []

    async def execute_searches(self, queries: List[str]) -> List[Dict[str, Any]]:
        """
        Step 2: Execute all searches simultaneously on both engines
        """
        all_tasks = []

        for query in queries:
            if self.brave_search:
                all_tasks.append(self.search_brave(query))
            if self.serper_available:
                all_tasks.append(self.search_serper(query))

        # Run all searches in parallel
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        # Flatten and deduplicate
        all_results = []
        seen_urls = set()

        for result_set in results:
            if isinstance(result_set, list):
                for item in result_set:
                    if item['url'] not in seen_urls:
                        seen_urls.add(item['url'])
                        all_results.append(item)

        return all_results

    def compile_search_context(self, queries: List[str], results: List[Dict[str, Any]]) -> str:
        """
        Step 3: Compile search results into context for reasoning model
        """
        context = f"SEARCH QUERIES EXECUTED:\n"
        for i, q in enumerate(queries, 1):
            context += f"{i}. {q}\n"

        if not results:
            context += "\n\nSEARCH RESULTS: No live search data available.\n"
            context += "Use your training knowledge and industry expertise to provide comprehensive research.\n"
            return context

        context += f"\n\nSEARCH RESULTS ({len(results)} sources found):\n\n"

        for i, result in enumerate(results, 1):
            context += f"[{i}] {result['title']}\n"
            context += f"URL: {result['url']}\n"
            context += f"Snippet: {result['snippet']}\n"
            context += f"Source: {result['source']}\n\n"

        return context

    async def analyze_with_reasoning(self, topic: str, search_context: str) -> str:
        """
        Step 4: Deep analysis using Tier 4 reasoning model (Kimi K2.5)
        """
        prompt = f"""You are a research analyst. You've been given comprehensive search results on a topic. Analyze the information and provide a structured research report.

ORIGINAL TOPIC: {topic}

{search_context}

Provide a detailed analysis in this EXACT format:

## SUMMARY
[2-3 paragraph executive summary of findings]

## KEY FINDINGS
1. [First major finding with supporting evidence]
2. [Second major finding with supporting evidence]
3. [Third major finding with supporting evidence]
4. [Fourth major finding with supporting evidence]
5. [Fifth major finding with supporting evidence]

## SOURCES USED
[List the most relevant sources with [Title](URL) format]

## RECOMMENDATIONS
1. [First actionable recommendation]
2. [Second actionable recommendation]
3. [Third actionable recommendation]
4. [Fourth actionable recommendation]
5. [Fifth actionable recommendation]

## CONFIDENCE ASSESSMENT
[Rate your confidence 0.0-1.0 and explain reasoning gaps if any]"""

        response = await call_model(
            prompt=prompt,
            tier=4,  # Tier 4 = reasoning models (Kimi K2.5, DeepSeek R1)
        )

        content = response.get("content", "") if isinstance(response, dict) else str(response)
        return content

    def parse_analysis(self, analysis: str, queries: List[str], results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Step 5: Parse the reasoning model output into structured data
        """
        sections = {
            'summary': '',
            'key_findings': [],
            'sources': [],
            'recommendations': [],
            'confidence': 0.85
        }

        current_section = None
        current_content = []

        for line in analysis.split('\n'):
            line_stripped = line.strip()

            # Detect section headers
            if '## SUMMARY' in line_stripped.upper():
                current_section = 'summary'
                current_content = []
            elif '## KEY FINDINGS' in line_stripped.upper():
                if current_section == 'summary':
                    sections['summary'] = '\n'.join(current_content).strip()
                current_section = 'key_findings'
                current_content = []
            elif '## SOURCES' in line_stripped.upper():
                if current_section == 'key_findings':
                    sections['key_findings'] = self._parse_list_items(current_content)
                current_section = 'sources'
                current_content = []
            elif '## RECOMMENDATIONS' in line_stripped.upper():
                if current_section == 'sources':
                    sections['sources'] = self._parse_sources(current_content, results)
                current_section = 'recommendations'
                current_content = []
            elif '## CONFIDENCE' in line_stripped.upper():
                if current_section == 'recommendations':
                    sections['recommendations'] = self._parse_list_items(current_content)
                current_section = 'confidence'
                current_content = []
            else:
                # Add content to current section
                if line_stripped:
                    current_content.append(line_stripped)

        # Parse final section (confidence)
        if current_section == 'confidence':
            sections['confidence'] = self._parse_confidence(current_content)

        # Add metadata
        sections['search_queries_used'] = queries
        sections['total_sources_found'] = len(results)

        return sections

    def _parse_list_items(self, lines: List[str]) -> List[str]:
        """Parse numbered list items"""
        items = []
        for line in lines:
            # Remove numbering like "1.", "2)", etc
            cleaned = line
            if len(line) > 2 and line[0].isdigit() and line[1] in '.):':
                cleaned = line[2:].strip()
            elif line.startswith('- '):
                cleaned = line[2:].strip()
            if cleaned:
                items.append(cleaned)
        return items[:5]  # Max 5 items

    def _parse_sources(self, lines: List[str], search_results: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        """Parse sources and match with search results"""
        sources = []
        for result in search_results[:10]:  # Top 10 sources
            sources.append({
                'title': result['title'],
                'url': result['url'],
                'snippet': result['snippet'][:200] + '...' if len(result['snippet']) > 200 else result['snippet']
            })
        return sources

    def _parse_confidence(self, lines: List[str]) -> float:
        """Extract confidence score from text"""
        text = ' '.join(lines).lower()

        # Look for explicit score
        import re
        scores = re.findall(r'(\d+\.?\d*)', text)
        for score in scores:
            val = float(score)
            if 0 <= val <= 1:
                return val
            elif 0 <= val <= 100:
                return val / 100

        # Default based on keywords
        if 'high confidence' in text or 'very confident' in text:
            return 0.9
        elif 'moderate' in text or 'medium' in text:
            return 0.7
        elif 'low' in text:
            return 0.5

        return 0.8  # Default

    async def research(self, topic: str) -> Dict[str, Any]:
        """
        Main research method - executes full 5-step process

        Returns structured research data with:
        - summary: Executive summary
        - key_findings: List of 5 major findings
        - sources: List of source objects with title/url/snippet
        - recommendations: List of 5 actionable items
        - confidence: 0.0-1.0 score
        - search_queries_used: The queries that were executed
        - models_used: Which AI models were used
        - total_latency_ms: Total time taken
        """
        start_time = time.time()

        print(f"🔬 Starting deep research on: {topic}")

        # Step 1: Generate search queries
        print("📝 Step 1/5: Generating search queries...")
        queries = await self.generate_search_queries(topic)
        print(f"✅ Generated {len(queries)} queries: {queries}")

        # Step 2: Execute searches
        print(f"🔍 Step 2/5: Executing searches on {'Brave + Serper' if self.serper_available else 'Brave'}...")
        results = await self.execute_searches(queries)
        print(f"✅ Found {len(results)} unique sources")

        if not results:
            # Fall back to LLM-only research — don't fail the request
            print("⚠️  No search results — falling back to LLM knowledge base research")
            results = []

        # Step 3: Compile context
        print("📊 Step 3/5: Compiling search context...")
        search_context = self.compile_search_context(queries, results)

        # Step 4: Analyze with reasoning model
        print("🧠 Step 4/5: Analyzing with Kimi K2.5 reasoning model...")
        analysis = await self.analyze_with_reasoning(topic, search_context)

        # Step 5: Parse into structured data
        print("📋 Step 5/5: Parsing structured results...")
        structured_data = self.parse_analysis(analysis, queries, results)

        # Add metadata
        from model_router import get_last_call_info
        model_info = get_last_call_info()

        # Ensure required keys are always present
        structured_data.setdefault('summary', analysis[:500] if analysis else "Research complete.")
        structured_data.setdefault('key_findings', [])
        structured_data.setdefault('sources', [])
        structured_data.setdefault('recommendations', [])
        structured_data.setdefault('confidence', 0.7)

        structured_data['success'] = True
        structured_data['models_used'] = {
            'query_generation': 'groq/llama-3.3-70b (Tier 1)',
            'analysis': f"{model_info.get('provider', 'unknown')}/{model_info.get('model', 'unknown')} (Tier 4)"
        }
        structured_data['total_latency_ms'] = int((time.time() - start_time) * 1000)

        print(f"✅ Deep research complete! ({structured_data['total_latency_ms']}ms)")
        print(f"📊 Confidence: {structured_data['confidence']:.0%}")

        return structured_data


# Singleton instance
_deep_research_agent = None

def get_deep_research_agent(brave_api_key: str = None, serper_api_key: str = None):
    """Get or create the deep research agent singleton"""
    global _deep_research_agent
    if _deep_research_agent is None:
        _deep_research_agent = DeepResearchAgent(brave_api_key, serper_api_key)
    return _deep_research_agent
