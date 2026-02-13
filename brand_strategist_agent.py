"""
Brand Strategist Agent - MarketingOS 2.0
Guardian of brand DNA and market positioning
Uses model_router for multi-provider AI with automatic fallback
"""

import os
from dotenv import load_dotenv
from model_router import call_model_sync

# Load environment variables
load_dotenv()


class BrandStrategistAgent:
    """
    Brand Strategist Agent
    Ensures brand consistency and develops positioning strategies
    Uses multi-provider model router with automatic fallback
    """

    def __init__(self):
        """Initialize the Brand Strategist Agent"""
        print("🎨 Initializing Brand Strategist Agent...")
        print("✅ Brand Strategist Agent ready (Multi-Provider Router)!")
    
    def create_brand_strategy(self, company_name: str, industry: str, target_audience: str, unique_value: str = "") -> str:
        """
        Create comprehensive brand strategy
        
        Args:
            company_name: Name of the company/brand
            industry: Industry/sector
            target_audience: Primary target audience
            unique_value: Unique value proposition
            
        Returns:
            Complete brand strategy document
        """
        print(f"\n🎨 Creating brand strategy for {company_name}...")
        
        prompt = f"""You are an expert Brand Strategist. Create a comprehensive brand strategy for:

Company: {company_name}
Industry: {industry}
Target Audience: {target_audience}
Unique Value: {unique_value if unique_value else "Not specified"}

Provide a detailed brand strategy including:

1. BRAND POSITIONING
   - Market position
   - Competitive differentiation
   - Brand promise

2. BRAND PERSONALITY
   - Core values (3-5)
   - Brand archetype
   - Personality traits

3. TONE OF VOICE
   - Communication style
   - Do's and Don'ts
   - Example phrases

4. VISUAL IDENTITY DIRECTION
   - Color palette suggestions
   - Typography direction
   - Visual style guidance

5. MESSAGING FRAMEWORK
   - Core message
   - Key messages (3-5)
   - Elevator pitch

6. BRAND GUIDELINES
   - Usage rules
   - Consistency checklist

Make it actionable, specific, and professional."""

        try:
            result_data = call_model_sync(prompt=prompt, tier=3, max_tokens=2500, temperature=0.7)
            result = result_data["content"]
            print("✅ Brand strategy created!")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error creating brand strategy: {str(e)}"
            print(error_msg)
            return error_msg
    
    def define_tone_of_voice(self, brand_name: str, brand_personality: str, target_audience: str) -> str:
        """
        Define brand tone of voice
        
        Args:
            brand_name: Brand name
            brand_personality: Personality traits
            target_audience: Who the brand speaks to
            
        Returns:
            Tone of voice guidelines
        """
        print(f"\n🗣️ Defining tone of voice for {brand_name}...")
        
        prompt = f"""You are a Brand Voice Expert. Define the tone of voice for:

Brand: {brand_name}
Personality: {brand_personality}
Audience: {target_audience}

Create detailed tone of voice guidelines including:

1. VOICE CHARACTERISTICS
   - 4-5 defining traits (e.g., friendly, authoritative, playful)
   - How these traits manifest in communication

2. LANGUAGE STYLE
   - Vocabulary level
   - Sentence structure
   - Technical vs. simple language

3. DO's
   - 5+ specific examples of what to do
   - Sample phrases that embody the voice

4. DON'Ts
   - 5+ specific examples of what to avoid
   - Counter-examples of off-brand communication

5. TONE VARIATIONS
   - Formal contexts (e.g., legal, official)
   - Casual contexts (e.g., social media, blogs)
   - Crisis communication

6. EXAMPLES
   - 3 sample sentences in brand voice
   - 3 sample sentences NOT in brand voice

Make it practical and easy to follow."""

        try:
            result_data = call_model_sync(prompt=prompt, tier=3, max_tokens=2000, temperature=0.7)
            result = result_data["content"]
            print("✅ Tone of voice defined!")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error defining tone: {str(e)}"
            print(error_msg)
            return error_msg
    
    def analyze_brand_consistency(self, content: str, brand_guidelines: str) -> str:
        """
        Analyze content for brand consistency
        
        Args:
            content: Content to analyze
            brand_guidelines: Brand guidelines to check against
            
        Returns:
            Consistency analysis and recommendations
        """
        print(f"\n🔍 Analyzing brand consistency...")
        
        prompt = f"""You are a Brand Compliance Analyst. Review this content against brand guidelines:

BRAND GUIDELINES:
{brand_guidelines[:500]}

CONTENT TO REVIEW:
{content[:1000]}

Provide a detailed analysis:

1. CONSISTENCY SCORE (1-10)
   - Overall alignment with brand

2. TONE ANALYSIS
   - Does it match brand voice?
   - Specific examples of alignment/misalignment

3. MESSAGING ANALYSIS
   - Key messages present or missing
   - Brand values reflected

4. VIOLATIONS (if any)
   - Specific issues
   - Severity level

5. RECOMMENDATIONS
   - What to fix
   - How to improve
   - Specific rewrites if needed

6. APPROVAL STATUS
   - Approve / Approve with changes / Reject
   - Reasoning

Be specific and constructive."""

        try:
            result_data = call_model_sync(prompt=prompt, tier=3, max_tokens=1500, temperature=0.5)
            result = result_data["content"]
            print("✅ Brand consistency analyzed!")
            return result
            
        except Exception as e:
            error_msg = f"❌ Error analyzing consistency: {str(e)}"
            print(error_msg)
            return error_msg


# Simplified functions for easy use
def create_brand_strategy(company_name: str, industry: str, target_audience: str, unique_value: str = "") -> str:
    """Create comprehensive brand strategy"""
    agent = BrandStrategistAgent()
    return agent.create_brand_strategy(company_name, industry, target_audience, unique_value)


def define_tone_of_voice(brand_name: str, brand_personality: str, target_audience: str) -> str:
    """Define brand tone of voice guidelines"""
    agent = BrandStrategistAgent()
    return agent.define_tone_of_voice(brand_name, brand_personality, target_audience)


def analyze_brand_consistency(content: str, brand_guidelines: str) -> str:
    """Analyze content for brand consistency"""
    agent = BrandStrategistAgent()
    return agent.analyze_brand_consistency(content, brand_guidelines)


# Test the agent
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING BRAND STRATEGIST AGENT (GROQ)")
    print("="*60)
    
    # Test: Brand Strategy
    print("\n--- Test: Brand Strategy ---")
    strategy = create_brand_strategy(
        company_name="EcoClean",
        industry="Sustainable cleaning products",
        target_audience="Environmentally conscious millennials",
        unique_value="100% plastic-free packaging"
    )
    print(f"\nResult preview:\n{strategy[:400]}...")
    
    print("\n✅ Brand Strategist Agent test complete!")