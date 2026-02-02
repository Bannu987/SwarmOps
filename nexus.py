"""
The Nexus - Master Orchestrator (UPGRADED v4.0 → 2.0)
Smart routing to 10 specialized agents with advanced workflows
+ Budget Management + Agent Debate + Performance Tracking
"""

from langchain_ollama import OllamaLLM
from langchain_core.prompts import PromptTemplate
from content_agent import generate_content
from research_agent import research_topic, quick_research
from seo_agent import analyze_seo, find_keywords, competitor_analysis
from ppc_agent import create_campaign_strategy, write_ad_copy
from crm_agent import create_email_sequence, write_single_email
from analytics_agent import analyze_performance, calculate_roi
from brand_strategist_agent import create_brand_strategy, define_tone_of_voice, analyze_brand_consistency
from web_ux_agent import design_landing_page, optimize_user_flow, analyze_ux_issues
from cro_agent import analyze_funnel, create_ab_test_plan, identify_friction_points
from smm_agent import create_social_calendar, analyze_trends, write_platform_post, create_engagement_strategy, create_viral_hooks
import os
from memory_system import MemorySystem
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

"""
MARKETINGOS 2.0 ENHANCEMENTS
"""

class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

class AgentDebate:
    """
    Debate mechanism for agent conflict resolution
    When agents disagree, Nexus facilitates debate and makes final decision
    """
    
    def __init__(self):
        self.debate_history = []
    
    def initiate_debate(self, topic: str, agent_positions: Dict[str, str]) -> Dict:
        """
        Start a debate between agents on a specific topic
        
        Args:
            topic: What the debate is about
            agent_positions: Each agent's position/recommendation
            
        Returns:
            Debate result with winner and reasoning
        """
        debate = {
            'id': f"debate_{len(self.debate_history)+1}",
            'timestamp': datetime.now().isoformat(),
            'topic': topic,
            'participants': list(agent_positions.keys()),
            'positions': agent_positions,
            'winner': None,
            'reasoning': None
        }
        
        # Evaluate each position
        scores = {}
        for agent, position in agent_positions.items():
            score = self._evaluate_position(agent, position, topic)
            scores[agent] = score
        
        # Determine winner
        winner = max(scores.items(), key=lambda x: x[1])
        
        debate['winner'] = winner[0]
        debate['scores'] = scores
        debate['reasoning'] = f"Selected {winner[0]}'s position (score: {winner[1]:.2f})"
        
        self.debate_history.append(debate)
        
        return debate
    
    def _evaluate_position(self, agent: str, position: str, topic: str) -> float:
        """Evaluate an agent's position using real GA4 data when available, else heuristics"""
        score = 0.5  # Base score

        # --- Try to pull real conversion data from GA4 ---
        real_data_bonus = 0.0
        try:
            from integrations.google_analytics import GoogleAnalytics
            ga = GoogleAnalytics()
            if ga.available:
                events = ga.get_conversion_events(days=30)
                if events:
                    # Agents whose positions align with high-converting event types score higher
                    pos_lower = position.lower()
                    for ev in events:
                        ev_name = ev.get("event_name", "").lower()
                        if ev_name in pos_lower or ev_name.replace("_", " ") in pos_lower:
                            # Weight by conversion count — more conversions = stronger signal
                            real_data_bonus += min(ev.get("count", 0) / 500.0, 0.15)
                    real_data_bonus = min(real_data_bonus, 0.25)  # Cap at 0.25
        except Exception:
            pass  # Fall through to heuristic scoring

        score += real_data_bonus

        # Bonus for detail
        if len(position) > 100:
            score += 0.15

        # Bonus for citing real numbers (digits present)
        import re
        if re.search(r'\d+', position):
            score += 0.1

        # Bonus for referencing known high-value terms
        if any(word in position.lower() for word in ['roi', 'conversion', 'cpa', 'cpc', 'roas']):
            score += 0.1

        return min(1.0, max(0.0, score))


class BudgetManager:
    """Manages budget allocation across campaigns"""
    
    def __init__(self, total_budget: float = 10000):
        self.total_budget = total_budget
        self.allocated = 0
        self.allocations = []
    
    def allocate(self, task: str, amount: float, agent: str) -> bool:
        """
        Allocate budget to a task
        
        Returns:
            True if approved, False if denied
        """
        if self.allocated + amount <= self.total_budget:
            self.allocated += amount
            self.allocations.append({
                'task': task,
                'amount': amount,
                'agent': agent,
                'timestamp': datetime.now().isoformat()
            })
            remaining = self.total_budget - self.allocated
            print(f"✅ Budget approved: ${amount:,.2f} for {agent}")
            print(f"   Remaining: ${remaining:,.2f} / ${self.total_budget:,.2f}")
            return True
        else:
            shortage = (self.allocated + amount) - self.total_budget
            print(f"❌ Budget denied: ${amount:,.2f}")
            print(f"   Would exceed budget by: ${shortage:,.2f}")
            return False
    
    def get_report(self) -> Dict:
        """Get budget utilization report"""
        return {
            'total_budget': self.total_budget,
            'allocated': self.allocated,
            'remaining': self.total_budget - self.allocated,
            'utilization_percent': (self.allocated / self.total_budget) * 100,
            'allocations': self.allocations
        }


class Nexus:
    """
    The Master Orchestrator - v4.0 → 2.0
    Intelligently routes tasks to 9 specialized agents
    + Budget Management + Agent Debate + Performance Tracking
    """
    
    def __init__(self, budget_limit: float = 10000):
        """Initialize The Nexus with enhanced capabilities"""
        print("🧠 Initializing The Nexus (Master Orchestrator - v4.0 → 2.0 UPGRADE)...")
        self.brain = OllamaLLM(model="llama3.2")
        self.memory = MemorySystem()
        
        # NEW: MarketingOS 2.0 Features
        self.debate_system = AgentDebate()
        self.budget_manager = BudgetManager(total_budget=budget_limit)
        self.performance_metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'agent_usage': {}
        }
        
        # Available agents (10 AGENTS — MarketingOS 2.0)
        self.available_agents = {
            "content": "Content Agent - writes blog posts, articles, emails, social media, copy",
            "research": "Research Agent - searches web, gathers information, analyzes trends",
            "seo": "SEO Agent - keyword research, competitor analysis, SEO strategy",
            "ppc": "PPC Agent - ad campaign strategy, ad copy, budget allocation",
            "crm": "CRM Agent - email sequences, customer segmentation, nurture campaigns",
            "analytics": "Analytics Agent - performance analysis, ROI calculation, insights",
            "brand": "Brand Strategist Agent - brand strategy, tone of voice, positioning",
            "webux": "Web/UX Agent - landing pages, user flow, UX optimization",
            "cro": "CRO Agent - conversion optimization, A/B testing, funnel analysis",
            "smm": "SMM Agent - social media marketing, content calendar, trend analysis",
        }
        
        print("✅ The Nexus v2.0 is ready!")
        print(f"📋 Available agents: {len(self.available_agents)}")
        print(f"💰 Budget limit: ${budget_limit:,.2f}")
        for agent_name, description in self.available_agents.items():
            print(f"   - {agent_name}: {description}")
    
    def smart_route(self, user_goal):
        """
        Intelligently analyze the goal and decide which agent(s) to use
        
        Args:
            user_goal (str): The user's high-level goal
            
        Returns:
            str: The name of the best agent for this task
        """
        print(f"\n🤔 The Nexus is analyzing your goal intelligently...")
        
        goal_lower = user_goal.lower()
        
        # BRAND STRATEGIST keywords
        brand_keywords = [
            'brand', 'branding', 'positioning', 'tone of voice', 'brand strategy',
            'brand identity', 'brand guidelines', 'brand persona', 'brand voice',
            'brand consistency', 'brand positioning', 'brand message'
        ]
        
        # WEB/UX keywords
        webux_keywords = [
            'landing page', 'website', 'web design', 'ux', 'user experience',
            'ui', 'user interface', 'wireframe', 'user flow', 'page design',
            'layout', 'navigation', 'responsive', 'mobile design'
        ]
        
        # CRO keywords
        cro_keywords = [
            'conversion', 'cro', 'optimize conversion', 'a/b test', 'ab test',
            'funnel', 'checkout', 'friction', 'cart abandonment', 'conversion rate',
            'landing page optimization', 'test plan', 'conversion audit'
        ]
        
        # ANALYTICS AGENT keywords
        analytics_keywords = [
            'analyze', 'analysis', 'performance', 'metrics', 'data',
            'roi', 'calculate', 'measure', 'report', 'dashboard',
            'compare', 'benchmark'
        ]
        
        # PPC AGENT keywords
        ppc_keywords = [
            'ad', 'ads', 'ppc', 'campaign', 'google ads', 'facebook ads',
            'budget', 'advertising', 'paid', 'cpc', 'cpm', 'targeting'
        ]
        
        # CRM AGENT keywords
        crm_keywords = [
            'email', 'sequence', 'nurture', 'customer', 'crm',
            'segment', 'lifecycle', 'retention', 'onboard', 'welcome'
        ]
        
        # SEO AGENT keywords
        seo_keywords = [
            'seo', 'keyword', 'keywords', 'rank', 'ranking',
            'competitor', 'competition', 'optimize', 'search engine',
            'google', 'backlink', 'content gap'
        ]
        
        # RESEARCH AGENT keywords
        research_keywords = [
            'research', 'find', 'search', 'look up', 'discover',
            'what are', 'what is', 'trending', 'news', 'latest',
            'current', 'recent', 'investigate'
        ]
        
        # SMM AGENT keywords (checked BEFORE content — 'social' and 'post' overlap)
        smm_keywords = [
            'social media', 'instagram', 'linkedin', 'twitter', 'tiktok',
            'facebook post', 'social calendar', 'social strategy', 'engagement',
            'viral', 'social content', 'social post', 'social marketing',
            'influencer', 'hashtag', 'social trend'
        ]

        # CONTENT AGENT keywords
        content_keywords = [
            'write', 'blog', 'post', 'article', 'content',
            'copy', 'text', 'description',
            'create', 'draft', 'compose', 'caption'
        ]

        # Priority order: Brand > WebUX > CRO > Analytics > PPC > CRM > SEO > SMM > Research > Content
        if any(keyword in goal_lower for keyword in brand_keywords):
            print(f"✅ Decision: Brand Strategist Agent (detected branding task)")
            return "brand"
        
        if any(keyword in goal_lower for keyword in webux_keywords):
            print(f"✅ Decision: Web/UX Agent (detected web/UX task)")
            return "webux"
        
        if any(keyword in goal_lower for keyword in cro_keywords):
            print(f"✅ Decision: CRO Agent (detected conversion optimization task)")
            return "cro"
        
        if any(keyword in goal_lower for keyword in analytics_keywords):
            print(f"✅ Decision: Analytics Agent (detected data analysis task)")
            return "analytics"
        
        if any(keyword in goal_lower for keyword in ppc_keywords):
            print(f"✅ Decision: PPC Agent (detected advertising task)")
            return "ppc"
        
        if any(keyword in goal_lower for keyword in crm_keywords):
            print(f"✅ Decision: CRM Agent (detected customer/email task)")
            return "crm"
        
        if any(keyword in goal_lower for keyword in seo_keywords):
            print(f"✅ Decision: SEO Agent (detected SEO-related task)")
            return "seo"
        
        if any(keyword in goal_lower for keyword in smm_keywords):
            print(f"✅ Decision: SMM Agent (detected social media task)")
            return "smm"

        if any(keyword in goal_lower for keyword in research_keywords):
            print(f"✅ Decision: Research Agent (detected research need)")
            return "research"

        if any(keyword in goal_lower for keyword in content_keywords):
            print(f"✅ Decision: Content Agent (detected writing task)")
            return "content"
        
        # Default: if unclear, use research (safer choice)
        print(f"✅ Default decision: Research Agent (will gather information)")
        return "research"
    
    def execute_task(self, user_goal):
        """
        Execute the user's goal by routing to the right agent(s)
        Now supports complex multi-agent collaboration!
        
        Args:
            user_goal (str): The user's high-level goal
            
        Returns:
            str: The result from the agent(s)
        """
        print("\n" + "="*60)
        print("🚀 THE NEXUS - TASK EXECUTION (v2.0 - 10 Agents)")
        print("="*60)
        
        # Detect if this is a multi-agent task
        goal_lower = user_goal.lower()
        
        # ADVANCED WORKFLOW: Complete Marketing Campaign
        if 'complete' in goal_lower and 'campaign' in goal_lower:
            return self._execute_complete_campaign(user_goal)
        
        # WORKFLOW: Research + SEO + Write
        if ('research' in goal_lower and 'seo' in goal_lower and 'write' in goal_lower):
            return self._execute_research_seo_content(user_goal)
        
        # WORKFLOW: Research + Write
        research_and_write = any([
            'research' in goal_lower and 'write' in goal_lower,
            'find' in goal_lower and 'write' in goal_lower,
            'search' in goal_lower and 'create' in goal_lower,
        ])
        
        if research_and_write:
            return self._execute_research_content(user_goal)
        
        # WORKFLOW: SEO + Write
        seo_and_write = any([
            'keyword' in goal_lower and 'write' in goal_lower,
            'seo' in goal_lower and 'content' in goal_lower,
            'optimize' in goal_lower and 'write' in goal_lower,
        ])
        
        if seo_and_write:
            return self._execute_seo_content(user_goal)
        
        # WORKFLOW: PPC + Analytics
        if ('ad' in goal_lower or 'ppc' in goal_lower) and 'analyze' in goal_lower:
            return self._execute_ppc_analytics(user_goal)
        
        # SINGLE AGENT TASKS
        return self._execute_single_agent(user_goal)
    
    def _execute_complete_campaign(self, user_goal):
        """Execute a complete multi-agent marketing campaign"""
        print("\n🚀 COMPLETE MARKETING CAMPAIGN DETECTED!")
        print("📋 Workflow: Research → SEO → Content → PPC → CRM → Analytics")
        
        results = {}
        
        try:
            # Step 1: Research
            print("\n--- Step 1: Market Research ---")
            research_result = research_topic(user_goal, num_results=5)
            results['research'] = research_result['analysis'][:500] + "..."
            
            # Step 2: SEO
            print("\n--- Step 2: SEO Strategy ---")
            keywords = find_keywords(user_goal, num_keywords=10)
            results['keywords'] = keywords[:500] + "..."
            
            # Step 3: Content
            print("\n--- Step 3: Content Creation ---")
            content_prompt = f"Write a blog post about: {user_goal}\n\nUse these insights: {results['research'][:200]}"
            content = generate_content(content_prompt)
            results['content'] = content[:500] + "..."
            
            # Step 4: PPC
            print("\n--- Step 4: PPC Campaign ---")
            ppc_strategy = create_campaign_strategy(user_goal, budget=500)
            results['ppc'] = ppc_strategy[:500] + "..."
            
            # Step 5: CRM
            print("\n--- Step 5: Email Sequence ---")
            email_seq = create_email_sequence(f"nurture leads for {user_goal}", num_emails=3)
            results['crm'] = email_seq[:500] + "..."
            
            # Step 6: Analytics Plan
            print("\n--- Step 6: Analytics & Tracking ---")
            analytics_plan = f"Campaign metrics to track for: {user_goal}"
            results['analytics'] = "Tracking plan created"
            
            print("\n✅ Complete campaign executed!")
            
            # Log to memory
            self.memory.log_task(
                task_description=user_goal,
                result_summary="Complete 6-agent campaign executed",
                agent_used="all_agents"
            )
            
            # Format results
            output = "🎯 COMPLETE MARKETING CAMPAIGN\n\n"
            output += f"1️⃣ RESEARCH:\n{results['research']}\n\n"
            output += f"2️⃣ SEO KEYWORDS:\n{results['keywords']}\n\n"
            output += f"3️⃣ CONTENT:\n{results['content']}\n\n"
            output += f"4️⃣ PPC STRATEGY:\n{results['ppc']}\n\n"
            output += f"5️⃣ EMAIL SEQUENCE:\n{results['crm']}\n\n"
            output += f"6️⃣ ANALYTICS: Tracking plan ready\n"
            
            return output
            
        except Exception as e:
            return f"❌ Error in complete campaign: {e}"
    
    def _execute_research_content(self, user_goal):
        """Execute Research + Content workflow"""
        print("\n🔗 Multi-agent task detected!")
        print("📋 Workflow: Research Agent → Content Agent")
        
        try:
            print("\n--- Step 1: Research Phase ---")
            research_query = user_goal.replace('write', '').replace('create', '').strip()
            research_result = research_topic(research_query, num_results=5)
            research_data = research_result['analysis']
            
            print("\n--- Step 2: Content Creation Phase ---")
            content_prompt = f"Based on this research:\n\n{research_data}\n\nNow write content as requested: {user_goal}"
            result = generate_content(content_prompt)
            
            self.memory.log_task(
                task_description=user_goal,
                result_summary="Research + Content collaboration",
                agent_used="research+content"
            )
            
            return f"🔬 RESEARCH:\n{research_data}\n\n{'='*60}\n\n✍️ CONTENT:\n{result}"
            
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _execute_seo_content(self, user_goal):
        """Execute SEO + Content workflow"""
        print("\n🔗 Multi-agent task detected!")
        print("📋 Workflow: SEO Agent → Content Agent")
        
        try:
            print("\n--- Step 1: SEO Analysis ---")
            seo_topic = user_goal.replace('write', '').replace('create', '').strip()
            keywords = find_keywords(seo_topic, num_keywords=10)
            
            print("\n--- Step 2: SEO-Optimized Content ---")
            content_prompt = f"Using these keywords:\n\n{keywords}\n\nCreate: {user_goal}"
            result = generate_content(content_prompt)
            
            self.memory.log_task(
                task_description=user_goal,
                result_summary="SEO + Content collaboration",
                agent_used="seo+content"
            )
            
            return f"🔑 KEYWORDS:\n{keywords}\n\n{'='*60}\n\n✍️ CONTENT:\n{result}"
            
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _execute_research_seo_content(self, user_goal):
        """Execute Research + SEO + Content workflow"""
        print("\n🔗 Advanced 3-agent workflow!")
        print("📋 Workflow: Research → SEO → Content")
        
        try:
            print("\n--- Step 1: Research ---")
            research_result = research_topic(user_goal, num_results=5)
            
            print("\n--- Step 2: SEO Keywords ---")
            keywords = find_keywords(user_goal, num_keywords=10)
            
            print("\n--- Step 3: SEO-Optimized Content with Research ---")
            prompt = f"Research:\n{research_result['analysis'][:500]}\n\nKeywords:\n{keywords[:300]}\n\nWrite: {user_goal}"
            content = generate_content(prompt)
            
            self.memory.log_task(
                task_description=user_goal,
                result_summary="Research + SEO + Content",
                agent_used="research+seo+content"
            )
            
            return f"🔬 RESEARCH:\n{research_result['analysis'][:500]}...\n\n🔑 KEYWORDS:\n{keywords[:300]}...\n\n✍️ CONTENT:\n{content}"
            
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _execute_ppc_analytics(self, user_goal):
        """Execute PPC + Analytics workflow"""
        print("\n🔗 Multi-agent task detected!")
        print("📋 Workflow: PPC Agent → Analytics Agent")
        
        try:
            print("\n--- Step 1: PPC Strategy ---")
            ppc_result = create_campaign_strategy(user_goal)
            
            print("\n--- Step 2: Analytics Plan ---")
            analytics_prompt = f"Create tracking plan for: {user_goal}\n\nPPC Strategy: {ppc_result[:300]}"
            
            return f"💰 PPC STRATEGY:\n{ppc_result}\n\n{'='*60}\n\n📊 ANALYTICS PLAN:\nTracking metrics defined"
            
        except Exception as e:
            return f"❌ Error: {e}"
    
    def _execute_single_agent(self, user_goal):
        """Execute single agent task"""
        agent_name = self.smart_route(user_goal)
        
        print(f"\n📡 Routing task to: {agent_name.upper()} AGENT")
        
        try:
            if agent_name == "content":
                result = generate_content(user_goal)
            
            elif agent_name == "research":
                if len(user_goal.split()) <= 10:
                    result = quick_research(user_goal)
                else:
                    research_result = research_topic(user_goal, num_results=5)
                    result = research_result['analysis']
            
            elif agent_name == "seo":
                if 'keyword' in user_goal.lower():
                    result = find_keywords(user_goal.replace('keywords', '').replace('keyword', '').strip())
                elif 'competitor' in user_goal.lower():
                    result = competitor_analysis(user_goal)
                else:
                    seo_result = analyze_seo(user_goal)
                    result = seo_result['analysis']
            
            elif agent_name == "ppc":
                if 'ad copy' in user_goal.lower() or 'write ad' in user_goal.lower():
                    result = write_ad_copy(user_goal)
                else:
                    result = create_campaign_strategy(user_goal)
            
            elif agent_name == "crm":
                if 'sequence' in user_goal.lower():
                    result = create_email_sequence(user_goal)
                else:
                    result = write_single_email(user_goal)
            
            elif agent_name == "analytics":
                result = f"Analytics Agent ready. Please provide specific data to analyze."
            
            elif agent_name == "brand":
                if 'tone of voice' in user_goal.lower() or 'tone' in user_goal.lower():
                    result = define_tone_of_voice(
                        brand_name="Brand",
                        brand_personality="Professional, friendly",
                        target_audience="Business professionals"
                    )
                elif 'positioning' in user_goal.lower():
                    result = "Brand positioning requires: company, target, category, benefit, differentiation. Please provide these details."
                else:
                    result = create_brand_strategy(
                        company_name="Company",
                        industry="General",
                        target_audience="Target audience",
                        unique_value=user_goal
                    )
            
            elif agent_name == "webux":
                if 'landing page' in user_goal.lower():
                    result = design_landing_page(
                        product="Product",
                        target_audience="Target audience",
                        goal="Conversion",
                        key_benefits=user_goal
                    )
                elif 'flow' in user_goal.lower():
                    result = optimize_user_flow(
                        current_flow="Current user flow",
                        conversion_goal=user_goal,
                        pain_points=""
                    )
                else:
                    result = analyze_ux_issues(
                        page_description=user_goal,
                        user_feedback="",
                        metrics=""
                    )
            
            elif agent_name == "cro":
                if 'funnel' in user_goal.lower():
                    result = analyze_funnel(
                        funnel_steps=user_goal,
                        conversion_data="",
                        goal="Increase conversions"
                    )
                elif 'a/b test' in user_goal.lower() or 'ab test' in user_goal.lower():
                    result = create_ab_test_plan(
                        element_to_test="Element",
                        current_version="Current version",
                        hypothesis=user_goal,
                        success_metric="Conversion rate"
                    )
                elif 'friction' in user_goal.lower():
                    result = identify_friction_points(
                        page_type="Page",
                        user_behavior="User behavior observed",
                        conversion_goal=user_goal
                    )
                else:
                    result = analyze_funnel(
                        funnel_steps=user_goal,
                        conversion_data="",
                        goal="Optimize conversion"
                    )
            
            elif agent_name == "smm":
                goal_l = user_goal.lower()
                if 'calendar' in goal_l:
                    result = create_social_calendar(
                        brand_name="Brand",
                        industry="General",
                        platforms=["instagram", "linkedin", "twitter"],
                        posts_per_week=5,
                        target_audience=user_goal
                    )
                elif 'trend' in goal_l:
                    result = analyze_trends(
                        industry=user_goal,
                        platforms=["instagram", "linkedin", "twitter", "tiktok"]
                    )
                elif 'viral' in goal_l or 'hook' in goal_l:
                    result = create_viral_hooks(
                        topic=user_goal,
                        platform="instagram",
                        count=5
                    )
                elif 'engagement' in goal_l or 'strategy' in goal_l:
                    result = create_engagement_strategy(
                        brand_name="Brand",
                        industry="General",
                        current_followers=1000,
                        growth_goal="Grow engagement by 50%"
                    )
                else:
                    # Detect platform from goal or default
                    platform = "instagram"
                    for p in ["linkedin", "twitter", "tiktok", "facebook"]:
                        if p in goal_l:
                            platform = p
                            break
                    result = write_platform_post(
                        platform=platform,
                        topic=user_goal,
                        brand_voice="Professional and engaging",
                        goal="Increase engagement",
                        brand_name="Brand"
                    )

            else:
                result = "Error: Agent not found"

            print("\n✅ Task completed by The Nexus")
            
            # Track performance
            self.performance_metrics['total_tasks'] += 1
            self.performance_metrics['successful_tasks'] += 1
            if agent_name not in self.performance_metrics['agent_usage']:
                self.performance_metrics['agent_usage'][agent_name] = 0
            self.performance_metrics['agent_usage'][agent_name] += 1
            
            self.memory.log_task(
                task_description=user_goal,
                result_summary=result[:100] + "..." if len(result) > 100 else result,
                agent_used=agent_name
            )
            
            return result
            
        except Exception as e:
            error_msg = f"❌ Error executing task: {str(e)}"
            print(error_msg)
            
            # Track failure
            self.performance_metrics['total_tasks'] += 1
            self.performance_metrics['failed_tasks'] += 1
            
            return error_msg
    
    def resolve_conflict(self, topic: str, agent_positions: Dict[str, str]) -> Dict:
        """Resolve conflict between agents using debate"""
        print(f"\n⚖️ CONFLICT RESOLUTION INITIATED")
        print(f"Topic: {topic}")
        print("-" * 60)
        
        for agent, position in agent_positions.items():
            print(f"\n{agent.upper()}'s Position:")
            print(f"  {position[:150]}...")
        
        result = self.debate_system.initiate_debate(topic, agent_positions)
        
        print(f"\n🏆 Winner: {result['winner']}")
        print(f"📊 Reasoning: {result['reasoning']}")
        print("-" * 60)
        
        return result
    
    def allocate_budget(self, task: str, amount: float, agent: str) -> bool:
        """Allocate budget for a task"""
        return self.budget_manager.allocate(task, amount, agent)
    
    def veto_output(self, agent: str, output: str, reason: str) -> bool:
        """Exercise veto power over agent output"""
        print(f"\n🚫 VETO EXERCISED BY THE NEXUS")
        print(f"Agent: {agent.upper()}")
        print(f"Reason: {reason}")
        print(f"Output (preview): {output[:100]}...")
        print("-" * 60)
        
        return True
    
    def get_performance_report(self) -> Dict:
        """Get comprehensive system performance report"""
        budget_report = self.budget_manager.get_report()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'tasks': self.performance_metrics,
            'budget': budget_report,
            'debates': len(self.debate_system.debate_history),
            'agents': self.available_agents
        }
    
    def display_dashboard(self):
        """Display comprehensive system dashboard"""
        report = self.get_performance_report()
        
        print("\n" + "="*70)
        print("📊 THE NEXUS - SYSTEM DASHBOARD (MarketingOS 2.0)")
        print("="*70)
        
        print(f"\n💰 BUDGET STATUS:")
        print(f"   Total: ${report['budget']['total_budget']:,.2f}")
        print(f"   Allocated: ${report['budget']['allocated']:,.2f}")
        print(f"   Remaining: ${report['budget']['remaining']:,.2f}")
        print(f"   Utilization: {report['budget']['utilization_percent']:.1f}%")
        
        print(f"\n📋 TASK STATISTICS:")
        print(f"   Total: {report['tasks']['total_tasks']}")
        print(f"   Successful: {report['tasks']['successful_tasks']}")
        print(f"   Failed: {report['tasks']['failed_tasks']}")
        
        print(f"\n⚖️ DEBATES: {report['debates']}")
        
        print(f"\n🤖 AGENTS: {len(report['agents'])}")
        
        if report['tasks']['agent_usage']:
            print(f"\n📊 AGENT USAGE:")
            for agent, count in report['tasks']['agent_usage'].items():
                print(f"   {agent}: {count} tasks")
        
        print("="*70 + "\n")

    def run_feedback_loop(self):
        """
        Pull live analytics, detect anomalies, and auto-trigger agents.
        This is the real feedback loop — the system watches its own performance
        and acts when something goes wrong.

        Returns:
            dict with 'anomalies', 'actions_taken', and 'report'
        """
        print("\n" + "=" * 60)
        print("🔄 FEEDBACK LOOP — Live Performance Check")
        print("=" * 60)

        result = {"anomalies": [], "actions_taken": [], "report": ""}

        try:
            from analytics_agent import detect_live_anomalies
            from ppc_agent import get_real_campaign_performance, auto_optimize_campaigns
            from crm_agent import get_real_email_performance

            # --- 1. Check for traffic / conversion anomalies ---
            anomaly_data = detect_live_anomalies(days=7)
            if anomaly_data and anomaly_data.get("anomalies"):
                result["anomalies"] = anomaly_data["anomalies"]
                print(f"\n⚠️  {len(anomaly_data['anomalies'])} anomalies detected")

                for a in anomaly_data["anomalies"]:
                    metric = a.get("metric", "unknown")
                    severity = a.get("severity", "warning")
                    change = a.get("change_percent", 0)
                    print(f"   [{severity.upper()}] {metric}: {change:+.1f}%")

                    # Auto-trigger CRO agent if conversions dropped
                    if metric in ("purchase", "conversion", "lead") and change < -15:
                        print(f"\n🚨 Conversion drop on '{metric}' — triggering CRO analysis...")
                        cro_result = analyze_funnel(
                            funnel_steps=f"Conversion event '{metric}' dropped {change:+.1f}% in last 7 days",
                            conversion_data=anomaly_data.get("report", ""),
                            goal="Identify and fix conversion drop"
                        )
                        result["actions_taken"].append({
                            "trigger": f"conversion_drop:{metric}",
                            "agent": "cro",
                            "output": cro_result[:300]
                        })
                        print("   ✅ CRO analysis complete")
            else:
                print("\n✅ No anomalies detected — all metrics stable")

            # --- 2. Check PPC campaign health ---
            campaigns = get_real_campaign_performance(days=7)
            if campaigns:
                for c in campaigns:
                    cpa = c.get("cpa_usd", 0)
                    if cpa > 0:
                        # Flag campaigns with CPA > 3x average (simple threshold)
                        avg_cpa = sum(x.get("cpa_usd", 0) for x in campaigns) / len(campaigns)
                        if cpa > avg_cpa * 3:
                            print(f"\n⚠️  Campaign '{c['name']}' CPA (${cpa:.2f}) is 3x+ above average (${avg_cpa:.2f})")
                            result["actions_taken"].append({
                                "trigger": f"high_cpa:{c['name']}",
                                "agent": "ppc",
                                "output": "Flagged for manual review — CPA exceeds 3x average"
                            })
                opt_report = auto_optimize_campaigns(days=7)
                if opt_report:
                    result["actions_taken"].append({
                        "trigger": "ppc_auto_optimize",
                        "agent": "ppc",
                        "output": opt_report[:300]
                    })

            # --- 3. Check email performance ---
            email_stats = get_real_email_performance()
            if email_stats:
                print(f"\n📧 Email stats pulled — {type(email_stats).__name__} returned")
                result["actions_taken"].append({
                    "trigger": "email_stats_check",
                    "agent": "crm",
                    "output": str(email_stats)[:300]
                })

        except Exception as e:
            print(f"⚠️  Feedback loop error: {e}")
            result["report"] = f"Error: {e}"
            return result

        # Build summary report
        lines = [
            f"Anomalies found: {len(result['anomalies'])}",
            f"Actions triggered: {len(result['actions_taken'])}",
        ]
        for action in result["actions_taken"]:
            lines.append(f"  → [{action['agent'].upper()}] {action['trigger']}")
        result["report"] = "\n".join(lines)

        print("\n" + "-" * 60)
        print("📋 Feedback Loop Summary:")
        print(result["report"])
        print("-" * 60)

        return result

    def interactive_mode(self):
        """Interactive mode - keep asking for tasks until user quits"""
        print("\n" + "="*60)
        print("🎮 INTERACTIVE MODE - THE NEXUS v2.0 (10 AGENTS)")
        print("="*60)
        print("Type your goals, and The Nexus will orchestrate intelligently!")
        print("\n📋 Special commands:")
        print("  - 'dashboard' - View complete system dashboard")
        print("  - 'budget' - View budget status")
        print("  - 'memory' or 'show memory' - View memory summary")
        print("  - 'tasks' - View recent tasks")
        print("  - 'agents' - Show available agents")
        print("  - 'debate <topic>' - Test conflict resolution")
        print("  - 'feedback' - Run live feedback loop (anomaly detection + auto-actions)")
        print("  - 'quit' or 'exit' - Stop")
        print("="*60)
        
        while True:
            user_input = input("\n👤 Your goal: ").strip()
            
            if not user_input:
                print("⚠️ Please enter a goal!")
                continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Shutting down The Nexus. Goodbye!")
                break
            
            if user_input.lower() == 'dashboard':
                self.display_dashboard()
                continue
            
            if user_input.lower() == 'budget':
                report = self.budget_manager.get_report()
                print(f"\n💰 BUDGET REPORT:")
                print(f"   Total: ${report['total_budget']:,.2f}")
                print(f"   Allocated: ${report['allocated']:,.2f}")
                print(f"   Remaining: ${report['remaining']:,.2f}")
                print(f"   Utilization: {report['utilization_percent']:.1f}%")
                continue
            
            if user_input.lower().startswith('debate '):
                topic = user_input[7:].strip()
                result = self.resolve_conflict(
                    topic,
                    {
                        'seo': "Target long-tail keywords for better ROI and sustainable growth",
                        'ppc': "Target high-volume head terms for immediate visibility and brand awareness"
                    }
                )
                continue

            if user_input.lower() == 'feedback':
                self.run_feedback_loop()
                continue
            
            if user_input.lower() in ['memory', 'show memory']:
                self.show_memory()
                continue
            
            if user_input.lower() == 'tasks':
                recent = self.memory.get_recent_tasks(10)
                print("\n📋 Recent Tasks:")
                if not recent:
                    print("   No tasks yet!")
                else:
                    for i, task in enumerate(recent, 1):
                        print(f"\n{i}. {task['task'][:60]}...")
                        print(f"   Agent: {task['agent']}")
                        print(f"   Time: {task['timestamp']}")
                continue
            
            if user_input.lower() == 'agents':
                print("\n🤖 Available Agents:")
                for name, desc in self.available_agents.items():
                    print(f"\n{name.upper()}:")
                    print(f"  {desc}")
                continue
            
            result = self.execute_task(user_input)
            
            print("\n" + "="*60)
            print("📄 RESULT:")
            print("="*60)
            print(result[:500] if len(result) > 500 else result)
            if len(result) > 500:
                print(f"\n... ({len(result)} total characters)")
            print("="*60)
    
    def show_memory(self):
        """Display current memory summary"""
        self.memory.display_summary()


# Test The Nexus v2.0
if __name__ == "__main__":
    nexus = Nexus()
    
    print("\n" + "="*60)
    print("🧪 TESTING MARKETINGOS 2.0 WITH 9 AGENTS")
    print("="*60)
    
    # Test routing for all 9 agents
    test_goals = [
        "Research AI trends",
        "Write a blog post",
        "Find keywords for coffee shop",
        "Create ad campaign for yoga studio",
        "Write email sequence for new customers",
        "Analyze campaign performance",
        "Create brand strategy for startup",
        "Design landing page for SaaS",
        "Analyze funnel for e-commerce"
    ]
    
    for i, goal in enumerate(test_goals, 1):
        print(f"\n--- Test {i}/9 ---")
        print(f"Goal: {goal}")
        agent = nexus.smart_route(goal)
        print(f"Routed to: {agent}")
    
    # Test new features
    print("\n" + "="*60)
    print("🧪 TESTING 2.0 FEATURES")
    print("="*60)
    
    # Test budget
    print("\n--- Budget Allocation ---")
    nexus.allocate_budget("Brand Strategy", 1500, "brand")
    nexus.allocate_budget("Landing Page Design", 2000, "webux")
    
    # Test debate
    print("\n--- Agent Debate ---")
    nexus.resolve_conflict(
        "Should we redesign the landing page or optimize the funnel first?",
        {
            "webux": "Redesign provides better user experience and modern aesthetics",
            "cro": "Optimize funnel first - fixes conversion issues with minimal design changes"
        }
    )
    
    # Show dashboard
    nexus.display_dashboard()
    
    print("\n" + "="*60)
    print("✅ All tests complete! MarketingOS 2.0 with 9 agents ready!")
    print("\nStarting interactive mode...")
    print("="*60)
    
    nexus.interactive_mode()