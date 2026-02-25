"""
SMM Agent - Social Media Marketing Specialist
SwarmOps — The 9th Main Agent

Handles platform-specific social media strategy, content creation,
trend analysis, and engagement planning.
Uses model_router (multi-provider AI) + web search (trend research).
"""

import os
from dotenv import load_dotenv
from web_search import WebSearch
from model_router import call_model_sync

load_dotenv()


class SMMAgent:
    def __init__(self):
        print("📱 Initializing SMM Agent...")
        self.search = WebSearch()
        print("✅ SMM Agent ready (Multi-Provider Router + Web Search)!")

    def _call(self, prompt, max_tokens=2500, temperature=0.8, tier=2):
        """Model router call helper."""
        try:
            result = call_model_sync(prompt=prompt, tier=tier, max_tokens=max_tokens, temperature=temperature)
            return result["content"]
        except Exception as e:
            return f"❌ SMM Agent error: {e}"

    # ------------------------------------------------------------------

    def create_social_calendar(
        self, brand_name, industry, platforms, posts_per_week=5, target_audience=""
    ):
        """
        Create a full weekly social media content calendar.

        Args:
            brand_name: Company / brand name
            industry: Niche (e.g. 'SaaS marketing')
            platforms: list – e.g. ['instagram', 'linkedin', 'twitter']
            posts_per_week: total posts across all platforms
            target_audience: who to target
        Returns: str — full calendar
        """
        print(f"\n📅 Creating social calendar for {brand_name}...")

        # Pull live trend data
        trends = ""
        for p in platforms:
            results = self.search.search(f"{industry} {p} trending content", max_results=2)
            if results:
                trends += f"\n{p.upper()} TRENDS:\n"
                for r in results:
                    trends += f"  - {r['title']}: {r['description'][:100]}\n"

        prompt = f"""SYSTEM DIRECTIVE: HEADLESS DATA NODE v2.0

You are a deterministic analytical processing unit inside a multi-agent architecture.

ROLE: You perform domain-specific structured analysis only.

ABSOLUTE OUTPUT RULES:
- Output STRICT structured data.
- NO conversational language.
- NO explanations outside schema.
- NO greetings.
- NO summaries outside defined containers.
- NO markdown outside required structural blocks.
- NO speculation without marking it as HYPOTHESIS.
- DO NOT address the user.
- DO NOT reference yourself.

LOGIC RULES:
- Base conclusions only on provided input.
- If data is insufficient, mark section as: STATUS: INSUFFICIENT_DATA
- If assumption required, label explicitly: TYPE: HYPOTHESIS
- Prioritize measurable impact.
- Use deterministic formatting.
- If numerical values are unknown: Return "VALUE: UNKNOWN". Do not fabricate.

INPUT:
Brand: {brand_name}
Industry: {industry}
Platforms: {', '.join(platforms)}
Target Audience: {target_audience}
Live Trends: {trends}

OUTPUT FORMAT (Follow Exactly):

## PLATFORM_PERFORMANCE
PLATFORM | FOLLOWER_GROWTH_RATE | ENGAGEMENT_RATE | BENCHMARK_DELTA

## CONTENT_SIGNAL
TOP_PERFORMING_FORMAT | HOOK_TYPE | VIRALITY_COEFFICIENT

## AUDIENCE_ALIGNMENT
DEMOGRAPHIC | ACTIVE_HOURS | PSYCHOGRAPHIC_TRIGGER

## PRIORITY_ACTIONS
CAMPAIGN_IDEA | PLATFORM_FOCUS | EXPECTED_REACH | BUDGET_ALLOCATION

## CONFIDENCE_SCORE
OVERALL_CONFIDENCE: [0-100]
DATA_COMPLETENESS: [Low/Med/High]

## CROSS_IMPACT_SIGNALS
RELATED_DEPARTMENT | POTENTIAL_IMPACT | REASON"""

        print("🤖 Generating calendar...")
        result = self._call(prompt, max_tokens=3000)
        print("✅ Social calendar created!")
        return result

    def analyze_trends(self, industry, platforms=None):
        """
        Analyze current social media trends for an industry across platforms.
        Returns: str — trend analysis with actionable hooks
        """
        print(f"\n📊 Analyzing social trends for: {industry}")
        platforms = platforms or ["instagram", "linkedin", "twitter", "tiktok"]

        all_trends = ""
        for p in platforms:
            results = self.search.search(f"{industry} {p} trending viral 2025", max_results=3)
            if results:
                all_trends += f"\n--- {p.upper()} ---\n"
                for r in results:
                    all_trends += f"  • {r['title']}\n    {r['description'][:150]}\n"

        prompt = f"""Analyze these social media trends for the {industry} industry:

{all_trends}

Provide:
## 1. TOP TRENDING TOPICS
- What's trending now and why
- How long each will stay relevant

## 2. CONTENT FORMAT TRENDS
- Which formats get the most engagement per platform
- Emerging styles to adopt

## 3. AUDIENCE BEHAVIOR
- Peak activity times
- What messaging resonates most

## 4. TREND HIJACK OPPORTUNITIES
- 3 specific trends you can tap into RIGHT NOW
- Exact content idea for each
- Expected engagement level

## 5. ACTION PLAN
- Top 3 immediate actions ranked by impact

Be specific and actionable."""

        result = self._call(prompt, max_tokens=2500, temperature=0.7, tier=4)
        print("✅ Trend analysis complete!")
        return result

    def write_platform_post(
        self, platform, topic, brand_voice="professional", goal="engagement", brand_name=""
    ):
        """
        Write a single optimized post for a specific platform.

        Args:
            platform: instagram | linkedin | twitter | tiktok | facebook
            topic: what to write about
            brand_voice: professional | casual | humorous | inspirational
            goal: engagement | leads | awareness | sales
            brand_name: optional
        Returns: str — complete post with caption, hashtags, visual brief
        """
        print(f"\n✍️  Writing {platform.upper()} post: {topic}")

        specs = {
            "instagram": {"hashtags": "8-15", "formats": "Reels, Carousels, Stories", "tip": "Hook first. Line breaks. End with a question."},
            "linkedin": {"hashtags": "3-5", "formats": "Text, Carousels, Video", "tip": "Share lessons learned. Be authentic. Use storytelling."},
            "twitter": {"hashtags": "1-3", "formats": "Text, Images, Threads", "tip": "Be concise and punchy. Hot takes get engagement."},
            "tiktok": {"hashtags": "5-10", "formats": "Video 15-60s, Duet, Stitch", "tip": "Hook in first 2 seconds. Follow trending sounds."},
            "facebook": {"hashtags": "3-5", "formats": "Video, Images, Links", "tip": "Ask questions. Share resources. Use groups."},
        }
        s = specs.get(platform.lower(), specs["instagram"])

        prompt = f"""Write an optimized {platform.upper()} post.

TOPIC: {topic}
BRAND: {brand_name or 'The brand'}
VOICE: {brand_voice}
GOAL: {goal}

PLATFORM RULES:
- Hashtags: {s['hashtags']}
- Best formats: {s['formats']}
- Key tip: {s['tip']}

Deliver:
## THE POST
[Full caption optimized for {platform}]

## HASHTAGS
[Optimal set]

## VISUAL BRIEF
[Describe the image or video]

## ENGAGEMENT STRATEGY
- What actions to expect
- How to respond to comments
- Follow-up content idea

## PERFORMANCE PREDICTION
- Expected engagement level and why

Write now:"""

        result = self._call(prompt, max_tokens=1500)
        print("✅ Post created!")
        return result

    def create_engagement_strategy(
        self, brand_name, industry, current_followers=0, growth_goal=""
    ):
        """
        Full engagement + growth strategy for a brand.
        Returns: str — strategy with content pillars, 30-day plan
        """
        print(f"\n🎯 Building engagement strategy for {brand_name}...")

        results = self.search.search(f"{industry} social media engagement growth strategy", max_results=3)
        research = "\n".join(
            [f"  - {r['title']}: {r['description'][:100]}" for r in (results or [])]
        )

        prompt = f"""Create a comprehensive social media engagement and growth strategy.

BRAND: {brand_name}
INDUSTRY: {industry}
CURRENT FOLLOWERS: {current_followers:,}
GROWTH GOAL: {growth_goal or 'Grow audience and increase engagement'}

MARKET RESEARCH:
{research}

Cover:
## 1. AUDIENCE PROFILE
## 2. GROWTH TACTICS (ranked by impact)
## 3. DAILY ENGAGEMENT PLAYBOOK
## 4. 5 CONTENT PILLARS (theme, types, frequency, example topics per pillar)
## 5. COMPETITOR GAPS TO EXPLOIT
## 6. KEY METRICS TO TRACK
## 7. 30-DAY ACTION PLAN (week by week)

Be specific and actionable."""

        result = self._call(prompt, max_tokens=3000, temperature=0.7, tier=4)
        print("✅ Engagement strategy ready!")
        return result

    def create_viral_hooks(self, topic, platform="instagram", count=5):
        """
        Generate scroll-stopping content hooks.
        Returns: str — N hooks with psychological triggers
        """
        print(f"\n🎣 Generating {count} viral hooks for: {topic}")

        prompt = f"""Generate {count} viral content hooks for {platform.upper()} about: {topic}

A hook is the FIRST LINE that stops someone from scrolling.
Use different psychological triggers for each:
1. Curiosity gap
2. Controversial take
3. Surprising statistic
4. Personal story opener
5. Bold claim / challenge

For each hook:
HOOK [{1}-{count}]:
  Trigger: [which psychological trigger]
  Hook: [the actual text — short, punchy]
  Follow-up: [how to continue after the hook]
  Engagement potential: [High / Medium / Low]

Make them SCROLL-STOPPING."""

        result = self._call(prompt, max_tokens=1000, temperature=0.9)
        print("✅ Hooks generated!")
        return result


# ---------------------------------------------------------------------------
# Module-level functions (matches import pattern of other agents)
# ---------------------------------------------------------------------------


def create_social_calendar(brand_name, industry, platforms, posts_per_week=5, target_audience=""):
    agent = SMMAgent()
    return agent.create_social_calendar(brand_name, industry, platforms, posts_per_week, target_audience)


def analyze_trends(industry, platforms=None):
    agent = SMMAgent()
    return agent.analyze_trends(industry, platforms)


def write_platform_post(platform, topic, brand_voice="professional", goal="engagement", brand_name=""):
    agent = SMMAgent()
    return agent.write_platform_post(platform, topic, brand_voice, goal, brand_name)


def create_engagement_strategy(brand_name, industry, current_followers=0, growth_goal=""):
    agent = SMMAgent()
    return agent.create_engagement_strategy(brand_name, industry, current_followers, growth_goal)


def create_viral_hooks(topic, platform="instagram", count=5):
    agent = SMMAgent()
    return agent.create_viral_hooks(topic, platform, count)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🧪 TESTING SMM AGENT")
    print("=" * 60)

    try:
        print("\n--- Test 1: Viral Hooks ---")
        hooks = create_viral_hooks("AI in marketing", platform="linkedin", count=3)
        print(hooks[:600] + "...")

        print("\n--- Test 2: LinkedIn Post ---")
        post = write_platform_post(
            platform="linkedin",
            topic="How AI is changing digital marketing",
            brand_voice="professional",
            goal="engagement",
            brand_name="SwarmOps",
        )
        print(post[:600] + "...")

        print("\n--- Test 3: Trend Analysis ---")
        trends = analyze_trends("SaaS marketing", platforms=["linkedin", "twitter"])
        print(trends[:600] + "...")

        print("\n✅ All SMM Agent tests complete!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
