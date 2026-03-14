"""
Marketing Audit Engine — SwarmOps
One URL → complete 7-section marketing intelligence report with letter grades.
Parallel execution. Anti-hallucination enforced throughout.
"""

import os
import re
import json
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Optional
from db import get_connection as _get_conn


# ---------------------------------------------------------------------------
# DB Init
# ---------------------------------------------------------------------------

def _init_tables():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS marketing_audits (
            id           TEXT PRIMARY KEY,
            url          TEXT NOT NULL,
            grade        TEXT,
            overall_score REAL,
            brand_name   TEXT,
            raw_json     TEXT,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_audits_url ON marketing_audits(url);
        CREATE INDEX IF NOT EXISTS idx_audits_created ON marketing_audits(created_at);
    """)
    conn.commit()


_init_tables()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _llm(prompt: str, system: str = "", max_tokens: int = 1024) -> str:
    """Call LLM. Returns content or '' on failure."""
    try:
        from model_router import call_model_sync
        result = call_model_sync(
            prompt=prompt,
            system_prompt=system or "You are an expert marketing analyst. Return ONLY valid JSON.",
            tier=2,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        return result.get("content", "").strip()
    except Exception as e:
        print(f"[marketing_audit] LLM error: {e}")
        return ""


def _parse_json(raw: str) -> dict:
    """Parse JSON from LLM output, stripping markdown fences."""
    try:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = re.sub(r"^```[a-z]*\n?", "", clean)
            clean = re.sub(r"\n?```$", "", clean)
        return json.loads(clean.strip())
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# MarketingAudit Class
# ---------------------------------------------------------------------------

class MarketingAudit:

    GRADE_THRESHOLDS = {
        90: "A+", 85: "A", 80: "A-", 75: "B+", 70: "B",
        65: "B-", 60: "C+", 55: "C", 50: "C-", 40: "D", 0: "F"
    }

    SCORE_WEIGHTS = {
        "seo": 0.20,
        "content": 0.15,
        "cro": 0.25,
        "messaging": 0.15,
        "competitive": 0.10,
        "growth": 0.15,
    }

    def run_full_audit(self, url: str) -> dict:
        """One URL → complete marketing intelligence report with grades."""
        try:
            if not url.startswith("http"):
                url = "https://" + url

            audit_id = str(uuid.uuid4())
            print(f"[marketing_audit] Starting full audit for {url}")

            # Step 1: Extract BrandDNA
            brand_data = {}
            try:
                from brand_dna import get_brand_dna
                result = get_brand_dna().extract(url)
                if result.get("success"):
                    brand_data = result.get("brand_dna", {})
            except Exception as e:
                print(f"[marketing_audit] BrandDNA extraction failed: {e}")

            # Step 2: Run 7 audits in parallel
            audits_to_run = {
                "seo": self._audit_seo,
                "content": self._audit_content,
                "cro": self._audit_cro,
                "messaging": self._audit_messaging,
                "ppc": self._audit_ppc_strategy,
                "competitive": self._audit_competitive,
                "growth": self._audit_growth,
            }

            results = {}
            with ThreadPoolExecutor(max_workers=7) as executor:
                futures = {
                    executor.submit(fn, url, brand_data): name
                    for name, fn in audits_to_run.items()
                }
                for future in as_completed(futures, timeout=90):
                    name = futures[future]
                    try:
                        results[name] = future.result(timeout=45)
                    except Exception as e:
                        results[name] = {"error": str(e), "score": 0}

            # Step 3: Calculate scores and grade
            scores = {}
            for section in ["seo", "content", "cro", "messaging", "competitive", "growth"]:
                scores[section] = self._extract_score(results.get(section, {}))

            overall_score = sum(
                scores.get(k, 0) * v for k, v in self.SCORE_WEIGHTS.items()
            )
            grade = self._score_to_grade(overall_score)

            # Step 4: Before/After simulation
            improvement_simulation = self._simulate_improvements(scores, brand_data)

            # Step 5: Top priority actions
            priority_actions = self._extract_priority_actions(results)

            # Step 6: Executive summary
            exec_summary = self._generate_executive_summary(
                url, brand_data, scores, grade, results
            )

            # Step 7: Assemble report
            brand_name = brand_data.get("brand_name", url)
            audit_report = {
                "id": audit_id,
                "url": url,
                "audit_date": datetime.now(timezone.utc).isoformat(),
                "brand": {
                    "name": brand_name,
                    "industry": brand_data.get("industry", "not_found"),
                    "tagline": brand_data.get("tagline", "not_found"),
                },
                "grade": grade,
                "overall_score": round(overall_score, 1),
                "scores": {
                    "seo": scores.get("seo", 0),
                    "content": scores.get("content", 0),
                    "cro": scores.get("cro", 0),
                    "messaging": scores.get("messaging", 0),
                    "competitive": scores.get("competitive", 0),
                    "growth": scores.get("growth", 0),
                },
                "executive_summary": exec_summary,
                "sections": {
                    "seo_audit": results.get("seo", {}),
                    "content_audit": results.get("content", {}),
                    "cro_audit": results.get("cro", {}),
                    "messaging_audit": results.get("messaging", {}),
                    "ppc_strategy": results.get("ppc", {}),
                    "competitive_landscape": results.get("competitive", {}),
                    "growth_opportunities": results.get("growth", {}),
                },
                "priority_actions": priority_actions[:10],
                "improvement_simulation": improvement_simulation,
            }

            # Store
            self._store_audit(audit_id, url, brand_name, grade, overall_score, audit_report)
            print(f"[marketing_audit] Audit complete: {brand_name} → {grade} ({round(overall_score, 1)})")

            return audit_report

        except Exception as e:
            print(f"[marketing_audit] run_full_audit error: {e}")
            return {"success": False, "error": str(e), "url": url}

    # -----------------------------------------------------------------------
    # Individual Audit Methods
    # -----------------------------------------------------------------------

    def _audit_seo(self, url: str, brand_data: dict) -> dict:
        """SEO audit: meta tags, keywords, content structure, technical signals."""
        brand_name = brand_data.get("brand_name", "the website")
        seo_signals = brand_data.get("seo_signals", {})
        industry = brand_data.get("industry", "unknown")
        products = brand_data.get("products_services", [])
        products_str = ", ".join(p.get("name", "") for p in products[:3]) if products else "unknown"

        prompt = f"""You are a senior SEO consultant auditing {url} for a client presentation.

Brand: {brand_name} | Industry: {industry} | Products: {products_str}
SEO signals found: {json.dumps(seo_signals)}

CRITICAL: Do NOT give generic advice. Every recommendation must be SPECIFIC to {brand_name}
and {url}. Reference actual pages, features, and keywords by name.

BAD: "Optimize meta descriptions"
GOOD: "{brand_name}'s /pricing page meta description is missing — add one that mentions
specific pricing tiers and includes the keyword '{brand_name.lower()} pricing' to capture
high-intent comparison searches"

BAD: "Add schema markup"
GOOD: "{brand_name}'s product pages lack FAQ schema — adding it to the top 5 FAQ questions
on /{products_str.split(',')[0].strip().lower().replace(' ','-') if products_str != 'unknown' else 'product'}
could earn rich snippets and increase CTR by 15-30%"

Include {brand_name} and specific page references in every recommendation.
Evaluate on a 0-100 scale across:
1. Meta tags quality (title, description, OG tags) — reference actual detected values
2. Keyword optimization for {industry} searches
3. Content structure and H-tag hierarchy
4. Technical SEO signals
5. Internal linking opportunities
6. Backlink potential given {brand_name}'s authority level

Return ONLY valid JSON:
{{
  "score": 0-100,
  "meta_score": 0-100,
  "keyword_score": 0-100,
  "content_structure_score": 0-100,
  "technical_score": 0-100,
  "top_keyword_opportunities": ["specific kw for {brand_name}", "kw2", "kw3", "kw4", "kw5"],
  "missing_meta_elements": ["specific missing element on {brand_name} site"],
  "quick_wins": ["specific fix referencing {brand_name} page/feature", "fix2", "fix3"],
  "recommendations": ["specific rec for {brand_name}", "rec2", "rec3", "rec4", "rec5"],
  "estimated_traffic_potential": "low/medium/high",
  "priority": "high/medium/low"
}}"""
        raw = _llm(prompt, max_tokens=1200)
        result = _parse_json(raw)
        if not result:
            result = {"score": 0, "error": "LLM parse failed", "recommendations": []}
        return result

    def _audit_content(self, url: str, brand_data: dict) -> dict:
        """Content audit: quality, gaps, formats, readability."""
        brand_name = brand_data.get("brand_name", "the website")
        content_strategy = brand_data.get("content_strategy", {})
        target_audience = brand_data.get("target_audience", {})
        audience_str = target_audience.get("primary", "general audience") if isinstance(target_audience, dict) else str(target_audience)
        industry = brand_data.get("industry", "general")
        pain_points = brand_data.get("customer_pain_points", [])
        pain_str = "; ".join(pain_points[:3]) if pain_points else "unknown"

        prompt = f"""You are a senior content marketing strategist auditing {url} for a CEO presentation.

Brand: {brand_name} | Industry: {industry}
Target audience: {audience_str}
Customer pain points: {pain_str}
Detected content strategy: {json.dumps(content_strategy)}

CRITICAL: Do NOT give generic advice. Every recommendation must be SPECIFIC to {brand_name}.
Reference actual content gaps for their industry and audience.

BAD: "Create more blog content"
GOOD: "{brand_name} has no content addressing '{pain_str.split(';')[0].strip() if pain_str != 'unknown' else 'key pain points'}' —
this is the #1 objection for {industry} buyers and competitors like [Competitor] own this keyword cluster"

BAD: "Add case studies"
GOOD: "{brand_name}'s website shows no customer success stories despite serving {audience_str} —
a 3-part case study series showing ROI metrics would directly address the 'does this actually work?' objection
in the consideration stage"

Include {brand_name} specifically in every recommendation.

Evaluate on a 0-100 scale:
1. Content quality and depth relative to {industry} standards
2. Topic coverage of {audience_str} pain points
3. Content gap opportunities vs competitors
4. Readability and engagement for {audience_str}
5. Format diversity (video, guides, case studies)
6. SEO-content alignment for {industry} keywords

Return ONLY valid JSON:
{{
  "score": 0-100,
  "quality_score": 0-100,
  "coverage_score": 0-100,
  "engagement_score": 0-100,
  "blog_exists": true,
  "content_gaps": ["specific gap for {brand_name}", "gap2", "gap3"],
  "top_content_ideas": ["specific idea for {brand_name} audience", "idea2", "idea3", "idea4", "idea5"],
  "missing_formats": ["specific missing format for {brand_name}", "format2"],
  "recommendations": ["specific rec for {brand_name}", "rec2", "rec3", "rec4", "rec5"],
  "content_calendar_suggestion": "weekly/biweekly/monthly",
  "priority": "high/medium/low"
}}"""
        raw = _llm(prompt, max_tokens=1200)
        result = _parse_json(raw)
        if not result:
            result = {"score": 0, "error": "LLM parse failed", "recommendations": []}
        return result

    def _audit_cro(self, url: str, brand_data: dict) -> dict:
        """CRO audit: CTAs, trust signals, friction points, conversion flow."""
        brand_name = brand_data.get("brand_name", "the website")
        cta_patterns = brand_data.get("cta_patterns", [])
        trust_signals = brand_data.get("trust_signals", {})
        marketing_funnel = brand_data.get("marketing_funnel", {})
        biz_objectives = brand_data.get("business_objectives", {})
        conversion_type = biz_objectives.get("conversion_type", "signup") if isinstance(biz_objectives, dict) else "signup"
        sales_motion = biz_objectives.get("sales_motion", "self-serve") if isinstance(biz_objectives, dict) else "self-serve"
        industry = brand_data.get("industry", "general")
        ctas_str = ", ".join(f'"{c}"' for c in cta_patterns[:5]) if cta_patterns else "none detected"

        prompt = f"""You are a senior CRO consultant auditing {url} for a board presentation.

Brand: {brand_name} | Industry: {industry} | Sales motion: {sales_motion}
Primary conversion goal: {conversion_type}
Detected CTAs on site: {ctas_str}
Trust signals detected: {json.dumps(trust_signals)}
Funnel data: {json.dumps(marketing_funnel)}

CRITICAL: Do NOT give generic CRO advice. Every recommendation must name {brand_name}
and specific pages/elements observed on their actual site.

BAD: "Add testimonials to the homepage"
GOOD: "{brand_name}'s homepage hero section has no social proof — adding 3 customer logos
from recognizable {industry} brands above the fold would increase trial signups by an estimated 12-18%
(industry benchmark: social proof near CTA improves conversion 15-30%)"

BAD: "Improve your CTA button"
GOOD: "{brand_name}'s primary CTA '{cta_patterns[0] if cta_patterns else 'Start now'}' on the
homepage doesn't communicate the value exchange — changing to 'Start free — no credit card required'
eliminates the #1 conversion blocker for {industry} {conversion_type} flows"

Reference the actual CTAs ({ctas_str}) in your analysis.
Compare to {industry} conversion benchmarks.

Evaluate on a 0-100 scale:
1. CTA effectiveness of {brand_name}'s current CTAs
2. Trust signals for {industry} buyers
3. Friction points in {conversion_type} flow
4. Social proof quality and placement
5. Value proposition clarity at decision points
6. Mobile conversion UX

Return ONLY valid JSON:
{{
  "score": 0-100,
  "cta_score": 0-100,
  "trust_score": 0-100,
  "flow_score": 0-100,
  "social_proof_score": 0-100,
  "friction_points": ["specific friction on {brand_name} site", "friction2", "friction3"],
  "missing_trust_elements": ["specific element {brand_name} is missing", "element2"],
  "cta_improvements": ["specific improvement for {brand_name}'s actual CTAs", "improvement2", "improvement3"],
  "quick_wins": ["specific win for {brand_name}", "win2", "win3"],
  "recommendations": ["specific rec for {brand_name}", "rec2", "rec3", "rec4", "rec5"],
  "estimated_conversion_lift": "+X-Y%",
  "priority": "high/medium/low"
}}"""
        raw = _llm(prompt, max_tokens=1200)
        result = _parse_json(raw)
        if not result:
            result = {"score": 0, "error": "LLM parse failed", "recommendations": []}
        return result

    def _audit_messaging(self, url: str, brand_data: dict) -> dict:
        """Messaging audit: headline clarity, value prop strength, differentiation."""
        value_prop = brand_data.get("value_proposition", {})
        brand_positioning = brand_data.get("brand_positioning", {})
        brand_name = brand_data.get("brand_name", "the website")
        vp_primary = value_prop.get("primary", "") if isinstance(value_prop, dict) else str(value_prop)
        differentiator = value_prop.get("unique_differentiator", "") if isinstance(value_prop, dict) else ""
        industry = brand_data.get("industry", "general")
        target_audience = brand_data.get("target_audience", {})
        audience_str = target_audience.get("primary", "businesses") if isinstance(target_audience, dict) else str(target_audience)
        seo_h1 = brand_data.get("seo_signals", {}).get("h1_text", "not detected")

        prompt = f"""You are a brand messaging expert and copywriter auditing {url} for a pitch deck.

Brand: {brand_name} | Industry: {industry} | Audience: {audience_str}
Detected homepage H1: "{seo_h1}"
Current value proposition: {vp_primary}
Unique differentiator claimed: {differentiator}
Positioning: {json.dumps(brand_positioning)}

CRITICAL: Do NOT give generic messaging advice. Reference {brand_name}'s ACTUAL detected
messaging, headlines, and positioning in every recommendation.

BAD: "Make your headline clearer"
GOOD: "{brand_name}'s current H1 '{seo_h1}' is feature-focused rather than benefit-focused —
'{audience_str} that use {brand_name} achieve [specific outcome]' would speak directly to {audience_str}
decision-makers rather than just describing the product"

BAD: "Improve differentiation"
GOOD: "{brand_name}'s current differentiator '{differentiator}' is too broad — in {industry},
[Competitor A] and [Competitor B] say the same thing. Adding a specific, verifiable claim like
'[X] {industry} companies saved [Y] hours using {brand_name}' creates a defensible position"

Write 3 alternative headlines that would outperform {brand_name}'s current messaging.
Make them specific, benefit-led, and audience-targeted.

Evaluate on a 0-100 scale:
1. Headline clarity — does {seo_h1} immediately communicate value?
2. Value proposition strength vs {industry} competitors
3. Differentiation quality of {differentiator}
4. Emotional resonance for {audience_str}
5. Audience specificity — does it speak to {audience_str}?
6. Message consistency across {url} pages

Return ONLY valid JSON:
{{
  "score": 0-100,
  "headline_clarity": 0-100,
  "value_prop_strength": 0-100,
  "differentiation": 0-100,
  "emotional_appeal": 0-100,
  "audience_clarity": 0-100,
  "weaknesses": ["specific weakness in {brand_name}'s messaging", "weakness2", "weakness3"],
  "improved_headlines": ["specific better headline for {brand_name}", "alternative 2", "alternative 3"],
  "improved_taglines": ["specific tagline for {brand_name}", "alternative tagline"],
  "recommendations": ["specific rec referencing {brand_name}'s actual messaging", "rec2", "rec3"],
  "priority": "high/medium/low"
}}"""
        raw = _llm(prompt, max_tokens=1200)
        result = _parse_json(raw)
        if not result:
            result = {"score": 0, "error": "LLM parse failed", "recommendations": []}
        return result

    def _audit_ppc_strategy(self, url: str, brand_data: dict) -> dict:
        """PPC strategy: keyword recommendations, ad copy, budget guidance, ROAS estimates."""
        brand_name = brand_data.get("brand_name", "the business")
        industry = brand_data.get("industry", "general")
        target_audience = brand_data.get("target_audience", {})
        audience = target_audience.get("primary", "businesses") if isinstance(target_audience, dict) else str(target_audience)
        pricing = brand_data.get("pricing", {})
        pricing_model = pricing.get("model", "unknown") if isinstance(pricing, dict) else str(pricing)
        starting_price = pricing.get("starting_price", "unknown") if isinstance(pricing, dict) else "unknown"
        products = brand_data.get("products_services", [])
        top_product = products[0].get("name", brand_name) if products else brand_name

        prompt = f"""You are a senior PPC strategist building a paid media plan for {url}.

Brand: {brand_name} | Industry: {industry} | Pricing: {pricing_model} (from {starting_price})
Primary product to advertise: {top_product}
Target buyer: {audience}

CRITICAL: Every keyword, ad headline, and recommendation must be SPECIFIC to {brand_name}
and its actual products/audience. Do not use placeholder text.

Write actual Google Search ad headlines for {brand_name}'s {top_product}.
Recommend actual keywords a {industry} buyer would search when looking for {top_product}.
Suggest actual channels based on where {audience} spend time.

Example of GOOD keyword: "{brand_name.lower()} {industry.lower()} solution" — high-intent, brand+category
Example of GOOD headline: "{top_product} — Try {brand_name} Free | No Credit Card" — benefit + CTA

Return ONLY valid JSON:
{{
  "score": 0-100,
  "recommended_keywords": [
    {{"keyword": "actual keyword for {brand_name}", "estimated_cpc": "$X.XX", "intent": "high/medium/low"}}
  ],
  "negative_keywords": ["actual negative kw for {brand_name}", "kw2", "kw3"],
  "ad_headlines": ["actual headline for {brand_name}", "headline2", "headline3"],
  "ad_descriptions": ["actual description for {brand_name}", "desc2"],
  "channel_recommendations": [
    {{"channel": "specific channel for {audience}", "budget_pct": 40, "rationale": "why for {brand_name}"}}
  ],
  "budget_guidance": {{
    "minimum_monthly": "$X,XXX",
    "recommended_monthly": "$X,XXX",
    "expected_roas": "X.X"
  }},
  "recommendations": ["specific rec for {brand_name} PPC", "rec2", "rec3"],
  "priority": "high/medium/low"
}}"""
        raw = _llm(prompt, max_tokens=1400)
        result = _parse_json(raw)
        if not result:
            result = {"score": 0, "error": "LLM parse failed", "recommendations": []}
        return result

    def _audit_competitive(self, url: str, brand_data: dict) -> dict:
        """Competitive audit: identify top competitors, gaps, threats, opportunities."""
        brand_name = brand_data.get("brand_name", "the business")
        industry = brand_data.get("industry", "general")
        comps_data = brand_data.get("competitors", {})
        mentioned = comps_data.get("mentioned_on_site", []) if isinstance(comps_data, dict) else []
        implied = comps_data.get("implied_competitors", []) if isinstance(comps_data, dict) else []
        bp = brand_data.get("brand_positioning", {})
        differentiators = bp.get("key_differentiators", []) if isinstance(bp, dict) else []
        market_pos = bp.get("market_position", "mid-market") if isinstance(bp, dict) else "mid-market"
        target_audience = brand_data.get("target_audience", {})
        audience_str = target_audience.get("primary", "businesses") if isinstance(target_audience, dict) else str(target_audience)

        prompt = f"""You are a senior competitive intelligence analyst preparing a competitive brief for {brand_name}.

Brand: {brand_name} | Industry: {industry} | Market position: {market_pos}
Target audience: {audience_str}
Competitors mentioned on {brand_name}'s site: {mentioned}
Implied competitors from positioning: {implied}
{brand_name}'s claimed differentiators: {differentiators}

CRITICAL: Name actual real competitors in the {industry} space. Be specific about
{brand_name}'s relative strengths and weaknesses vs each named competitor.

BAD: "Competitor A has better pricing"
GOOD: "Brex offers 10x points on rideshares vs Stripe's standard 1x — Stripe should counter with
developer-first tooling that Brex lacks, specifically the API documentation and webhook ecosystem"

Identify 3-5 REAL named competitors in {industry} that {brand_name} competes with directly.
For each, name their URL, their #1 strength {brand_name} lacks, and {brand_name}'s specific advantage.

Return ONLY valid JSON:
{{
  "score": 0-100,
  "top_competitors": [
    {{
      "name": "real competitor name",
      "url": "competitor.com",
      "threat_level": "high/medium/low",
      "their_strength": "specific strength vs {brand_name}",
      "your_advantage": "specific advantage {brand_name} has over them"
    }}
  ],
  "market_gaps": ["specific gap {brand_name} can fill", "gap2", "gap3"],
  "competitive_strengths": ["specific strength {brand_name} has", "strength2", "strength3"],
  "competitive_weaknesses": ["specific weakness vs named competitor", "weakness2"],
  "opportunities": ["specific opportunity for {brand_name}", "opportunity2", "opportunity3"],
  "recommendations": ["specific rec for {brand_name} vs competitors", "rec2", "rec3"],
  "overall_competitive_position": "leading/competitive/lagging",
  "priority": "high/medium/low"
}}"""
        raw = _llm(prompt, max_tokens=1400)
        result = _parse_json(raw)
        if not result:
            result = {"score": 0, "error": "LLM parse failed", "recommendations": []}
        return result

    def _audit_growth(self, url: str, brand_data: dict) -> dict:
        """Growth audit: top 5 opportunities ranked by impact vs effort."""
        brand_name = brand_data.get("brand_name", "the business")
        industry = brand_data.get("industry", "general")
        biz_obj = brand_data.get("business_objectives", {})
        goal = biz_obj.get("primary_goal", "growth") if isinstance(biz_obj, dict) else "growth"
        sales_motion = biz_obj.get("sales_motion", "self-serve") if isinstance(biz_obj, dict) else "self-serve"
        auth_signals = brand_data.get("authority_signals", {})
        marketing_funnel = brand_data.get("marketing_funnel", {})
        social_presence = brand_data.get("social_presence", {})
        platforms = social_presence.get("platforms_detected", []) if isinstance(social_presence, dict) else []
        target_audience = brand_data.get("target_audience", {})
        audience_str = target_audience.get("primary", "businesses") if isinstance(target_audience, dict) else str(target_audience)
        content_strategy = brand_data.get("content_strategy", {})
        blog_exists = content_strategy.get("blog_exists", False) if isinstance(content_strategy, dict) else False

        prompt = f"""You are a growth strategist who has scaled {industry} companies.
Identify the top growth opportunities for {brand_name} ({url}).

Brand context:
- Goal: {goal} | Sales motion: {sales_motion}
- Target: {audience_str}
- Social platforms active: {platforms}
- Blog/content exists: {blog_exists}
- Authority signals: {json.dumps(auth_signals)}
- Funnel: {json.dumps(marketing_funnel)}

CRITICAL: Every opportunity must be SPECIFIC to {brand_name}'s actual situation.
Reference their industry ({industry}), audience ({audience_str}), and current gaps.

BAD: "Launch a referral program"
GOOD: "{brand_name} has no referral mechanism despite serving {audience_str} who heavily trust
peer recommendations — a 'Give $X, Get $X' referral program targeting their existing {sales_motion}
customers could drive 20-30% of new signups within 90 days (benchmark: Dropbox grew 3900% via referral)"

BAD: "Create more content"
GOOD: "{brand_name} has {'a blog' if blog_exists else 'no blog'} but {'social media on' if platforms else 'no detected social presence'} —
launching a weekly {industry}-focused newsletter targeting {audience_str} decision-makers
would compound authority over 6 months and capture email leads at $0 CAC"

Name specific channels, metrics, and outcomes for {brand_name}.

Return ONLY valid JSON:
{{
  "score": 0-100,
  "opportunities": [
    {{
      "title": "specific opportunity title for {brand_name}",
      "description": "specific description referencing {brand_name}'s situation",
      "impact": "high/medium/low",
      "effort": "high/medium/low",
      "timeline": "1-2 weeks/1 month/3 months",
      "expected_result": "specific metric outcome for {brand_name}",
      "action_steps": ["specific step for {brand_name}", "step2", "step3"]
    }}
  ],
  "quick_wins": ["specific quick win for {brand_name}", "win2", "win3"],
  "long_term_plays": ["specific play for {brand_name}", "play2"],
  "untapped_channels": ["specific channel for {audience_str}", "channel2"],
  "recommendations": ["specific rec for {brand_name}", "rec2", "rec3", "rec4", "rec5"],
  "priority": "high/medium/low"
}}"""
        raw = _llm(prompt, max_tokens=1400)
        result = _parse_json(raw)
        if not result:
            result = {"score": 0, "error": "LLM parse failed", "recommendations": []}
        return result

    # -----------------------------------------------------------------------
    # Scoring and Grading
    # -----------------------------------------------------------------------

    def _extract_score(self, section_result: dict) -> float:
        """Extract numeric score from an audit section result."""
        if not section_result:
            return 0
        score = section_result.get("score", 0)
        try:
            return float(score)
        except (ValueError, TypeError):
            return 0

    def _score_to_grade(self, score: float) -> str:
        for threshold, grade in sorted(self.GRADE_THRESHOLDS.items(), reverse=True):
            if score >= threshold:
                return grade
        return "F"

    def _simulate_improvements(self, scores: dict, brand_data: dict) -> dict:
        """Before/After improvement simulator with revenue estimates."""
        improvements = {}

        for section, score in scores.items():
            if score < 50:
                potential_lift = "high"
                traffic_impact = "+25-40%"
                conversion_impact = "+15-25%"
            elif score < 70:
                potential_lift = "medium"
                traffic_impact = "+15-25%"
                conversion_impact = "+8-15%"
            elif score < 85:
                potential_lift = "low"
                traffic_impact = "+5-15%"
                conversion_impact = "+3-8%"
            else:
                potential_lift = "minimal"
                traffic_impact = "+1-5%"
                conversion_impact = "+1-3%"

            improvements[section] = {
                "current_score": round(score, 1),
                "potential_score": min(round(score + 20, 1), 95),
                "potential_lift": potential_lift,
                "traffic_impact": traffic_impact,
                "conversion_impact": conversion_impact,
            }

        avg_score = sum(scores.values()) / max(len(scores), 1)
        if avg_score < 50:
            revenue_opportunity = "$50K-100K/year potential"
        elif avg_score < 70:
            revenue_opportunity = "$20K-50K/year potential"
        else:
            revenue_opportunity = "$5K-20K/year potential"

        return {
            "sections": improvements,
            "overall": {
                "current_grade": self._score_to_grade(avg_score),
                "potential_grade": self._score_to_grade(min(avg_score + 15, 95)),
                "estimated_traffic_increase": "+15-35%",
                "estimated_conversion_increase": "+10-20%",
                "estimated_revenue_opportunity": revenue_opportunity,
                "timeframe": "3-6 months with consistent execution",
            },
        }

    def _extract_priority_actions(self, results: dict) -> list:
        """Pull top recommendations from all audit sections, deduplicated."""
        actions = []

        section_priority_map = {
            "cro": "high",
            "messaging": "high",
            "seo": "medium",
            "growth": "medium",
            "content": "medium",
            "competitive": "medium",
            "ppc": "low",
        }

        for section, result in results.items():
            if not isinstance(result, dict):
                continue
            recs = result.get("recommendations", [])
            quick_wins = result.get("quick_wins", [])
            priority = result.get("priority", section_priority_map.get(section, "medium"))

            for qw in quick_wins[:2]:
                if qw and isinstance(qw, str):
                    actions.append({
                        "action": qw,
                        "section": section,
                        "type": "quick_win",
                        "priority": "high",
                    })

            for rec in recs[:3]:
                if rec and isinstance(rec, str):
                    actions.append({
                        "action": rec,
                        "section": section,
                        "type": "recommendation",
                        "priority": priority,
                    })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        actions.sort(key=lambda x: (
            priority_order.get(x.get("priority", "medium"), 1),
            0 if x.get("type") == "quick_win" else 1
        ))

        # Deduplicate similar actions
        seen = set()
        deduped = []
        for action in actions:
            key = action["action"][:50].lower()
            if key not in seen:
                seen.add(key)
                deduped.append(action)

        return deduped[:10]

    def _generate_executive_summary(
        self, url: str, brand_data: dict, scores: dict, grade: str, results: dict
    ) -> str:
        """Generate an LLM-written executive summary like a senior consultant."""
        brand_name = brand_data.get("brand_name", url)
        industry = brand_data.get("industry", "General Business")

        # Key findings to inform the LLM
        if scores:
            best_section = max(scores, key=scores.get)
            worst_section = min(scores, key=scores.get)
            best_score = round(scores[best_section], 1)
            worst_score = round(scores[worst_section], 1)
        else:
            best_section = worst_section = "overall"
            best_score = worst_score = 0

        # Top quick win from most impactful section
        top_finding = ""
        for section in ["cro", "messaging", "seo", "growth"]:
            s_result = results.get(section, {})
            qw = s_result.get("quick_wins", [])
            if qw:
                top_finding = qw[0]
                break

        prompt = f"""Write a 3-4 sentence executive summary of this marketing audit for a CEO presentation.

Brand: {brand_name} | URL: {url} | Industry: {industry}
Overall Grade: {grade}
Scores: SEO {scores.get('seo', 0)}/100, Content {scores.get('content', 0)}/100, CRO {scores.get('cro', 0)}/100, Messaging {scores.get('messaging', 0)}/100, Competitive {scores.get('competitive', 0)}/100, Growth {scores.get('growth', 0)}/100
Strongest area: {best_section.upper()} ({best_score}/100)
Biggest opportunity: {worst_section.upper()} ({worst_score}/100)
Top finding: {top_finding}

Write like a senior marketing consultant presenting to a CEO.
Be specific about {brand_name}'s actual strengths and weaknesses.
Do NOT use bullet points. Write in professional prose.
Do NOT be generic. Mention {brand_name} by name.
Return ONLY the summary text, no JSON, no headers."""

        summary = _llm(prompt, system="You are a senior marketing consultant. Write concise, specific executive summaries.", max_tokens=300)

        if not summary or len(summary) < 50:
            # Fallback: structured string
            summary = (
                f"{brand_name} received a marketing grade of {grade} in the {industry} sector, "
                f"with notable strength in {best_section.upper()} ({best_score}/100) "
                f"and the greatest opportunity in {worst_section.upper()} ({worst_score}/100). "
                f"{'Priority action: ' + top_finding + ' ' if top_finding else ''}"
                f"With focused execution over 3-6 months, {brand_name} can achieve significant improvements "
                f"in organic traffic, conversion rate, and revenue."
            )

        return summary

    # -----------------------------------------------------------------------
    # Storage
    # -----------------------------------------------------------------------

    def _store_audit(
        self, audit_id: str, url: str, brand_name: str,
        grade: str, overall_score: float, report: dict
    ):
        try:
            conn = _get_conn()
            conn.execute(
                """INSERT INTO marketing_audits
                   (id, url, grade, overall_score, brand_name, raw_json)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (audit_id, url, grade, round(overall_score, 1), brand_name, json.dumps(report))
            )
            conn.commit()
        except Exception as e:
            print(f"[marketing_audit] _store_audit error: {e}")

    def get_audit_history(self, limit: int = 20) -> list:
        """Return list of past audits (summary only, not full report)."""
        try:
            conn = _get_conn()
            rows = conn.execute(
                """SELECT id, url, grade, overall_score, brand_name, created_at
                   FROM marketing_audits ORDER BY created_at DESC LIMIT ?""",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"[marketing_audit] get_audit_history error: {e}")
            return []

    def get_audit_by_id(self, audit_id: str) -> Optional[dict]:
        """Return a full stored audit report by ID."""
        try:
            conn = _get_conn()
            row = conn.execute(
                "SELECT raw_json FROM marketing_audits WHERE id = ?", (audit_id,)
            ).fetchone()
            if not row:
                return None
            return json.loads(row["raw_json"])
        except Exception as e:
            print(f"[marketing_audit] get_audit_by_id error: {e}")
            return None


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_audit_instance: Optional[MarketingAudit] = None


def get_marketing_audit() -> MarketingAudit:
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = MarketingAudit()
    return _audit_instance
