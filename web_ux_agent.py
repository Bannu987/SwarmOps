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
""" + """
RESPONSE QUALITY RULES:

LENGTH:
- Default: 4-8 sentences. Do not exceed this unless the user asks for a detailed plan, audit, or full analysis.
- Short questions → 2-4 sentences
- Normal requests → 4-8 sentences

FORMAT:
- Use short bullet lists (3-5 items) for recommendations.
- Each bullet = one specific, actionable sentence.
- Short numbered lists (1-5 items) are encouraged for clarity.

SPECIFICITY:
- Never give vague advice. Every recommendation must be specific.
- BAD: 'Improve your SEO' → GOOD: 'Write a guide targeting the keyword "AI marketing tools"'
- BAD: 'Create good content' → GOOD: 'Publish a case study on how AI tools increased client traffic by 40%'
- If you cannot be specific without more info, say exactly what info you need.

NO TEMPLATES:
- Avoid: 'Critical Issues', 'Strategic Roadmap', 'Heuristic Evaluation', 'Assessment Matrix', 'Action Architecture'
- Short numbered lists (1-5 items) ARE allowed and encouraged.
"""


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
        
        prompt = f"""You are a senior UX/web designer. Design a high-converting landing page for the product below.

Product/Service: {product}
Target Audience: {target_audience}
Goal: {goal}
Key Benefits: {key_benefits}
Style: {style} — {style_guide}

RESPONSE FORMAT:
Present UX recommendations conversationally. Identify specific friction points and suggest improvements with expected impact on conversions.
End with: "**Next step:** [specific action]"
""" + AGENT_CONVERSATIONAL_RULES

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