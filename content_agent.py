"""
Content Agent - MarketingOS 2.0
Uses model_router for multi-provider AI with automatic fallback
"""

import os
from dotenv import load_dotenv
from model_router import call_model_sync

# Load environment variables
load_dotenv()

print("🔧 Initializing Content Agent...")
print("✅ Content Agent ready (Multi-Provider Router)!")

# Function to use the agent
def generate_content(user_request, max_length=2000):
    """
    Generate content based on user request
    
    Args:
        user_request (str): What the user wants written
        max_length (int): Maximum length of content
        
    Returns:
        str: The generated content
    """
    print(f"\n📝 Content Agent is working on: '{user_request}'")
    print("⏳ Generating content... (this may take 5-15 seconds)")
    
    try:
        # Check memory for past content to avoid repetition
        past_context = ""
        try:
            from memory_store import get_memory_store
            past = get_memory_store().recall_memories("content", limit=5)
            if past:
                past_lines = "\n".join(f"  - {m['content']}" for m in past)
                past_context = f"\n\nWe already wrote about:\n{past_lines}\nTake a fresh angle or cover something we haven't addressed.\n"
        except Exception:
            pass

        # Create the prompt
        prompt = f"""You are a helpful content writing assistant.
Your job is to write high-quality content based on the user's request.
{past_context}
User Request: {user_request}

Please write the content now:"""
        
        # Call model router (tier 2 = content generation)
        result_data = call_model_sync(prompt=prompt, tier=2, max_tokens=max_length, temperature=0.7)
        result = result_data["content"]
        
        print("✅ Content generated!\n")
        return result
        
    except Exception as e:
        error_msg = f"❌ Error generating content: {str(e)}"
        print(error_msg)
        return error_msg


# ==============================================================
# REAL EXECUTION LAYER — MarketingOS 2.0 Upgrade
# Publishes content directly to WordPress.
# Falls back to text-only mode if WordPress is not configured.
# ==============================================================


def generate_and_publish(topic, post_type="blog", status="draft", categories=None, seo_keywords=None):
    """
    Generate content AND publish it to WordPress in one call.

    Args:
        topic: What to write about
        post_type: 'blog' or 'page'
        status: 'draft' (safe — review before live) or 'publish'
        categories: list of WordPress category IDs
        seo_keywords: list of keywords to weave in (optional)
    Returns: dict with content, WordPress result, and URL
    """
    try:
        from integrations.wordpress import WordPress

        wp = WordPress()

        # --- Step 1: Generate the content ---
        if seo_keywords:
            kw_list = ", ".join(seo_keywords) if isinstance(seo_keywords, list) else seo_keywords
            prompt = (
                f"Write a comprehensive blog post about: {topic}\n\n"
                f"Optimize for these SEO keywords: {kw_list}\n\n"
                "Requirements:\n"
                "- Include the primary keyword in the title\n"
                "- Use keywords naturally (no stuffing)\n"
                "- 800-1200 words\n"
                "- Format in HTML (<h2> for subheadings, <p> for paragraphs, <ul>/<li> for lists)\n"
                "- End with a clear call-to-action\n\n"
                "Write the full blog post now:"
            )
        else:
            prompt = (
                f"Write a comprehensive blog post about: {topic}\n\n"
                "Requirements:\n"
                "- 800-1200 words\n"
                "- Format in HTML (<h2> for subheadings, <p> for paragraphs, <ul>/<li> for lists)\n"
                "- End with a clear call-to-action\n\n"
                "Write the full blog post now:"
            )

        print(f"\n📝 Generating content for: {topic}")
        content = generate_content(prompt, max_length=3000)

        if content.startswith("❌"):
            return {"status": "error", "error": content}

        # Extract title (first markdown h1 or default to topic)
        title = topic
        for line in content.strip().split("\n"):
            stripped = line.strip()
            if stripped.startswith("# "):
                title = stripped[2:].strip()
                break
            if stripped.startswith("<h1>"):
                title = stripped.replace("<h1>", "").replace("</h1>", "").strip()
                break

        # --- Step 2: Publish to WordPress ---
        if not wp.available:
            print("⚠️  WordPress not configured — content generated but not published.")
            return {
                "status": "generated_only",
                "title": title,
                "content": content,
                "wordpress": None,
                "note": "Connect WordPress to enable auto-publishing.",
            }

        print(f"📤 Publishing to WordPress as: {status}...")

        if post_type == "page":
            wp_result = wp.create_page(title=title, content=content, status=status)
        else:
            wp_result = wp.create_post(
                title=title, content=content, status=status, categories=categories
            )

        if wp_result:
            print(f"✅ Published! URL: {wp_result.get('url', 'N/A')}")
            return {
                "status": status,
                "title": title,
                "content": content,
                "wordpress": wp_result,
                "url": wp_result.get("url", ""),
            }

        return {
            "status": "publish_failed",
            "title": title,
            "content": content,
            "wordpress": None,
            "note": "Content generated but WordPress publish failed.",
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


def publish_content(title, content, post_type="blog", status="draft"):
    """
    Publish pre-written content to WordPress.
    Returns: WordPress result dict or None
    """
    try:
        from integrations.wordpress import WordPress

        wp = WordPress()
        if not wp.available:
            print("⚠️  WordPress not configured.")
            return None

        if post_type == "page":
            return wp.create_page(title=title, content=content, status=status)
        return wp.create_post(title=title, content=content, status=status)

    except Exception as e:
        print(f"❌ Publish error: {e}")
        return None


# Test the agent when this file is run directly
if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 CONTENT AGENT - GROQ TEST")
    print("="*60)
    
    # Test request
    test_request = "Write a short blog post introduction about email marketing (3 sentences)"
    
    # Generate content
    content = generate_content(test_request)
    
    # Display result
    print("\n" + "="*60)
    print("📄 GENERATED CONTENT:")
    print("="*60)
    print(content)
    print("="*60)