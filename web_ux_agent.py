"""
Web/UX Agent - SwarmOps
Full-stack architect of the digital experience
Creates Linear/Emergent-style designs
Uses model_router for multi-provider AI with automatic fallback
"""

import os
from dotenv import load_dotenv
from model_router import call_model_sync

# Load environment variables
load_dotenv()


class WebUXAgent:
    """
    Web/UX Agent
    Designs and optimizes digital experiences for maximum conversion
    Uses multi-provider model router with automatic fallback
    """

    def __init__(self):
        """Initialize the Web/UX Agent"""
        print("🌐 Initializing Web/UX Agent...")
        print("✅ Web/UX Agent ready (Multi-Provider Router)!")
    
    def design_landing_page(self, product: str, target_audience: str, goal: str, 
                           style: str = "modern", key_benefits: str = "") -> str:
        """
        Design a high-converting landing page (Linear/Emergent style)
        
        Args:
            product: Product/service name
            target_audience: Who the page targets
            goal: Primary goal (signup, purchase, etc.)
            style: Design style (modern, minimal, linear, emergent)
            key_benefits: Main benefits to highlight
            
        Returns:
            Complete landing page design specification
        """
        print(f"\n🎨 Designing {style} landing page for {product}...")
        
        style_examples = {
            "linear": "Dark theme (#0a0a0a background), purple-blue accents (#5E6AD2), glassmorphism, smooth animations",
            "emergent": "Clean white/gray (#f5f5f5), bold typography, generous whitespace, subtle shadows",
            "modern": "Contemporary, balanced light/dark, gradient accents, micro-interactions",
            "minimal": "Maximum whitespace, monochrome with one accent color, simple shapes"
        }
        
        style_guide = style_examples.get(style.lower(), style_examples["modern"])
        
        prompt = f"""You are the Web/UX Agent for SwarmOps, an enterprise-grade AI marketing intelligence engine.

YOUR ROLE: Design high-converting digital experiences with specific conversion rate targets, A/B test variants, and production-ready specifications — not generic UX advice.

Product/Service: {product}
Target Audience: {target_audience}
Primary Goal: {goal}
Key Benefits: {key_benefits if key_benefits else "Not specified"}
Design Style: {style} — {style_guide}

RULES — FOLLOW ALL OF THESE:
1. Every section must have a conversion optimization rationale — WHY this element placement increases conversions (cite a UX principle or benchmark).
2. Provide conversion rate benchmarks: landing page avg 2.35% | top 25%: 5.31% | top 10%: 11.45% — state which tier this design targets.
3. Hero headline must include 3 A/B test variants. State which psychological trigger each uses (curiosity, social proof, urgency, etc.).
4. CTA button must include: exact copy, hex color, px size, hover behavior, and predicted CTR (estimated).
5. Social proof must use specific number formats ("10,000+ teams" not "many teams") — explain why specificity increases trust.
6. Every color must have a hex code. Every spacing value must be in px or rem. Every font must have px size and weight.
7. Label all predicted conversion lift estimates as "(estimated, based on [principle/benchmark])".
8. Include a friction audit: top 3 trust-killers for this specific page type and how to address each.

## CONVERSION TARGET
- Landing page avg: 2.35% | Top quartile: 5.31% | This design targets: X% — REASON: [specific design choices]

## HERO SECTION (Above the Fold)
- Background: [hex/gradient with exact values]
- Headline A (test): "[text]" — Trigger: [psychological principle]
- Headline B (test): "[text]" — Trigger: [different principle]
- Headline C (test): "[text]" — Trigger: [different principle]
- Subheadline: "[text]"
- Primary CTA: "[text]" | Color: [hex] | Size: [px] | Hover: [effect] | Predicted CTR: X% (estimated)
- Secondary CTA: "[text]" (optional)
- Trust Indicator: "[specific social proof format with number]"
- Hero Visual: [specific description at exact dimensions]

## BENEFITS SECTION
(3-4 benefits, each with: icon description + headline ≤6 words + 2-sentence description + evidence statement)

## SOCIAL PROOF SECTION
(3 testimonials, each with: specific outcome metric | name/title/company | 2-3 sentences)
(Key stats with specific numbers | logos | trust badges)

## DESIGN SYSTEM
**Colors:** Primary [hex + usage] | Secondary [hex + usage] | Accent [hex + usage] | Background [hex] | Text [hex]
**Typography:** [Font family] | H1: [px/weight] | H2: [px/weight] | Body: [px/weight] | Button: [px/weight]
**Spacing:** Section padding: [px] | Container max-width: [px] | Grid gap: [px] | Border radius: [px]
**Effects:** Shadows [CSS value] | Hover transitions [duration + easing] | Scroll animations [describe]

## FRICTION AUDIT
| Trust-Killer | Severity | Solution | Estimated CVR Lift |
|-------------|----------|----------|-------------------|

## A/B TEST PRIORITY QUEUE
1. [Element] — Hypothesis: If [change] then [metric] improves by X% because [reason] — Success metric: [KPI]
2. [Element] — same format
3. [Element] — same format

## RESPONSIVE SPECIFICATIONS
- Desktop (1200px+): [specific layout]
- Tablet (768-1199px): [specific changes with px breakpoints]
- Mobile (320-767px): [stacked layout with specific changes]

Make it production-ready, {style}-style, and inspired by Linear.app aesthetics."""

        try:
            result_data = call_model_sync(prompt=prompt, tier=2, max_tokens=3000, temperature=0.7)
            result = result_data["content"]
            print("✅ Landing page designed!")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error designing page: {str(e)}"
            print(error_msg)
            return error_msg
    
    def optimize_user_flow(self, current_flow: str, conversion_goal: str, 
                          pain_points: str = "") -> str:
        """
        Optimize user flow for better conversion
        
        Args:
            current_flow: Description of current user journey
            conversion_goal: What you want users to do
            pain_points: Known issues/friction points
            
        Returns:
            Optimized user flow with recommendations
        """
        print(f"\n🔄 Optimizing user flow for {conversion_goal}...")
        
        prompt = f"""You are a UX Flow Optimization Expert. Analyze and optimize this user flow:

CURRENT FLOW:
{current_flow}

CONVERSION GOAL:
{conversion_goal}

KNOWN PAIN POINTS:
{pain_points if pain_points else "Not specified"}

Provide:

## 1. CURRENT FLOW ANALYSIS
- Map current flow step-by-step
- Identify friction points (number each)
- Estimate drop-off at each step
- Calculate cognitive load

## 2. OPTIMIZED FLOW
- Recommended new flow (step-by-step)
- Why each change improves conversion
- Friction removed
- Expected improvement %

## 3. PSYCHOLOGICAL PRINCIPLES APPLIED
- Progressive disclosure
- Commitment & consistency
- Social proof placement
- Reciprocity
- Scarcity/Urgency

## 4. QUICK WINS (Implement First)
- 3-5 changes with highest impact
- Implementation difficulty (Easy/Medium/Hard)
- Expected conversion lift

## 5. A/B TEST PLAN
- What to test first
- Hypothesis
- Success metric

Be specific and data-driven."""

        try:
            result_data = call_model_sync(prompt=prompt, tier=3, max_tokens=2000, temperature=0.6)
            result = result_data["content"]
            print("✅ User flow optimized!")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error optimizing flow: {str(e)}"
            print(error_msg)
            return error_msg
    
    def create_wireframe_spec(self, page_type: str, key_elements: str, 
                             user_goal: str, style: str = "linear") -> str:
        """
        Create detailed wireframe specifications
        
        Args:
            page_type: Type of page (homepage, dashboard, etc.)
            key_elements: Must-have elements
            user_goal: What user needs to accomplish
            style: Design style reference
            
        Returns:
            Detailed wireframe specifications
        """
        print(f"\n📐 Creating {style}-style wireframe for {page_type}...")
        
        prompt = f"""You are a UX/UI Designer creating wireframe specifications.

PAGE TYPE: {page_type}
KEY ELEMENTS: {key_elements}
USER GOAL: {user_goal}
STYLE REFERENCE: {style} (like Linear.app if linear, or Emergent if emergent)

Create detailed wireframe specifications:

## 1. LAYOUT STRUCTURE
- Grid system (12-column, etc.)
- Header (height, elements, sticky/fixed)
- Main content areas (describe each)
- Sidebar (if any)
- Footer (height, content)

## 2. VISUAL HIERARCHY
- Primary elements (largest, most prominent)
- Secondary elements
- Tertiary elements
- Z-pattern or F-pattern reading flow

## 3. NAVIGATION
- Primary nav items (list them)
- Secondary nav
- Breadcrumbs (if needed)
- Mobile menu structure

## 4. CONTENT BLOCKS (Top to Bottom)
For each block specify:
- Purpose
- Content type
- Size/position (use px or %)
- Visual treatment
- Spacing around it

## 5. INTERACTIVE ELEMENTS
- Buttons (primary, secondary, sizes)
- Forms (fields, labels, validation)
- Dropdowns/selectors
- Modals/tooltips
- Hover states

## 6. RESPONSIVE BREAKPOINTS
- Desktop (1200px+): full layout
- Tablet (768-1199px): changes
- Mobile (320-767px): stacked layout

## 7. SPACING SYSTEM
- Padding (each section)
- Margins (between elements)
- Gaps (in grids/flexbox)

## 8. ASCII WIREFRAME
Create a simple ASCII representation:

┌─────────────────────────────────┐
│ HEADER                          │
├─────────────────────────────────┤
│                                 │
│         HERO SECTION            │
│                                 │
├─────────────────────────────────┤
etc.

Be specific and ready to hand off to developers."""

        try:
            result_data = call_model_sync(prompt=prompt, tier=2, max_tokens=2500, temperature=0.5)
            result = result_data["content"]
            print("✅ Wireframe spec created!")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error creating wireframe: {str(e)}"
            print(error_msg)
            return error_msg
    
    def analyze_ux_issues(self, page_description: str, user_feedback: str = "", 
                         metrics: str = "") -> str:
        """
        Analyze UX issues and provide recommendations
        
        Args:
            page_description: Description of the page/experience
            user_feedback: User complaints or feedback
            metrics: Relevant metrics (bounce rate, etc.)
            
        Returns:
            UX audit with prioritized recommendations
        """
        print(f"\n🔍 Analyzing UX issues...")
        
        prompt = f"""You are conducting a comprehensive UX audit.

PAGE DESCRIPTION:
{page_description}

USER FEEDBACK:
{user_feedback if user_feedback else "Not provided"}

METRICS:
{metrics if metrics else "Not provided"}

Conduct a thorough UX audit:

## 1. CRITICAL ISSUES (Fix Immediately)
For each issue:
- What's wrong
- User impact (high/medium/low)
- How to fix
- Expected improvement

## 2. HEURISTIC EVALUATION
Evaluate against:
- Visibility of system status
- User control and freedom
- Consistency and standards
- Error prevention
- Recognition vs recall
- Flexibility and efficiency
- Aesthetic and minimalist design

## 3. FRICTION POINTS
- Cognitive friction (confusing)
- Visual friction (cluttered)
- Technical friction (slow/broken)
- Trust friction (security concerns)

## 4. QUICK WINS (High Impact, Low Effort)
- List 5-7 changes
- Implementation time
- Expected conversion lift %

## 5. PRIORITIZED ROADMAP
- Week 1: Critical fixes
- Week 2-3: Major improvements
- Month 2+: Long-term enhancements

## 6. BEFORE/AFTER COMPARISON
For top 3 issues, show:
- Current state (what's wrong)
- Improved state (how to fix)
- Why it's better

Be ruthlessly honest and specific."""

        try:
            result_data = call_model_sync(prompt=prompt, tier=3, max_tokens=2000, temperature=0.6)
            result = result_data["content"]
            print("✅ UX analysis complete!")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error analyzing UX: {str(e)}"
            print(error_msg)
            return error_msg


# Simplified functions for easy use
def design_landing_page(product: str, target_audience: str, goal: str, 
                       style: str = "modern", key_benefits: str = "") -> str:
    """Design a high-converting landing page"""
    agent = WebUXAgent()
    return agent.design_landing_page(product, target_audience, goal, style, key_benefits)


def optimize_user_flow(current_flow: str, conversion_goal: str, pain_points: str = "") -> str:
    """Optimize user flow for better conversion"""
    agent = WebUXAgent()
    return agent.optimize_user_flow(current_flow, conversion_goal, pain_points)


def create_wireframe_spec(page_type: str, key_elements: str, user_goal: str, style: str = "linear") -> str:
    """Create wireframe specifications"""
    agent = WebUXAgent()
    return agent.create_wireframe_spec(page_type, key_elements, user_goal, style)


def analyze_ux_issues(page_description: str, user_feedback: str = "", metrics: str = "") -> str:
    """Analyze UX issues and provide recommendations"""
    agent = WebUXAgent()
    return agent.analyze_ux_issues(page_description, user_feedback, metrics)


# Test the agent
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING WEB/UX AGENT (GROQ)")
    print("="*60)
    
    # Test: Linear-style landing page
    print("\n--- Test: Design Linear-Style Landing Page ---")
    design = design_landing_page(
        product="TaskFlow - AI Project Management",
        target_audience="Remote software teams (5-50 people)",
        goal="Free trial signup",
        style="linear",  # Linear.app style
        key_benefits="AI-powered automation, real-time collaboration, beautiful interface"
    )
    print(f"\nDesign preview:\n{design[:500]}...")
    
    print("\n✅ Web/UX Agent test complete!")