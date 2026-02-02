"""
Content Templates for MarketingOS
Pre-built prompts for common marketing tasks
"""

class ContentTemplates:
    """Collection of professional content templates"""
    
    # Blog Post Templates
    BLOG_TEMPLATES = {
        "how_to_guide": {
            "name": "📚 How-To Guide",
            "description": "Step-by-step educational content",
            "prompt": "Write a comprehensive how-to guide about {topic} for {audience}. Include:\n- Clear introduction explaining the benefit\n- 5-7 detailed steps with examples\n- Common mistakes to avoid\n- Pro tips for best results\n- Strong conclusion with call-to-action\nMake it {length} words, {tone} tone.",
            "fields": ["topic", "audience", "length", "tone"]
        },
        "listicle": {
            "name": "📋 Listicle/Top 10",
            "description": "Numbered list article",
            "prompt": "Write an engaging listicle: 'Top {number} {topic} for {audience}'. Include:\n- Attention-grabbing introduction\n- {number} items with descriptive paragraphs for each\n- Specific examples and data points\n- Brief explanation why each matters\n- Compelling conclusion\nMake it {length} words, {tone} tone.",
            "fields": ["number", "topic", "audience", "length", "tone"]
        },
        "thought_leadership": {
            "name": "💡 Thought Leadership",
            "description": "Industry insights and trends",
            "prompt": "Write a thought leadership article about {topic} in the {industry} industry. Include:\n- Bold opening statement or question\n- Current state analysis with trends\n- Your unique perspective or prediction\n- Data and examples to support claims\n- Forward-looking conclusion\nMake it {length} words, {tone} tone.",
            "fields": ["topic", "industry", "length", "tone"]
        },
        "case_study": {
            "name": "📊 Case Study",
            "description": "Success story format",
            "prompt": "Write a case study about {topic}. Structure:\n- Challenge: What problem needed solving\n- Solution: How it was addressed\n- Results: Specific outcomes and metrics\n- Lessons learned\n- Call-to-action\nMake it {length} words, {tone} tone.",
            "fields": ["topic", "length", "tone"]
        }
    }
    
    # Social Media Templates
    SOCIAL_TEMPLATES = {
        "linkedin_post": {
            "name": "💼 LinkedIn Post",
            "description": "Professional network post",
            "prompt": "Create a LinkedIn post about {topic} for {audience}. Include:\n- Hook in first line\n- Personal insight or story\n- 3 key takeaways (use line breaks)\n- Call-to-action or question\n- 3-5 relevant hashtags\nKeep it under 150 words, {tone} tone.",
            "fields": ["topic", "audience", "tone"]
        },
        "twitter_thread": {
            "name": "🐦 Twitter/X Thread",
            "description": "Multi-tweet thread",
            "prompt": "Create a {number}-tweet thread about {topic}. Format:\n- Tweet 1: Attention-grabbing hook\n- Tweets 2-{number}: Key points (one per tweet)\n- Final tweet: Summary and CTA\nEach tweet max 280 characters, {tone} tone.",
            "fields": ["number", "topic", "tone"]
        },
        "instagram_caption": {
            "name": "📸 Instagram Caption",
            "description": "Visual social caption",
            "prompt": "Write an Instagram caption for {topic}. Include:\n- Engaging opening line\n- Story or value proposition\n- Call-to-action\n- 5-10 relevant hashtags\n- Emoji usage (but not excessive)\nMake it {tone} tone.",
            "fields": ["topic", "tone"]
        }
    }
    
    # Email Templates
    EMAIL_TEMPLATES = {
        "welcome_sequence": {
            "name": "👋 Welcome Email Sequence",
            "description": "New subscriber onboarding",
            "prompt": "Create a {number}-email welcome sequence for {product} targeting {audience}. For each email include:\n- Compelling subject line\n- Personal greeting\n- Clear value proposition\n- Single call-to-action\n- {tone} tone\n\nEmail 1: Welcome & introduce brand\nEmail 2: Key benefit/feature\nEmail 3: Social proof/testimonial\nEmail 4: Special offer/next step",
            "fields": ["number", "product", "audience", "tone"]
        },
        "promotional_email": {
            "name": "🎁 Promotional Email",
            "description": "Sales/offer announcement",
            "prompt": "Write a promotional email for {product}. Include:\n- Subject line (under 50 chars)\n- Attention-grabbing opening\n- Clear offer/discount details\n- Benefits over features\n- Urgency element\n- Strong CTA button text\n- P.S. with secondary benefit\nMake it {tone} tone.",
            "fields": ["product", "tone"]
        },
        "newsletter": {
            "name": "📰 Newsletter",
            "description": "Regular update email",
            "prompt": "Create a newsletter about {topic} for {audience}. Include:\n- Catchy subject line\n- Brief intro paragraph\n- 3-4 content sections with headlines\n- Quick tips or resources\n- What's coming next\n- Clear CTA\nMake it {tone} tone.",
            "fields": ["topic", "audience", "tone"]
        }
    }
    
    # Ad Copy Templates
    AD_TEMPLATES = {
        "google_search_ad": {
            "name": "🔍 Google Search Ad",
            "description": "PPC search ad copy",
            "prompt": "Create Google Search ad copy for {product} targeting {audience}. Include:\n- 3 headlines (max 30 chars each)\n- 2 descriptions (max 90 chars each)\n- Focus on {benefit}\n- Include call-to-action\n- {tone} tone",
            "fields": ["product", "audience", "benefit", "tone"]
        },
        "facebook_ad": {
            "name": "📱 Facebook/Meta Ad",
            "description": "Social media ad",
            "prompt": "Write a Facebook ad for {product} targeting {audience}. Include:\n- Scroll-stopping opening hook\n- Problem/solution format\n- Key benefit: {benefit}\n- Social proof element\n- Clear CTA\n- {tone} tone\nKeep it under 125 words.",
            "fields": ["product", "audience", "benefit", "tone"]
        }
    }
    
    # SEO Templates
    SEO_TEMPLATES = {
        "meta_description": {
            "name": "🔍 Meta Description",
            "description": "SEO page description",
            "prompt": "Write a meta description for a page about {topic}. Include:\n- Target keyword: {keyword}\n- Clear value proposition\n- Call-to-action\n- Under 155 characters\n- Compelling and click-worthy",
            "fields": ["topic", "keyword"]
        },
        "product_description": {
            "name": "🛍️ Product Description",
            "description": "E-commerce SEO copy",
            "prompt": "Write an SEO-optimized product description for {product}. Include:\n- Target keywords naturally\n- Key features (bullet points)\n- Benefits over features\n- Use case scenarios\n- Technical specifications\n- Strong closing CTA\nMake it {length} words, {tone} tone.",
            "fields": ["product", "length", "tone"]
        }
    }
    
    @classmethod
    def get_all_templates(cls):
        """Get all templates organized by category"""
        return {
            "Blog Posts": cls.BLOG_TEMPLATES,
            "Social Media": cls.SOCIAL_TEMPLATES,
            "Email Marketing": cls.EMAIL_TEMPLATES,
            "Ad Copy": cls.AD_TEMPLATES,
            "SEO Content": cls.SEO_TEMPLATES
        }
    
    @classmethod
    def get_template(cls, category, template_key):
        """Get a specific template"""
        all_templates = cls.get_all_templates()
        return all_templates.get(category, {}).get(template_key)
    
    @classmethod
    def fill_template(cls, template, values):
        """Fill template with user values"""
        prompt = template['prompt']
        for field, value in values.items():
            prompt = prompt.replace(f"{{{field}}}", str(value))
        return prompt


# Default values for common fields
DEFAULT_VALUES = {
    "length": "500",
    "tone": "professional",
    "audience": "business professionals",
    "number": "5"
}