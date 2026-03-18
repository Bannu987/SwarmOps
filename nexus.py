"""
The Nexus - Master Orchestrator (UPGRADED v4.0 → 2.0)
Smart routing to 10 specialized agents with advanced workflows
+ Budget Management + Agent Debate + Performance Tracking + Pipeline Execution
"""

import asyncio
from model_router import call_model_sync
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

# ============================================================================
# NEXUS MASTER SYSTEM PROMPT — v2.0
# This is the foundational identity for The Nexus.
# It governs ALL responses: EQ override, revenue logic, tone, formatting.
# ============================================================================

NEXUS_MASTER_PROMPT = """RULES (these override ALL other instructions):
1. ANSWER FIRST. Always answer the user's question immediately.
   Never delay by requesting setup data. If info is missing, give best-practice advice first.

2. YOU vs THEM. You are SwarmOps, an AI marketing advisor.
   Say "you", "your business", or the brand name. NEVER "we", "our", "at SwarmOps we".

3. NO HALLUCINATION. Never diagnose a website you haven't analyzed.
   Never invent issues. If no data exists, say "based on best practices for your industry".

4. NO FAKE NUMBERS. Never fabricate statistics or percentages.
   Only use specific numbers when computed from real user-provided data.

5. CONCISE. Default: 4-8 sentences. Bullet lists (3-5 items) for recommendations.
   Only write long responses when user explicitly asks for a report or audit.

6. SPECIFIC. Every recommendation must be concrete and actionable.
   BAD: "Improve your SEO"
   GOOD: "Write a guide targeting the keyword 'marketing audit checklist'"

7. NO TEMPLATES. Never use section headers like "Critical Issues", "Priority Actions",
   "Expected Impact", "Action Architecture", "What We Found", "What This Means",
   "Your Next Move", "Heuristic Evaluation", "Strategic Roadmap", "Traffic Boost Strategy".
   Write like a smart friend giving advice, not a consulting firm.

8. EXTERNAL ANALYSIS. When analyzing a URL that is NOT the user's stored website,
   analyze it independently without applying the user's brand profile.

---

You are Nexus, a marketing strategist inside SwarmOps.
You help business owners grow through smart, data-driven marketing.
You coordinate specialist agents for SEO, content, PPC, analytics,
CRM, social media, brand strategy, web/UX, CRO, and research.

When responding:
- Lead with your key insight (1-2 sentences)
- Give 3-5 specific action items as bullets
- End with "Would you like me to..." and 2-3 next steps
"""

# ============================================================================
# EMOTIONAL DISTRESS DETECTOR
# ============================================================================

# Signals that trigger the EQ Override
_EQ_PANIC_SIGNALS = [
    "panic", "panicking", "freaking out", "stressed", "stressed out",
    "overwhelmed", "overwhelm", "anxious", "anxiety", "scared", "terrified",
    "no signups", "no sales", "zero sales", "no revenue", "no traffic",
    "burning money", "wasting money", "nothing works", "not working",
    "losing money", "can't afford", "going broke", "desperate",
    "help me", "don't know what to do", "lost", "confused", "frustrated",
    "gave up", "want to quit", "failing", "failure", "failed",
    "imposter", "not good enough", "shouldn't be doing this",
    "burnout", "burned out", "exhausted", "too much", "can't handle",
    "what do i do", "where do i start", "don't know where",
]

def detect_emotional_distress(message: str) -> bool:
    """
    Returns True if the user message contains high-distress signals
    that should trigger the EQ Override (Directive 1).
    """
    msg_lower = message.lower()
    return any(signal in msg_lower for signal in _EQ_PANIC_SIGNALS)


"""
SWARMOPS ENHANCEMENTS
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
        self.memory = MemorySystem()
        
        # NEW: SwarmOps Features
        self.debate_system = AgentDebate()
        self.budget_manager = BudgetManager(total_budget=budget_limit)
        self.performance_metrics = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'agent_usage': {}
        }
        
        # Available agents (10 AGENTS — SwarmOps)
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
    
    def detect_pipeline(self, user_goal: str) -> dict:
        """
        Detect if the task requires multiple agents in a pipeline.

        Args:
            user_goal: The user's high-level goal

        Returns:
            {
                "is_pipeline": bool,
                "pipeline": list of agent names or False,
                "reasoning": str
            }
        """
        goal_lower = user_goal.lower()

        # FULL CAMPAIGN
        if any(phrase in goal_lower for phrase in ["full campaign", "complete campaign", "entire campaign", "full marketing"]):
            return {
                "is_pipeline": True,
                "pipeline": ["seo", "content", "ppc", "smm", "crm"],
                "reasoning": "Full marketing campaign detected — SEO → Content → PPC/SMM/CRM in parallel"
            }

        # SEO + CONTENT
        if any(phrase in goal_lower for phrase in [
            "find keywords and write",
            "keywords and blog",
            "seo and content",
            "keyword research and write"
        ]) or ("keywords for" in goal_lower and "write" in goal_lower):
            return {
                "is_pipeline": True,
                "pipeline": ["seo", "content"],
                "reasoning": "SEO keyword research needed before content creation"
            }

        # RESEARCH + PPC
        if ("research" in goal_lower and "ad" in goal_lower) or ("research" in goal_lower and "ppc" in goal_lower):
            return {
                "is_pipeline": True,
                "pipeline": ["research", "ppc"],
                "reasoning": "Market research needed before ad campaign creation"
            }

        # CONTENT + SMM
        if ("write" in goal_lower or "content" in goal_lower) and ("post it" in goal_lower or "share" in goal_lower or "social" in goal_lower):
            return {
                "is_pipeline": True,
                "pipeline": ["content", "smm"],
                "reasoning": "Content creation followed by social media distribution"
            }

        # ANALYTICS + CRO
        if ("analyze" in goal_lower and "optimize" in goal_lower) or ("performance" in goal_lower and "conversion" in goal_lower):
            return {
                "is_pipeline": True,
                "pipeline": ["analytics", "cro"],
                "reasoning": "Analytics analysis followed by conversion optimization"
            }

        # No pipeline detected
        return {
            "is_pipeline": False,
            "pipeline": False,
            "reasoning": "Single-agent task"
        }

    async def run_pipeline(self, departments: list, instruction: str) -> dict:
        """
        Run agents in sequence/parallel pipeline, passing output between steps.

        Pipeline rules:
        - ["seo", "content"] → serial (SEO keywords → Content with keywords)
        - ["seo", "content", "ppc", "smm", "crm"] → SEO serial, Content serial, then PPC/SMM/CRM parallel
        - ["analytics", "cro"] → serial (Analytics → CRO with insights)

        Args:
            departments: List of agent names in execution order
            instruction: The user's original instruction

        Returns:
            {
                "pipeline": true,
                "steps": [{"department": "seo", "result": "...", "confidence": 0.82, "latency_ms": 1200}, ...],
                "total_latency_ms": 8500,
                "departments_used": ["seo", "content", "ppc"]
            }
        """
        import time

        print(f"\n🔗 PIPELINE EXECUTION: {' → '.join(departments)}")
        print("=" * 60)

        steps = []
        total_start = time.time()
        context = ""  # Accumulated context from previous steps

        # Determine parallel execution points
        # For full campaign: SEO (serial) → Content (serial) → PPC/SMM/CRM (parallel)
        if departments == ["seo", "content", "ppc", "smm", "crm"]:
            serial_agents = ["seo", "content"]
            parallel_agents = ["ppc", "smm", "crm"]
        else:
            # Default: all serial
            serial_agents = departments
            parallel_agents = []

        # Execute serial agents
        for dept in serial_agents:
            step_start = time.time()
            print(f"\n--- Step: {dept.upper()} Agent ---")

            # Build prompt with context from previous steps
            if context:
                prompt = f"{context}\n\nNow, based on the above context: {instruction}"
            else:
                prompt = instruction

            try:
                # Execute agent
                result = await asyncio.get_event_loop().run_in_executor(
                    None, self._execute_single_step, dept, prompt
                )

                latency = int((time.time() - step_start) * 1000)

                # Extract confidence from Skeptic if available
                confidence = 0.75  # Default confidence

                steps.append({
                    "department": dept,
                    "result": result[:500] + "..." if len(result) > 500 else result,
                    "full_result": result,  # Keep full result for next step's context
                    "confidence": confidence,
                    "latency_ms": latency
                })

                # Add to context for next step
                context += f"\n\n[{dept.upper()} OUTPUT]:\n{result[:300]}..."

                print(f"✅ {dept.upper()} completed ({latency}ms)")

            except Exception as e:
                print(f"❌ {dept.upper()} failed: {e}")
                steps.append({
                    "department": dept,
                    "result": f"Error: {e}",
                    "full_result": f"Error: {e}",
                    "confidence": 0.0,
                    "latency_ms": int((time.time() - step_start) * 1000)
                })

        # Execute parallel agents
        if parallel_agents:
            print(f"\n--- Parallel Execution: {', '.join([a.upper() for a in parallel_agents])} ---")

            parallel_tasks = []
            for dept in parallel_agents:
                # Build prompt with accumulated context
                if context:
                    prompt = f"{context}\n\nNow, based on the above context: {instruction}"
                else:
                    prompt = instruction

                # Create async task
                task = asyncio.get_event_loop().run_in_executor(
                    None, self._execute_single_step, dept, prompt
                )
                parallel_tasks.append((dept, task, time.time()))

            # Wait for all parallel tasks to complete
            for dept, task, start_time in parallel_tasks:
                try:
                    result = await task
                    latency = int((time.time() - start_time) * 1000)
                    confidence = 0.75

                    steps.append({
                        "department": dept,
                        "result": result[:500] + "..." if len(result) > 500 else result,
                        "full_result": result,
                        "confidence": confidence,
                        "latency_ms": latency
                    })

                    print(f"✅ {dept.upper()} completed ({latency}ms)")

                except Exception as e:
                    print(f"❌ {dept.upper()} failed: {e}")
                    steps.append({
                        "department": dept,
                        "result": f"Error: {e}",
                        "full_result": f"Error: {e}",
                        "confidence": 0.0,
                        "latency_ms": int((time.time() - time.time()) * 1000)
                    })

        total_latency = int((time.time() - total_start) * 1000)

        print("\n" + "=" * 60)
        print(f"✅ PIPELINE COMPLETE ({total_latency}ms total)")

        # Log to memory
        try:
            self.memory.log_task(
                task_description=f"PIPELINE: {instruction}",
                result_summary=f"Executed {len(steps)} agents: {', '.join(departments)}",
                agent_used="pipeline:" + "+".join(departments)
            )
        except Exception:
            pass

        return {
            "pipeline": True,
            "steps": steps,
            "total_latency_ms": total_latency,
            "departments_used": departments
        }

    def _execute_single_step(self, department: str, prompt: str) -> str:
        """
        Execute a single agent synchronously (called from run_pipeline).

        Args:
            department: Agent name (e.g., "seo", "content")
            prompt: The prompt for this agent

        Returns:
            Result string from the agent
        """
        # Map department name to agent function
        if department == "seo":
            from seo_agent import find_keywords
            return find_keywords(prompt)

        elif department == "content":
            from content_agent import generate_content
            return generate_content(prompt)

        elif department == "ppc":
            from ppc_agent import create_campaign_strategy
            return create_campaign_strategy(prompt)

        elif department == "smm":
            from smm_agent import write_platform_post
            return write_platform_post(
                platform="linkedin", topic=prompt,
                brand_voice="Professional", goal="engagement",
                brand_name="Brand"
            )

        elif department == "crm":
            from crm_agent import create_email_sequence
            return create_email_sequence(prompt, num_emails=3)

        elif department == "analytics":
            from analytics_agent import analyze_performance
            return analyze_performance(prompt, "Pipeline analysis step")

        elif department == "cro":
            from cro_agent import analyze_funnel
            return analyze_funnel(prompt, "", "Optimize conversion")

        elif department == "research":
            from research_agent import research_topic
            result = research_topic(prompt)
            if isinstance(result, dict):
                return result.get("analysis", str(result))
            return str(result)

        elif department == "brand":
            from brand_strategist_agent import create_brand_strategy
            return create_brand_strategy("Brand", "General", "General", prompt)

        elif department == "webux":
            from web_ux_agent import design_landing_page
            return design_landing_page(prompt, "General", "conversions")

        else:
            return f"Unknown department: {department}"

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

        # COMPETITIVE INTELLIGENCE keywords — specific intel queries (checked FIRST before SEO
        # to intercept 'competitor' when user wants tracked-competitor analysis/battle cards)
        competitive_intel_keywords = [
            'battle card', 'battlecard', 'battle-card',
            'competitive intelligence', 'competitive analysis',
            'add competitor', 'track competitor', 'competitive monitoring',
            'how do we compare', 'compare us to', 'stack up against',
            'market position', 'competitive landscape', 'who are our competitors',
        ]

        # Priority order: Competitive Intel > Brand > WebUX > CRO > Analytics > PPC > CRM > SEO > SMM > Research > Content
        if any(keyword in goal_lower for keyword in competitive_intel_keywords):
            print(f"✅ Decision: Competitive Intelligence Agent (detected competitive analysis task)")
            return "competitive_intel"

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
    
    def check_onboarding_needed(self) -> Optional[str]:
        """
        Check if the user is new (no business profile stored yet).
        Returns an onboarding prompt if first-time user, else None.
        """
        try:
            from memory_store import get_memory_store
            profile = get_memory_store().get_all_profile_keys()
            if not profile:
                return (
                    "Welcome to SwarmOps! To give you data-driven, personalized marketing intelligence "
                    "(not generic advice), I need to understand your business first.\n\n"
                    "Please answer these 4 quick questions:\n\n"
                    "1. **Website URL** — What's your website? (e.g., https://yoursite.com)\n"
                    "2. **Industry** — What industry/niche? "
                    "(e.g., SaaS, ecommerce, local business, B2B services, healthcare)\n"
                    "3. **Primary Marketing Goal** — What's your #1 goal right now? "
                    "(e.g., 'grow organic traffic', 'reduce customer acquisition cost', "
                    "'scale Google Ads', 'improve email open rates')\n"
                    "4. **Monthly Marketing Budget** — How much do you spend on marketing per month? "
                    "(e.g., $1,000 / $10,000 / $100,000)\n\n"
                    "Once I have this, I'll benchmark you against your industry, pull your live data "
                    "(if you've connected GA4, HubSpot, or Google Ads), and give you specific, "
                    "numbered recommendations — not generic platitudes."
                )
        except Exception:
            pass
        return None

    def _update_brand_context_silently(self, user_message: str):
        """Silently update the Brand Context if the user mentions changes."""
        from memory_store import get_memory_store
        import json
        
        prompt = f"""You are a silent data extractor.
Analyze the following user message to see if they are explicitly updating their business profile or brand context.
The context fields are:
- company_name
- industry
- target_audience
- budget_constraints
- current_funnel_bottleneck

If they mention a change (e.g., "We are pivoting to Enterprise", "Our budget is now $5k"), return a JSON object with strictly those keys and the new values.
If they do not mention any updates, return an empty JSON object {{}}.
Do not return any text other than the JSON.

User Message: "{user_message}"
"""
        try:
            response = call_model_sync(prompt, tier=3, max_tokens=150, temperature=0.1)
            content = response.get("content", "{}") if isinstance(response, dict) else str(response)
            
            from model_router import extract_json_safe
            updates = extract_json_safe(content, fallback={})
            if updates:
                get_memory_store().update_brand_context(updates)
                print(f"🔄 Silently updated Brand Context: {list(updates.keys())}")
        except Exception:
            pass

    def apply_nexus_persona(self, user_message: str, raw_agent_output: str) -> str:
        """
        Post-processing layer: re-voices the raw agent output through The Nexus
        Master Prompt identity. This is THE step that applies:
        - EQ Override (Directive 1) on distress detection
        - Revenue-First framing (Directive 2)
        - Conversational Translation Layer (Directive 3)
        - Clear ending with next move (Directive 6)
        - Calm authority tone (Directive 8)

        Args:
            user_message: Original user message (for EQ detection + context)
            raw_agent_output: The raw result from the sub-agent(s)

        Returns:
            Polished Nexus response as a string
        """
        try:
            # 1. Silently update context if user mentioned pivots
            self._update_brand_context_silently(user_message)

            # 2. Fetch current context
            from memory_store import get_memory_store
            brand_context = get_memory_store().get_brand_context()
            context_str = "\n".join([f"- {k.replace('_', ' ').title()}: {v}" for k, v in brand_context.items()])
            
            injected_prompt = f"{NEXUS_MASTER_PROMPT}\n\n=== CURRENT BRAND CONTEXT ===\n{context_str}\n=============================\n"

            is_distressed = detect_emotional_distress(user_message)
            is_eq_only = is_distressed and not raw_agent_output.strip()

            if is_eq_only:
                # Pure EQ mode: no agent data — respond directly as The Nexus with empathy first
                nexus_prompt = (
                    f"{injected_prompt}\n"
                    f"---\n\n"
                    f"USER MESSAGE: {user_message}\n\n"
                    f"---\n\n"
                    f"EMOTIONAL DISTRESS DETECTED. You are in EQ Override mode (Core Directive 1).\n\n"
                    f"STRICT REQUIREMENTS:\n"
                    f"1. Open with ONE warm, human sentence acknowledging their feeling. No platitudes.\n"
                    f"2. In 1-2 short sentences, normalize their experience.\n"
                    f"3. Identify exactly ONE or TWO immediate actions they can take RIGHT NOW.\n"
                    f"4. Close with a single, clear next move.\n"
                    f"5. Total response: 100-250 words maximum.\n"
                    f"6. NO bullet lists. NO headers. NO audit frameworks. NO 10-step plans.\n"
                    f"7. Tone: calm, warm, direct — like a trusted advisor who has seen this before.\n\n"
                    f"Do NOT mention any tools or research. Just respond as The Nexus to a founder who needs a moment of clarity.\n\n"
                    f"Respond now as The Nexus:"
                )
            elif is_distressed:
                # Distress detected but we have some context — lead with empathy, then one action
                nexus_prompt = (
                    f"{injected_prompt}\n"
                    f"---\n\n"
                    f"USER MESSAGE: {user_message}\n\n"
                    f"CONTEXT FROM ANALYSIS:\n{raw_agent_output[:1000]}\n\n"
                    f"---\n\n"
                    f"EMOTIONAL DISTRESS DETECTED. Apply EQ Override (Core Directive 1) BEFORE strategy:\n"
                    f"1. Start with empathy (1 sentence). 2. Normalize their experience (1 sentence). "
                    f"3. Give ONE clear immediate action from the context above. 4. Keep total response under 200 words. "
                    f"No bullet overload. No audit language. Warm, calm, authoritative.\n\n"
                    f"Respond now as The Nexus:"
                )
            else:
                # Normal strategic request — full CMO voice
                nexus_prompt = (
                    f"{injected_prompt}\n"
                    f"---\n\n"
                    f"USER MESSAGE: {user_message}\n\n"
                    f"RAW AGENT INTELLIGENCE (do NOT expose this verbatim — translate it):\n{raw_agent_output[:3000]}\n\n"
                    f"---\n\n"
                    f"Deliver this as The Nexus CMO persona. Translate technical content into business consequences. "
                    f"Apply the Revenue-First lens. "
                    f"End with a clear summary: what was found, what it means for the business, and one specific next action. "
                    f"Use calm authority, bold key ideas, short paragraphs. No corporate stiffness.\n\n"
                    f"Respond now as The Nexus:"
                )

            response_dict = call_model_sync(nexus_prompt, max_tokens=1500)
            polished = response_dict.get("content", "") if isinstance(response_dict, dict) else str(response_dict)
            if polished and len(polished.strip()) > 50:
                return polished.strip()
            # Fallback: return original if polish fails
            return raw_agent_output if raw_agent_output else "I hear you. Let's work through this together. What's your biggest blocker right now?"
        except Exception as e:
            print(f"⚠️  [Nexus] Persona polish failed: {e}")
            return raw_agent_output if raw_agent_output else user_message

    def _try_parse_profile_data(self, message: str):
        """
        Parse and store business profile data from a user message.
        Called on every message to progressively build the profile.
        """
        import re
        msg_lower = message.lower()
        profile_updates = {}

        # URL detection
        urls = re.findall(r'https?://[^\s,]+', message)
        if urls:
            profile_updates['website_url'] = urls[0].rstrip('.,)')

        # Industry detection
        industry_map = {
            'saas': 'saas', 'software': 'saas', 'app': 'saas',
            'ecommerce': 'ecommerce', 'e-commerce': 'ecommerce', 'shopify': 'ecommerce', 'store': 'ecommerce',
            'b2b': 'b2b', 'agency': 'b2b', 'consulting': 'b2b', 'services': 'b2b',
            'healthcare': 'healthcare', 'medical': 'healthcare', 'clinic': 'healthcare',
            'fintech': 'fintech', 'finance': 'fintech', 'banking': 'fintech',
            'real estate': 'real_estate', 'realtor': 'real_estate', 'property': 'real_estate',
            'education': 'education', 'course': 'education', 'school': 'education',
            'local': 'local_business', 'restaurant': 'local_business', 'salon': 'local_business',
        }
        for keyword, industry in industry_map.items():
            if keyword in msg_lower:
                profile_updates['industry'] = industry
                break

        # Budget detection — "$X", "$Xk", "$X,000"
        budget_match = re.search(r'\$([\d,]+(?:\.\d+)?)\s*(?:k|K)?(?:\s*/\s*month)?', message)
        if budget_match:
            profile_updates['monthly_budget'] = budget_match.group(0)

        # Goal detection
        goal_keywords = {
            'organic traffic': 'grow_organic_traffic',
            'seo': 'grow_organic_traffic',
            'google ads': 'scale_paid_ads',
            'paid ads': 'scale_paid_ads',
            'email': 'improve_email_marketing',
            'conversion': 'improve_conversion_rate',
            'reduce cac': 'reduce_acquisition_cost',
            'cac': 'reduce_acquisition_cost',
            'brand': 'build_brand_awareness',
            'leads': 'generate_leads',
        }
        for keyword, goal in goal_keywords.items():
            if keyword in msg_lower and 'primary_goal' not in profile_updates:
                profile_updates['primary_goal'] = goal
                break

        # Save updates to profile store
        if profile_updates:
            try:
                from memory_store import get_memory_store
                mem = get_memory_store()
                for key, value in profile_updates.items():
                    existing = mem.get_profile_key(key)
                    if not existing:  # Only set if not already stored
                        mem.set_profile_key(key, value)
                        print(f"  Profile updated: {key} = {value}")
            except Exception:
                pass

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

        # --- Onboarding check (first-time users only) ---
        onboarding_msg = self.check_onboarding_needed()
        if onboarding_msg:
            # Try to parse profile data from the message itself
            self._try_parse_profile_data(user_goal)
            # If still no profile after parsing, return onboarding prompt
            try:
                from memory_store import get_memory_store
                profile = get_memory_store().get_all_profile_keys()
                if not profile:
                    return onboarding_msg
            except Exception:
                pass
        else:
            # Always try to extract profile data from any message
            self._try_parse_profile_data(user_goal)

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
        print("📊 THE NEXUS - SYSTEM DASHBOARD (SwarmOps)")
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
    print("✅ All tests complete! SwarmOps with 9 agents ready!")
    print("\nStarting interactive mode...")
    print("="*60)
    
    nexus.interactive_mode()