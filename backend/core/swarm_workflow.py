import time
import logging
import json
import uuid
import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .model_router import call_model
from .prompts import get_prompt
from .events import EventBus
from .memory import get_memory
from .context import get_context
from .supabase_client import get_admin_client
from .signals.registry import CANONICAL_REGISTRY
from .signals.scoring import calculate_priority_score, get_priority_bucket, map_signal_to_registry_key, recalculate_project_health
from .agent_runner import _safe_parse_json

logger = logging.getLogger(__name__)


def map_to_text(val: float) -> str:
    """Map boardroom effort/impact to text limits (low, medium, high)"""
    if val >= 7.0:
        return "high"
    elif val >= 4.0:
        return "medium"
    else:
        return "low"


def sanitize_low_priority_language(text: str) -> str:
    if not text:
        return text
    import re
    replacements = {
        r"\bimmediately\b": "in due course",
        r"\burgent\b": "routine",
        r"\bcritical\b": "hygiene",
        r"\branking drops\b": "indexing clarity updates",
        r"\bcrawl budget loss\b": "crawl efficiency optimizations",
        r"\bblocking\b": "guiding",
        r"\bsevere\b": "minor"
    }
    sanitized = text
    for pattern, repl in replacements.items():
        sanitized = re.sub(pattern, repl, sanitized, flags=re.IGNORECASE)
    return sanitized


def handle_deterministic_follow_up(reg_key: str, message: str) -> Optional[str]:
    msg = message.lower()
    if any(k in msg for k in ["analyze and address", "analyze", "address this signal", "audit", "detector"]):
        return None
    
    # 1. No robots.txt / missing_robots_txt
    if reg_key in ["missing_robots_txt", "no_robots_txt"]:
        if any(k in msg for k in ["create", "generate", "content", "file path", "robots.txt"]):
            return """Here is the exact file path and content for your robots.txt file:

### File Path
Create a file at:
`public/robots.txt`

If your project has a frontend folder, use:
`frontend/public/robots.txt`

### File Content
```text
User-agent: *
Allow: /

Sitemap: https://shravanpayyavula.me/sitemap.xml
```

This file gives search engines and AI crawlers full access to crawl public pages, and specifies the correct location of your sitemap. Add this to your static assets directory and deploy."""
        if any(k in msg for k in ["crawl budget", "monitor crawl budget", "budget allocation"]):
            return "Crawl budget monitoring is not necessary for this small or personal website at this stage. Instead, we recommend adding a standard robots.txt file and referencing your sitemap, which ensures search engines and AI crawlers can discover your pages efficiently without overloading your server."

    # 2. Missing sitemap
    if reg_key == "missing_sitemap":
        if any(k in msg for k in ["create", "generate", "content", "sitemap.xml", "xml sitemap"]):
            return """Here is the XML structure and file path for your sitemap:

### File Path
Create a file at:
`public/sitemap.xml`

If your project has a frontend folder, use:
`frontend/public/sitemap.xml`

### File Content (Example)
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://shravanpayyavula.me/</loc>
    <lastmod>2026-06-11</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

Add your primary public URLs inside the `<urlset>` element, save, and deploy to your static assets directory."""

    # 3. Missing meta description
    if reg_key == "missing_meta_description":
        if any(k in msg for k in ["create", "generate", "content", "meta tag", "description tag"]):
            return """Here is the meta description tag implementation:

### HTML Tag
Add this inside the `<head>` section of your HTML files:
```html
<meta name="description" content="SwarmOps coordinates specialized AI agents to automate your technical marketing audits and growth campaigns.">
```

### Next.js (App Router) Metadata Configuration
If you are using Next.js, add this inside your page or layout `metadata` config:
```typescript
import { Metadata } from 'next';

export const metadata: Metadata = {
  description: 'SwarmOps coordinates specialized AI agents to automate your technical marketing audits and growth campaigns.',
};
```"""

    # 4. Missing Open Graph tags
    if reg_key == "missing_open_graph":
        if any(k in msg for k in ["create", "generate", "content", "og tags", "open graph"]):
            return """Here is the Open Graph metadata tag configuration:

### HTML Tags
Add these inside the `<head>` section of your HTML:
```html
<meta property="og:title" content="SwarmOps | Multi-Agent AI Marketing Command Center">
<meta property="og:description" content="Coordinate specialized AI agents to automate technical marketing audits.">
<meta property="og:image" content="https://shravanpayyavula.me/og-card.png">
<meta property="og:url" content="https://shravanpayyavula.me">
<meta property="og:type" content="website">
```

### Next.js (App Router) Metadata Configuration
```typescript
export const metadata = {
  openGraph: {
    title: 'SwarmOps | Multi-Agent AI Marketing Command Center',
    description: 'Coordinate specialized AI agents to automate technical marketing audits.',
    url: 'https://shravanpayyavula.me',
    siteName: 'SwarmOps',
    images: [
      {
        url: 'https://shravanpayyavula.me/og-card.png',
        width: 1200,
        height: 630,
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
};
```"""

    # 5. Missing canonical
    if reg_key == "missing_canonical":
        if any(k in msg for k in ["create", "generate", "content", "canonical tag", "link tag"]):
            return """Here is the canonical tag implementation:

### HTML Tag
Add this inside the `<head>` section of your HTML:
```html
<link rel="canonical" href="https://shravanpayyavula.me">
```

### Next.js (App Router) Metadata Configuration
```typescript
export const metadata = {
  alternates: {
    canonical: 'https://shravanpayyavula.me',
  },
};
```"""

    # 6. Missing analytics / missing_ga4_or_gtm
    if reg_key in ["missing_ga4_or_gtm", "missing_analytics"]:
        if any(k in msg for k in ["create", "generate", "content", "script", "install", "ga4", "gtm"]):
            return """Here is how to install Google Analytics (GA4) or Google Tag Manager (GTM):

### Option A: Google Tag Manager (GTM)
Paste this script as high as possible in the `<head>` of your page:
```html
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-XXXXXXX');</script>
<!-- End Google Tag Manager -->
```
Paste this noscript code immediately after the opening `<body>` tag:
```html
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXXX"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->
```

Replace `GTM-XXXXXXX` with your actual GTM Container ID."""

    return None


SIGNAL_SPECIFIC_RULES = {
    "missing_robots_txt": {
        "executive_summary": "The site does not currently expose a robots.txt file. This is a low-priority technical SEO hygiene issue, not an emergency. Search engines can still crawl most public websites without it, but adding one gives clearer crawl guidance and helps expose the sitemap location.",
        "final_priority_bucket": "Low",
        "final_impact": 2.0,
        "final_effort": 1.0,
        "final_urgency": 1.0,
        "final_confidence": 8.5,
        "final_decision": "Approve this as a low-effort technical SEO hygiene fix for the next deployment. It is not a ranking emergency, but it improves crawl guidance and sitemap discovery.",
        "action_title": "Create robots.txt file",
        "action_description": "Create a `robots.txt` file in the public/static assets directory and include a sitemap reference.",
        "checklist": [
            "Create `public/robots.txt`.",
            "Add a full crawl access rule.",
            "Add sitemap reference.",
            "Deploy frontend.",
            "Verify `/robots.txt` returns HTTP 200.",
            "Re-scan in SwarmOps.",
            "Mark the signal as resolved."
        ],
        "verification_method": "1. Deploy the change.\n2. Open `https://shravanpayyavula.me/robots.txt`.\n3. Confirm it returns HTTP 200 instead of 404.\n4. Confirm the sitemap URL is correct and accessible.\n5. Re-run the SwarmOps scan.\n6. Optional: submit or refresh the sitemap in Google Search Console.",
        "resolved_when": "The URL /robots.txt returns an HTTP 200 status code with valid robot directive content.",
        "specialists": {
            "seo": {
                "assessment": "Recommended adding a simple robots.txt file with full crawl access and a sitemap reference. This is a low-effort hygiene fix.",
                "recommended_action": "Create `public/robots.txt` with Allow: / and a Sitemap link.",
                "risk_or_caution": "robots.txt controls crawler access, not indexing. Adding one is a standard, risk-free hygiene practice."
            },
            "aeo": {
                "assessment": "Supported the fix because sitemap discovery can help search and AI crawlers understand the site structure more clearly.",
                "recommended_action": "Ensure sitemap reference is present in the robots.txt file.",
                "risk_or_caution": "Verify sitemap URL is fully qualified and public."
            },
            "engineering": {
                "assessment": "Creating a static robots.txt file is a low-effort engineering task (1-2/10 effort). Should be placed in the public assets folder.",
                "recommended_action": "Create `public/robots.txt` or `frontend/public/robots.txt`.",
                "risk_or_caution": "Confirm that build pipeline deploys static files correctly."
            }
        }
    },
    "missing_sitemap": {
        "executive_summary": "No XML sitemap reference was declared in robots.txt or found at standard sitemap locations. This is a standard technical opportunity.",
        "final_priority_bucket": "Medium",
        "final_impact": 3.0,
        "final_effort": 1.0,
        "final_urgency": 2.0,
        "final_confidence": 9.0,
        "final_decision": "Implement the XML sitemap to ensure search engine and AI crawlers discover new pages efficiently.",
        "action_title": "Configure XML Sitemap",
        "action_description": "Generate an XML sitemap listing your active pages and reference it in your robots.txt file.",
        "checklist": [
            "Generate `sitemap.xml` listing active pages.",
            "Deploy sitemap to public directory.",
            "Add Sitemap directive to `robots.txt`.",
            "Verify sitemap parses correctly.",
            "Submit sitemap to Google Search Console."
        ],
        "verification_method": "1. Open `/sitemap.xml` on the domain.\n2. Verify it renders valid XML with page URLs.\n3. Check `/robots.txt` contains a `Sitemap:` line pointing to the sitemap URL.\n4. Verify the sitemap URL is accessible and returns HTTP 200.",
        "resolved_when": "A valid XML sitemap is successfully parsed from the sitemap URL.",
        "specialists": {
            "seo": {
                "assessment": "Recommended generating and referencing a sitemap to guide page discovery.",
                "recommended_action": "Configure XML sitemap and update robots.txt.",
                "risk_or_caution": "Ensure all URLs in the sitemap use HTTPS and the correct canonical forms."
            },
            "aeo": {
                "assessment": "Supported sitemap configuration as it ensures AI indexers crawl entity links systematically.",
                "recommended_action": "Make sitemap indexable for AI scrapers.",
                "risk_or_caution": "Do not include non-canonical pages or admin links."
            },
            "engineering": {
                "assessment": "Configure sitemap generation in the frontend build script (e.g. next-sitemap) and append the link to robots.txt.",
                "recommended_action": "Automate sitemap creation in the deployment pipeline.",
                "risk_or_caution": "Ensure the sitemap updates dynamically when new pages are published."
            }
        }
    },
    "missing_meta_description": {
        "executive_summary": "The HTML header is missing a meta description tag. While not a ranking penalty, adding one improves snippet quality in search results.",
        "final_priority_bucket": "Medium",
        "final_impact": 3.0,
        "final_effort": 1.0,
        "final_urgency": 2.0,
        "final_confidence": 9.0,
        "final_decision": "Approve this meta description update to optimize organic search listing snippet appearance.",
        "action_title": "Add Meta Description",
        "action_description": "Add a descriptive `<meta name=\"description\" content=\"...\">` tag to the page HTML head.",
        "checklist": [
            "Draft meta description (150-160 characters).",
            "Add meta description tag to homepage layout.",
            "Deploy changes.",
            "Verify tag in rendered source."
        ],
        "verification_method": "1. View page source or inspect HTML.\n2. Search for `<meta name=\"description\"` inside the `<head>` section.\n3. Confirm the content attribute is populated with the desired text.",
        "resolved_when": "A populated description meta tag is present in the homepage HTML head.",
        "specialists": {
            "seo": {
                "assessment": "Recommended adding a custom meta description to control search snippet presentation.",
                "recommended_action": "Add description tag under 160 characters.",
                "risk_or_caution": "Avoid keyword stuffing; keep description natural and descriptive."
            },
            "cro": {
                "assessment": "Recommended writing a compelling description to improve click-through appeal from search results.",
                "recommended_action": "Write action-oriented click hooks in the meta tag content.",
                "risk_or_caution": "Ensure descriptions accurately reflect the destination page content."
            },
            "engineering": {
                "assessment": "Update the homepage metadata settings in the application layout or head tags.",
                "recommended_action": "Modify the head meta elements in Next.js metadata configs.",
                "risk_or_caution": "Avoid duplicate meta descriptions across different routes."
            }
        }
    },
    "missing_open_graph": {
        "executive_summary": "The page HTML lacks Open Graph metadata tags (`og:title`, `og:image`). This is a low-priority cosmetic issue affecting social share previews.",
        "final_priority_bucket": "Low",
        "final_impact": 2.0,
        "final_effort": 1.0,
        "final_urgency": 1.0,
        "final_confidence": 9.0,
        "final_decision": "Approve this low-effort cosmetic fix for the next deployment to ensure premium brand presentation when links are shared.",
        "action_title": "Add Open Graph Tags",
        "action_description": "Insert standard Open Graph tags in the HTML head to control titles and images on social shares.",
        "checklist": [
            "Create an og-image asset.",
            "Insert `og:title`, `og:description`, and `og:image` meta tags to layout head.",
            "Deploy frontend.",
            "Verify using a social media debugger."
        ],
        "verification_method": "1. Deploy the changes.\n2. Paste the URL into the Facebook Sharing Debugger or LinkedIn Post Inspector.\n3. Verify the title, description, and image preview display correctly.",
        "resolved_when": "At least og:title and og:image tags are detected in the page header.",
        "specialists": {
            "cro": {
                "assessment": "Recommended adding Open Graph tags to maximize visual appeal on social platforms.",
                "recommended_action": "Add high-converting share titles and cover images.",
                "risk_or_caution": "Social image should have recommended dimensions (1200x630)."
            },
            "content": {
                "assessment": "Recommended defining custom social preview text and images to keep branding consistent.",
                "recommended_action": "Design custom card preview banners.",
                "risk_or_caution": "Avoid generic default images."
            },
            "engineering": {
                "assessment": "Add meta property tags to the layout header or next/metadata configurations.",
                "recommended_action": "Inject og: tags into layout.tsx.",
                "risk_or_caution": "Ensure static assets (images) use absolute URLs."
            }
        }
    },
    "missing_canonical": {
        "executive_summary": "No canonical link tag was detected. Canonical tags consolidate link signals and prevent duplicate content issues.",
        "final_priority_bucket": "Medium",
        "final_impact": 3.0,
        "final_effort": 1.0,
        "final_urgency": 2.0,
        "final_confidence": 9.0,
        "final_decision": "Approve self-referencing canonical tag implementation to protect link signals and crawl consolidation.",
        "action_title": "Add Canonical Link Tag",
        "action_description": "Add a self-referencing `<link rel=\"canonical\" href=\"...\">` tag to the HTML head.",
        "checklist": [
            "Determine preferred primary URL.",
            "Add rel='canonical' link tag to the page template.",
            "Deploy changes.",
            "Verify in page source."
        ],
        "verification_method": "1. Open the page and inspect source.\n2. Search for `<link rel=\"canonical\"`.\n3. Verify the href attribute points to the absolute preferred URL of the page.",
        "resolved_when": "A canonical link tag is present and points to a valid absolute URL matching the page domain.",
        "specialists": {
            "seo": {
                "assessment": "Recommended canonical tags to guide indexing and prevent potential duplicate page versioning.",
                "recommended_action": "Add self-referencing canonical link tag.",
                "risk_or_caution": "Ensure canonical links point to the absolute URL version using HTTPS."
            },
            "engineering": {
                "assessment": "Add a self-referencing canonical URL tag to the layout template or routing middleware.",
                "recommended_action": "Use next/head or dynamic header functions to inject canonical elements.",
                "risk_or_caution": "Do not point canonical tags to redirected URLs."
            }
        }
    },
    "missing_ga4_or_gtm": {
        "executive_summary": "Google Analytics (GA4) or Google Tag Manager (GTM) tags were not detected. This prevents tracking visitor behavior and marketing campaigns.",
        "final_priority_bucket": "Medium",
        "final_impact": 7.0,
        "final_effort": 1.5,
        "final_urgency": 7.0,
        "final_confidence": 9.5,
        "final_decision": "Deploy the tracking script to ensure accurate measurement of traffic and campaign attribution.",
        "action_title": "Install Analytics Tracking",
        "action_description": "Embed the GA4 tracking script or GTM container script inside the site head and body.",
        "checklist": [
            "Retrieve tracking ID or GTM container ID.",
            "Insert GTM container script into the document head and body.",
            "Deploy frontend changes.",
            "Verify live signal reception in GA4 DebugView."
        ],
        "verification_method": "1. Open the website in browser.\n2. Inspect HTML or use Google Tag Assistant.\n3. Confirm that GTM or gtag scripts load without console errors and register tag hits.",
        "resolved_when": "A valid GTM or GA4 tracking tag is successfully parsed from the DOM.",
        "specialists": {
            "analytics": {
                "assessment": "Recommended integrating GTM/GA4 scripts to close tracking gaps and capture visitor insights.",
                "recommended_action": "Deploy analytics integration container.",
                "risk_or_caution": "Verify trigger configurations do not double count sessions."
            },
            "cro": {
                "assessment": "Supported tracking to enable conversion funnel measurement and audience profiling.",
                "recommended_action": "Implement pageview tracking rules.",
                "risk_or_caution": "Ensure compliance with privacy consent requirements (e.g. GDPR)."
            },
            "engineering": {
                "assessment": "Insert the tracking code block inside the root layout head and body scripts.",
                "recommended_action": "Embed script tags or next/third-parties library components.",
                "risk_or_caution": "Load script asynchronously to prevent LCP metric impact."
            }
        }
    },
    "missing_primary_cta": {
        "executive_summary": "No prominent primary Call to Action (CTA) button or link was found in the hero or header section. This can lower conversion rates.",
        "final_priority_bucket": "Medium",
        "final_impact": 6.0,
        "final_effort": 1.5,
        "final_urgency": 5.0,
        "final_confidence": 9.0,
        "final_decision": "Add a prominent primary CTA above the fold to guide user focus and reduce visitor friction.",
        "action_title": "Implement Primary CTA",
        "action_description": "Insert a prominent, high-contrast Call to Action button (e.g., 'Get Started' or 'Contact Us') above the fold.",
        "checklist": [
            "Select the primary conversion goal.",
            "Design a high-contrast CTA button for the hero section.",
            "Verify button positioning is prominent on mobile.",
            "Link CTA button to the registration/contact page."
        ],
        "verification_method": "1. Inspect the page layout above the fold.\n2. Ensure a distinct button with high-contrast styling and clear text is visible within the viewport.",
        "resolved_when": "At least one highly visible CTA button is identified in the page's top section.",
        "specialists": {
            "cro": {
                "assessment": "Recommended adding a high-contrast primary CTA above the fold to capture visitor intent.",
                "recommended_action": "Add responsive hero CTA button.",
                "risk_or_caution": "Friction increases if the CTA link leads to a long multi-step signup."
            },
            "content": {
                "assessment": "Recommended writing action-oriented, clear CTA copy to encourage signups.",
                "recommended_action": "Draft clear copy ('Get Started Free' or 'Book a Demo').",
                "risk_or_caution": "Avoid passive phrasing like 'Submit' or 'Click Here'."
            },
            "engineering": {
                "assessment": "Code a responsive CTA button in the hero component with clear routing links.",
                "recommended_action": "Implement interactive button component with hover styling.",
                "risk_or_caution": "Ensure elements are fully accessible (proper ARIA role and contrast)."
            }
        }
    },
    "missing_json_ld": {
        "executive_summary": "No JSON-LD structured data schema was found. Adding schema helps search engines and AI crawlers parse your entity relationships.",
        "final_priority_bucket": "Low",
        "final_impact": 4.0,
        "final_effort": 2.0,
        "final_urgency": 3.0,
        "final_confidence": 9.0,
        "final_decision": "Approve schema markup addition to improve semantic entity visibility for search and AI answer engines.",
        "action_title": "Implement JSON-LD Schema",
        "action_description": "Configure and embed a JSON-LD schema script (e.g., WebSite or Organization) representing your page entity.",
        "checklist": [
            "Identify correct schema type (WebSite/Organization).",
            "Generate valid JSON-LD schema script.",
            "Embed schema in page HTML head.",
            "Validate using Google Schema Validator."
        ],
        "verification_method": "1. Open Schema Markup Validator.\n2. Enter the webpage URL.\n3. Confirm that the schema type is detected with zero warnings or errors.",
        "resolved_when": "A valid JSON-LD schema script is detected in the page source and parses without errors.",
        "specialists": {
            "seo": {
                "assessment": "Recommended adding schema markup to feed structured details to search crawlers.",
                "recommended_action": "Embed WebSite/Organization structured JSON script.",
                "risk_or_caution": "Do not violate schema.org guidelines (e.g. marking up invisible details)."
            },
            "aeo": {
                "assessment": "Supported structured data because semantic schemas help AI answer engines map entities accurately.",
                "recommended_action": "Add entity connection references (sameAs attributes).",
                "risk_or_caution": "Ensure corporate metadata matches across social profiles."
            },
            "engineering": {
                "assessment": "Implement dynamic JSON-LD injection in the page head metadata parser.",
                "recommended_action": "Construct a dynamic script tag with type application/ld+json.",
                "risk_or_caution": "Ensure proper JSON escape characters to avoid rendering runtime errors."
            }
        }
    },
    "missing_h1": {
        "executive_summary": "No H1 heading tag was found. The H1 is the primary semantic header defining the page topic for visitors and search engine crawlers.",
        "final_priority_bucket": "Medium",
        "final_impact": 3.0,
        "final_effort": 1.0,
        "final_urgency": 2.0,
        "final_confidence": 9.5,
        "final_decision": "Implement a single H1 tag to establish proper semantic heading hierarchy and improve page structure.",
        "action_title": "Add H1 Heading Tag",
        "action_description": "Create a single <h1> heading tag at the top of the main page content.",
        "checklist": [
            "Draft a descriptive title for the primary heading.",
            "Wrap the main page title in an `<h1>` tag.",
            "Remove any extra `<h1>` tags to maintain a single H1 hierarchy.",
            "Deploy and inspect source."
        ],
        "verification_method": "1. Inspect page HTML.\n2. Confirm there is exactly one `<h1>` tag present in the document.\n3. Verify it contains descriptive text and is not empty.",
        "resolved_when": "Exactly one non-empty H1 tag is detected on the page.",
        "specialists": {
            "seo": {
                "assessment": "Recommended placing a single H1 tag to clearly define page focus for indexing bots.",
                "recommended_action": "Embed descriptive keywords in a main H1 element.",
                "risk_or_caution": "Do not hide the H1 tag using styling overrides; it must remain visible."
            },
            "content": {
                "assessment": "Recommended writing a descriptive, user-friendly headline for the H1 tag.",
                "recommended_action": "Write visitor-focused main header.",
                "risk_or_caution": "Avoid excessively long headlines (keep under 70 characters)."
            },
            "engineering": {
                "assessment": "Replace styled div text with a semantic `<h1>` element in the page layout.",
                "recommended_action": "Update HTML markup tag from div/h2 to h1.",
                "risk_or_caution": "Adjust CSS styles to match preceding layout aesthetics."
            }
        }
    },
    "slow_page_speed": {
        "executive_summary": "Page response time is slower than recommended benchmarks. Heavy scripts, unoptimized assets, or server delay could be contributing factors.",
        "final_priority_bucket": "Low",
        "final_impact": 5.0,
        "final_effort": 3.0,
        "final_urgency": 4.0,
        "final_confidence": 9.0,
        "final_decision": "Deploy frontend asset and script optimizations to ensure fast response times and improved user retention.",
        "action_title": "Optimize Page Speed",
        "action_description": "Optimize frontend performance by deferring non-critical scripts, compressing images, and setting appropriate cache controls.",
        "checklist": [
            "Audit slow-loading scripts and styles.",
            "Compress and convert homepage images to modern formats (WebP/AVIF).",
            "Enable gzip/brotli compression on the hosting server.",
            "Leverage browser caching for static assets."
        ],
        "verification_method": "1. Run Lighthouse or PageSpeed Insights on the homepage URL.\n2. Confirm the Performance score improves and page load time falls under 2.5 seconds.",
        "resolved_when": "Homepage response time falls under the 2.5-second benchmark on subsequent scans.",
        "specialists": {
            "seo": {
                "assessment": "Recommended optimization to align page response speed with Core Web Vitals guidelines.",
                "recommended_action": "Address script latency blocking Core Web Vitals.",
                "risk_or_caution": "Slight shifts in layout (CLS) should be avoided during speed changes."
            },
            "cro": {
                "assessment": "Recommended optimizing speed because fast loading reduces immediate page bounce rates.",
                "recommended_action": "Accelerate critical rendering path.",
                "risk_or_caution": "Slow loading increases abandonment rates significantly."
            },
            "engineering": {
                "assessment": "Optimize build bundles, enable lazy loading of images, and check server response latency.",
                "recommended_action": "Enable dynamic imports and asset CDNs.",
                "risk_or_caution": "Benchmark server response time (TTFB) to ensure host is not overloaded."
            }
        }
    }
}


def run_swarm_signal_workflow(
    clicked_signal: dict,
    message: str,
    conversation_id: str,
    bus: Optional[EventBus] = None,
    trace_id: Optional[str] = None
) -> dict:
    """
    Supervisor wrapper that generates trace_id, logs start/end/failure trace details.
    """
    import time
    import uuid
    from core.observability import log_structured_event, create_run_trace_db, update_run_trace_db

    start_time = time.time()

    if not trace_id:
        trace_id = clicked_signal.get("raw_data", {}).get("trace_id") or str(uuid.uuid4())

    signal_id = clicked_signal.get("signal_id")
    project_id = clicked_signal.get("project_id")
    user_id = clicked_signal.get("user_id")

    if not user_id or not project_id:
        try:
            ctx = get_context(conversation_id)
            if not project_id:
                project_id = ctx.project_id
            if not user_id:
                user_id = getattr(ctx, "user_id", None)
        except Exception:
            pass

    # Log boardroom.started
    log_structured_event(
        event_name="boardroom.started",
        trace_id=trace_id,
        user_id=user_id,
        project_id=project_id,
        signal_id=signal_id,
        status="running",
        metadata={"signal_type": clicked_signal.get("signal_type")}
    )

    create_run_trace_db(
        trace_id=trace_id,
        user_id=user_id,
        project_id=project_id,
        run_type="signal_analysis",
        model_name="openai/gpt-oss-120b:free",
        provider="openrouter",
        metadata={"signal_type": clicked_signal.get("signal_type"), "conversation_id": conversation_id}
    )

    try:
        # Execute the real workflow
        res = _run_swarm_signal_workflow_impl(
            clicked_signal=clicked_signal,
            message=message,
            conversation_id=conversation_id,
            bus=bus,
            trace_id=trace_id
        )

        total_latency = int((time.time() - start_time) * 1000)
        
        # Build replay snapshot
        from core.observability import BOARDROOM_PROMPT_VERSION, WORKFLOW_VERSION
        replay_snapshot = {
            "trace_id": trace_id,
            "prompt_version": BOARDROOM_PROMPT_VERSION,
            "model_name": "openai/gpt-oss-120b:free",
            "workflow_version": WORKFLOW_VERSION,
            "project_id": project_id,
            "website_url": clicked_signal.get("url"),
            "clicked_signal_payload": {
                "signal_id": clicked_signal.get("signal_id"),
                "signal_type": clicked_signal.get("signal_type"),
                "title": clicked_signal.get("title"),
                "category": clicked_signal.get("category"),
                "evidence": clicked_signal.get("evidence"),
            },
            "final_structured_output": res.get("structured", {}),
            "scoring_inputs": {
                "impact": res.get("structured", {}).get("final_impact"),
                "effort": res.get("structured", {}).get("final_effort"),
                "urgency": res.get("structured", {}).get("final_urgency"),
                "confidence": res.get("structured", {}).get("final_confidence"),
            }
        }
        # Check if deterministic rule was used
        reg_key = clicked_signal.get("signal_type") or map_signal_to_registry_key(clicked_signal.get("title", ""), clicked_signal.get("category", ""))
        rule_key = reg_key
        if reg_key in ["no_robots_txt", "missing_robots_txt"]:
            rule_key = "missing_robots_txt"
        from core.observability import get_feature_flag
        enable_deterministic = get_feature_flag("ENABLE_DETERMINISTIC_SIGNAL_RULES", True)
        if enable_deterministic and rule_key in SIGNAL_SPECIFIC_RULES:
            replay_snapshot["deterministic_rule_key"] = rule_key

        # Complete trace
        update_run_trace_db(
            trace_id=trace_id,
            status="completed",
            latency_ms=total_latency,
            metadata={"replay_snapshot": replay_snapshot}
        )

        # Log structured events
        log_structured_event(
            event_name="decision.reached",
            trace_id=trace_id,
            user_id=user_id,
            project_id=project_id,
            signal_id=signal_id,
            status="success",
            latency_ms=total_latency
        )
        log_structured_event(
            event_name="final.answer",
            trace_id=trace_id,
            user_id=user_id,
            project_id=project_id,
            signal_id=signal_id,
            status="success"
        )
        return res

    except Exception as e:
        total_latency = int((time.time() - start_time) * 1000)
        logger.exception(f"Error in boardroom swarm workflow: {e}")

        # Emit stream.failed on the bus
        if bus:
            bus.emit("stream.failed", {
                "error": str(e),
                "trace_id": trace_id
            })
            bus.emit("stream.end", {})

        # Update run trace to failed
        update_run_trace_db(
            trace_id=trace_id,
            status="failed",
            latency_ms=total_latency,
            error_type=type(e).__name__,
            error_message=str(e)
        )

        # Log structured event
        log_structured_event(
            event_name="stream.failed",
            trace_id=trace_id,
            user_id=user_id,
            project_id=project_id,
            signal_id=signal_id,
            status="failed",
            latency_ms=total_latency,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise e


def _run_swarm_signal_workflow_impl(
    clicked_signal: dict,
    message: str,
    conversation_id: str,
    bus: Optional[EventBus] = None,
    trace_id: Optional[str] = None
) -> dict:
    ctx = get_context(conversation_id)
    memory = get_memory(conversation_id)
    memory.store(message, role="user", mem_type="conversation")

    start_time = time.time()

    signal_id = clicked_signal.get("signal_id")
    title = clicked_signal.get("title", "")
    description = clicked_signal.get("description", "")
    category = clicked_signal.get("category", "")
    detector = clicked_signal.get("detector", "seo")
    severity = clicked_signal.get("severity", "medium")
    url = clicked_signal.get("url", "")
    evidence = clicked_signal.get("evidence", [])
    project_id = clicked_signal.get("project_id") or ctx.project_id
    user_id = getattr(ctx, "user_id", None)

    # ============================================
    # STEP 1: context_builder
    # ============================================
    if bus:
        bus.emit("workflow.started", {"workflow": "signal_analysis", "agents": []})
        bus.emit("phase.started", {"phase": "context_builder"})

    signal_id = clicked_signal.get("signal_id")
    title = clicked_signal.get("title", "")
    description = clicked_signal.get("description", "")
    category = clicked_signal.get("category", "")
    detector = clicked_signal.get("detector", "seo")
    severity = clicked_signal.get("severity", "medium")
    url = clicked_signal.get("url", "")
    evidence = clicked_signal.get("evidence", [])
    project_id = clicked_signal.get("project_id") or ctx.project_id
    user_id = getattr(ctx, "user_id", None)

    # Lookup registry key
    reg_key = clicked_signal.get("signal_type") or map_signal_to_registry_key(title, category)
    registry_entry = CANONICAL_REGISTRY.get(reg_key) if reg_key else None

    # Map key to rule key
    rule_key = reg_key
    if reg_key == "missing_ga4_or_gtm":
        rule_key = "missing_ga4_or_gtm"
    if reg_key in ["no_robots_txt", "missing_robots_txt"]:
        rule_key = "missing_robots_txt"
    if reg_key == "missing_analytics":
        rule_key = "missing_ga4_or_gtm"
    if reg_key == "weak_cta":
        rule_key = "missing_primary_cta"
    if reg_key == "missing_schema":
        rule_key = "missing_json_ld"

    # Check for follow-up query
    follow_up_answer = handle_deterministic_follow_up(rule_key or "", message)
    if follow_up_answer:
        # If streaming, output decision and close out bus
        if bus:
            bus.emit("decision.reached", {
                "rationale": "Follow-up request handled deterministically.",
                "confidence": 1.0,
                "agents_consulted": ["engineering"],
                "agents_agreed": ["engineering"],
                "agents_dissented": [],
                "debate_happened": False,
                "latency_ms": 1,
                "workflow": "signal_analysis",
                "next_action": {
                    "action": "Implement the provided code/file.",
                    "rationale": "Direct code snippet provided.",
                    "expected_impact": "low",
                    "effort": "low",
                    "timeframe": "now"
                }
            })
            bus.emit("final.answer", {
                "workflow": "signal_analysis",
                "decision_id": str(uuid.uuid4())[:8],
                "message_id": str(uuid.uuid4())[:8],
                "answer": follow_up_answer,
                "answer_len": len(follow_up_answer)
            })
            bus.emit("stream.end", {})
        
        memory.store(follow_up_answer[:1000], role="assistant", mem_type="conversation", importance=0.8)
        return {
            "workflow": "signal_analysis",
            "response": follow_up_answer,
            "agents_used": ["engineering"],
            "latency_ms": 1,
            "confidence": 1.0,
            "structured": {
                "decision": {"executive_summary": "Direct codebase snippet provided.", "final_priority_bucket": "Low"},
                "specialists": [],
                "nexus": {}
            }
        }

    # Construct compiled context details
    signal_context = {
        "signal_id": signal_id,
        "title": title,
        "description": description,
        "category": category,
        "detector": detector,
        "severity": severity,
        "url": url,
        "evidence": str(evidence),
        "project_id": project_id,
        "workspace_id": project_id,
        "what_issue_means": registry_entry.what_issue_means if registry_entry else "Standard technical opportunity detected.",
        "why_it_matters": registry_entry.why_it_matters if registry_entry else "Resolving this improves crawler access and site quality.",
        "business_impact": registry_entry.business_impact if registry_entry else "Aesthetic or structure improvements.",
        "seo_aeo_impact": registry_entry.seo_aeo_impact if registry_entry else "Crawler readability improvements.",
        "default_impact_score": registry_entry.default_impact_score if registry_entry else 5.0,
        "default_effort_score": registry_entry.default_effort_score if registry_entry else 3.0,
        "default_urgency_score": registry_entry.default_urgency_score if registry_entry else 5.0,
        "default_confidence_score": registry_entry.default_confidence_score if registry_entry else 9.0,
        "business_relevance_score": registry_entry.business_relevance_score if registry_entry else 5.0,
        "exact_fix": registry_entry.exact_fix if registry_entry else "Implement configuration fix.",
        "implementation_example": registry_entry.implementation_example if registry_entry else "",
        "verification_method": registry_entry.verification_method if registry_entry else "Re-scan the website.",
        "resolved_when": registry_entry.resolved_when if registry_entry else "No longer flagged by scanner.",
        "evidence_safe_wording": registry_entry.evidence_safe_wording if registry_entry else "Address site configuration.",
        "avoid_claims": registry_entry.avoid_claims if registry_entry else [],
    }

    if bus:
        bus.emit("phase.completed", {"phase": "context_builder"})

    # ============================================
    # STEP 2: specialist_router
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "specialist_router"})

    # Determine specialists based on signal category/title
    specialist_ids = []
    cat_lower = category.lower() if category else ""
    title_lower = title.lower()

    if cat_lower == "seo" or any(k in title_lower for k in ["robots.txt", "sitemap", "canonical", "title", "meta description", "heading", "h1"]):
        specialist_ids = ["seo", "aeo", "engineering"]
    elif cat_lower == "aeo" or any(k in title_lower for k in ["json-ld", "schema", "person", "organization"]):
        specialist_ids = ["aeo", "seo", "engineering"]
    elif cat_lower == "analytics" or any(k in title_lower for k in ["analytics", "ga4", "gtm"]):
        specialist_ids = ["analytics", "cro", "engineering"]
    elif cat_lower == "cro" or any(k in title_lower for k in ["cta", "lead capture", "form", "trust"]):
        specialist_ids = ["cro", "analytics", "engineering"]
    else:
        specialist_ids = ["seo", "cro", "engineering"]

    # Deduplicate and limit
    specialist_ids = list(dict.fromkeys(specialist_ids))

    if bus:
        bus.emit("phase.completed", {"phase": "specialist_router", "selected_agents": specialist_ids})

    # ============================================
    # STEP 3: specialist_review_nodes
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "specialist_review", "agents": specialist_ids})

    specialist_reviews = []
    is_deterministic = rule_key in SIGNAL_SPECIFIC_RULES

    if is_deterministic:
        rule = SIGNAL_SPECIFIC_RULES[rule_key]
        for agent_id in specialist_ids:
            spec_data = rule["specialists"].get(agent_id)
            if not spec_data:
                spec_data = {
                    "assessment": f"Recommended addressing the '{title}' issue.",
                    "recommended_action": signal_context.get("exact_fix", "Implement remediation."),
                    "risk_or_caution": "No major caution."
                }
            review_json = {
                "agent": agent_id,
                "assessment": spec_data["assessment"],
                "impact_view": signal_context["why_it_matters"],
                "evidence_used": [title],
                "recommended_action": spec_data["recommended_action"],
                "risk_or_caution": spec_data["risk_or_caution"],
                "confidence": 0.95
            }
            specialist_reviews.append(review_json)
            if bus:
                bus.emit("agent.started", {"agent_id": agent_id}, agent_id=agent_id)
                bus.emit("agent.responded", {
                    "agent_id": agent_id,
                    "conclusion": spec_data["assessment"][:200],
                    "confidence": 0.95
                }, agent_id=agent_id)
    else:
        def run_one_specialist(agent_id: str) -> dict:
            if bus:
                bus.emit("agent.started", {"agent_id": agent_id}, agent_id=agent_id)
            
            system_prompt = get_prompt(agent_id)
            
            # Specialist unique angles
            angle_instructions = ""
            if agent_id == "seo":
                angle_instructions = "Focus strictly on crawling, indexing, sitemaps, robots.txt rules, and search engine visibility. DO NOT repeat engineering steps or conversion/analytics concerns."
            elif agent_id == "aeo":
                angle_instructions = "Focus strictly on AI answer engines, LLM crawlers (e.g. GPTBot, ClaudeBot), semantic schemas (JSON-LD), and entity matching. DO NOT repeat general search crawling concerns."
            elif agent_id == "cro":
                angle_instructions = "Focus strictly on landing page conversion rate optimization, motivation vs friction, CTA contrast/placement, and buyer social proof. DO NOT repeat search index details."
            elif agent_id == "analytics":
                angle_instructions = "Focus strictly on tracking accuracy, data instrumentation, event triggers, GA4/GTM setup, and conversion measurement systems."
            elif agent_id == "engineering":
                angle_instructions = "Focus strictly on codebase implementation details, precise file paths (e.g., public/static folders), code syntax, and deployment/verification commands."

            instructions = f"""
You are the {agent_id.upper()} Specialist reviewing a specific website signal in the boardroom.
Your final output MUST be a JSON object ONLY matching this schema:
{{
  "agent": "{agent_id}",
  "assessment": "Detailed assessment of this signal",
  "impact_view": "Your perspective on the SEO, AEO, tracking, or conversion impact of this signal",
  "evidence_used": ["List of evidence metrics/strings evaluated"],
  "recommended_action": "Specific remediation fix",
  "risk_or_caution": "Detailed considerations or warnings",
  "confidence": 1.0
}}

YOUR SPECIFIC DOMAIN ANGLE:
{angle_instructions}

STRICT WORDING CONSTRAINTS:
1. Do NOT show or mention upstream rate limits, fallback providers, offline modes, or system failures.
2. robots.txt controls crawler access, not indexing.
3. A clear meta description may improve snippet quality and click appeal when search engines choose to display it (never claim CTR improves by 30%).
4. Structured data gives search engines explicit clues about the meaning of a page and can support machine understanding (never claim schema is critical for citations).

SIGNAL DETAILS:
- Title: {signal_context['title']}
- Description: {signal_context['description']}
- URL: {signal_context['url']}
- Evidence: {signal_context['evidence']}

Respond ONLY with the JSON object. Do not include markdown code fences or other prose.
"""
            # Call model
            raw = call_model(
                prompt=instructions,
                agent_id=agent_id,
                system=system_prompt + "\n\nALWAYS return JSON only. No markdown fences.",
                temperature=0.3,
                json_mode=True
            )

            parsed = _safe_parse_json(raw)
            
            # If parse failed, try once to repair
            if not parsed:
                repair_prompt = f"""
The following text could not be parsed as valid JSON. Please rewrite it so that it is valid JSON matching this schema:
{{
  "agent": "{agent_id}",
  "assessment": "Assessment string",
  "impact_view": "Impact view string",
  "evidence_used": ["evidence list"],
  "recommended_action": "Recommended action string",
  "risk_or_caution": "Risk string",
  "confidence": 0.9
}}

TEXT TO REPAIR:
{raw}
"""
                raw_repaired = call_model(
                    prompt=repair_prompt,
                    agent_id=agent_id,
                    system="Return ONLY valid JSON.",
                    temperature=0.1,
                    json_mode=True
                )
                parsed = _safe_parse_json(raw_repaired)

            if not parsed:
                # Fallback to registry default
                parsed = {
                    "agent": agent_id,
                    "assessment": f"Evaluated the {signal_context['title']} alert.",
                    "impact_view": signal_context["why_it_matters"],
                    "evidence_used": [signal_context["title"]],
                    "recommended_action": signal_context["exact_fix"],
                    "risk_or_caution": signal_context["evidence_safe_wording"],
                    "confidence": 0.8
                }

            if bus:
                bus.emit("agent.responded", {
                    "agent_id": agent_id,
                    "conclusion": parsed.get("assessment", "")[:200],
                    "confidence": parsed.get("confidence", 0.9)
                }, agent_id=agent_id)

            return parsed

        # Execute in parallel
        with ThreadPoolExecutor(max_workers=len(specialist_ids)) as executor:
            futures = {executor.submit(run_one_specialist, a): a for a in specialist_ids}
            for future in as_completed(futures):
                try:
                    specialist_reviews.append(future.result())
                except Exception as e:
                    logger.error(f"Specialist node failed: {e}")

    if bus:
        bus.emit("phase.completed", {"phase": "specialist_review"})

    # ============================================
    # STEP 4: boardroom_decision
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "boardroom_decision", "agent_id": "nexus"})
        bus.emit("agent.started", {"agent_id": "nexus", "role": "synthesizer"}, agent_id="nexus")

    if is_deterministic:
        rule = SIGNAL_SPECIFIC_RULES[rule_key]
        boardroom_json = {
            "executive_summary": rule["executive_summary"],
            "final_priority_bucket": rule["final_priority_bucket"],
            "final_impact": rule["final_impact"],
            "final_effort": rule["final_effort"],
            "final_urgency": rule["final_urgency"],
            "final_confidence": rule["final_confidence"],
            "final_decision": rule["final_decision"],
            "action_title": rule["action_title"],
            "action_description": rule["action_description"],
            "checklist": rule["checklist"],
            "verification_method": rule["verification_method"],
            "resolved_when": rule["resolved_when"],
            "implementation_example": signal_context.get("implementation_example", "")
        }
        if bus:
            bus.emit("agent.responded", {
                "agent_id": "nexus",
                "conclusion": boardroom_json["executive_summary"][:200],
                "confidence": boardroom_json["final_confidence"] / 10.0
            }, agent_id="nexus")
    else:
        specialist_reviews_str = json.dumps(specialist_reviews, indent=2)

        boardroom_prompt = f"""
You are Nexus, the Chief Boardroom Decision Agent. Synthesize the boardroom specialist reviews and reach a final consensus on the clicked signal.

STRICT WORDING CONSTRAINTS:
1. Do NOT mention upstream rate limits, fallback providers, offline modes, or system failures.
2. robots.txt controls crawler access, not indexing.
3. A clear meta description may improve snippet quality and click appeal when search engines choose to display it (never claim CTR improves by 30%).
4. Structured data gives search engines explicit clues about the meaning of a page and can support machine understanding (never claim schema is critical for citations).
5. DO NOT recommend crawl delay (Crawl-delay) for robots.txt by default unless there is explicit evidence of crawler overload or a very large website (10,000+ pages).
6. Bind the final metrics (final_impact, final_effort, final_urgency, final_confidence) to the registry defaults provided below unless there is strong, explicit counter-evidence.

SIGNAL CONTEXT:
- Title: {signal_context['title']}
- Description: {signal_context['description']}
- URL: {signal_context['url']}
- Default Impact: {signal_context['default_impact_score']}
- Default Effort: {signal_context['default_effort_score']}
- Default Urgency: {signal_context['default_urgency_score']}
- Default Confidence: {signal_context['default_confidence_score']}
- Business Relevance: {signal_context['business_relevance_score']}

SPECIALIST REVIEWS:
{specialist_reviews_str}

Your output MUST be a JSON object matching this schema:
{{
  "executive_summary": "Provide a 1-2 sentence top-line synthesis of the findings.",
  "final_priority_bucket": "Specify the priority bucket: Critical | High | Medium | Low.",
  "final_impact": "Provide a float value between 1.0 and 10.0.",
  "final_effort": "Provide a float value between 1.0 and 10.0.",
  "final_urgency": "Provide a float value between 1.0 and 10.0.",
  "final_confidence": "Provide a float value between 1.0 and 10.0.",
  "final_decision": "A precise final decision detailing the specific consensus.",
  "action_title": "A descriptive title for the action plan.",
  "action_description": "A clear description of the specific remediation steps.",
  "checklist": ["List of specific, concrete steps to implement the fix and verify it"],
  "verification_method": "Specific, concrete steps to verify the fix works.",
  "resolved_when": "The specific state required to resolve this alert."
}}

Respond ONLY with the JSON object. Do not include markdown code fences or other prose.
"""
        raw_boardroom = call_model(
            prompt=boardroom_prompt,
            agent_id="nexus",
            system=get_prompt("nexus") + "\n\nALWAYS return JSON only.",
            temperature=0.3,
            json_mode=True
        )

        boardroom_json = _safe_parse_json(raw_boardroom)

        # Repair once
        if not boardroom_json:
            repair_boardroom_prompt = f"The previous output was not valid JSON. Fix it and return valid JSON matching the schema:\n\n{raw_boardroom}"
            raw_repaired_br = call_model(
                prompt=repair_boardroom_prompt,
                agent_id="nexus",
                system="Return ONLY valid JSON.",
                temperature=0.1,
                json_mode=True
            )
            boardroom_json = _safe_parse_json(raw_repaired_br)

        if not boardroom_json:
            # Fallback boardroom JSON
            boardroom_json = {
                "executive_summary": f"Consensus reached to resolve the '{signal_context['title']}' alert.",
                "final_priority_bucket": get_priority_bucket(
                    calculate_priority_score(
                        signal_context["default_impact_score"],
                        signal_context["default_urgency_score"],
                        signal_context["default_confidence_score"],
                        signal_context["business_relevance_score"],
                        signal_context["default_effort_score"]
                    )
                ),
                "final_impact": signal_context["default_impact_score"],
                "final_effort": signal_context["default_effort_score"],
                "final_urgency": signal_context["default_urgency_score"],
                "final_confidence": signal_context["default_confidence_score"],
                "final_decision": f"Address the '{signal_context['title']}' issue immediately following standard procedures.",
                "action_title": f"Resolve: {signal_context['title']}",
                "action_description": signal_context["description"],
                "checklist": [signal_context["exact_fix"], f"Verify: {signal_context['verification_method']}"],
                "verification_method": signal_context["verification_method"],
                "resolved_when": signal_context["resolved_when"]
            }

        if bus:
            bus.emit("agent.responded", {
                "agent_id": "nexus",
                "conclusion": boardroom_json.get("executive_summary", "")[:200],
                "confidence": boardroom_json.get("final_confidence", 9.0) / 10.0
            }, agent_id="nexus")

    if bus:
        bus.emit("phase.completed", {"phase": "boardroom_decision"})

    # Calculate final priority score
    priority_score = calculate_priority_score(
        boardroom_json.get("final_impact", 5.0),
        boardroom_json.get("final_urgency", 5.0),
        boardroom_json.get("final_confidence", 9.0),
        signal_context["business_relevance_score"],
        boardroom_json.get("final_effort", 3.0)
    )
    priority_bucket = get_priority_bucket(priority_score)
    boardroom_json["priority_score"] = priority_score
    boardroom_json["final_priority_bucket"] = priority_bucket

    if bus:
        bus.emit("phase.completed", {"phase": "boardroom_decision"})

    # ============================================
    # STEP 5: action_plan_generation (Delegated to user approval)
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "action_plan_generation"})

    action_plan_id = None
    logger.info("[ACTION PLAN] Bypassing automatic action plan generation. Delegating to user approval flow.")

    if bus:
        bus.emit("phase.completed", {"phase": "action_plan_generation", "action_plan_id": None})

    # ============================================
    # STEP 6: save_agent_run
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "save_agent_run"})

    admin = get_admin_client()
    if admin and project_id and user_id:
        try:
            admin.table("agent_runs").insert({
                "user_id": user_id,
                "project_id": project_id,
                "signal_id": signal_id,
                "agent_id": "nexus",
                "workflow_name": "signal_analysis",
                "inputs": clicked_signal,
                "outputs": boardroom_json,
                "status": "completed",
                "latency_ms": int((time.time() - start_time) * 1000)
            }).execute()
        except Exception as run_err:
            logger.warning(f"Could not save agent run to Supabase: {run_err}")

    if bus:
        bus.emit("phase.completed", {"phase": "save_agent_run"})

    # ============================================
    # STEP 7: Format Response Markdown
    # ============================================
    # Prepare specialist reviews text
    reviews_md = ""
    for r in specialist_reviews:
        agent_name = "SEO Specialist" if r.get("agent") == "seo" else \
                     "AEO/GEO Specialist" if r.get("agent") == "aeo" else \
                     "Growth Strategist" if r.get("agent") == "cro" else \
                     "Analytics Specialist" if r.get("agent") == "analytics" else \
                     "Content Specialist" if r.get("agent") == "content" else \
                     "Engineering Lead" if r.get("agent") == "engineering" else \
                     r.get("agent", "").upper()
        reviews_md += f"\n- **{agent_name}**: {r.get('assessment', '')} "
        if r.get("recommended_action"):
            reviews_md += f"Recommendation: *{r.get('recommended_action')}* "
        if r.get("risk_or_caution"):
            reviews_md += f"(Note: {r.get('risk_or_caution')})"

    # Handle robots.txt default implementation block requirement
    impl_example = boardroom_json.get("implementation_example", signal_context.get("implementation_example", ""))
    if "robots.txt" in title.lower() or "robots.txt" in description.lower():
        impl_example = """```
User-agent: *
Allow: /

Sitemap: https://shravanpayyavula.me/sitemap.xml
```"""
    elif impl_example and not impl_example.startswith("```"):
        impl_example = f"```\n{impl_example}\n```"

    checklist_md = "\n".join(f"- [ ] {item}" for item in boardroom_json.get("checklist", []))

    final_markdown = f"""# SwarmOps Boardroom Analysis: {title}

### Signal Summary
{boardroom_json.get("executive_summary", "")}

### Evidence Found
- **URL**: {url or "Homepage"}
- **Detector**: {detector}
- **Telemetry Indicators**: {evidence or "Missing tag detected in page DOM."}

### What This Means
{signal_context['what_issue_means']}

### Why It Matters
{signal_context['why_it_matters']}

### Priority
- **Score**: {priority_score} / 10.0
- **Bucket**: **{priority_bucket}**
- **Metrics**: Impact: {boardroom_json.get("final_impact", 5.0)}/10 | Effort: {boardroom_json.get("final_effort", 3.0)}/10 | Urgency: {boardroom_json.get("final_urgency", 5.0)}/10 | Confidence: {boardroom_json.get("final_confidence", 9.0)}/10

### Specialist Review
{reviews_md}

### Recommended Fix
{boardroom_json.get("action_description", signal_context.get("exact_fix"))}

### Implementation Example
{impl_example}

### Verification Steps
{boardroom_json.get("verification_method", signal_context.get("verification_method"))}

### Final Boardroom Decision
{boardroom_json.get("final_decision", "")}

### Action Checklist
{checklist_md}
"""

    # Apply Priority-Language Guard if priority is Low
    if priority_bucket.lower() == "low":
        # Sanitize text fields in JSON
        for field in ["executive_summary", "final_decision", "action_description", "verification_method"]:
            if field in boardroom_json and isinstance(boardroom_json[field], str):
                boardroom_json[field] = sanitize_low_priority_language(boardroom_json[field])
        if "checklist" in boardroom_json and isinstance(boardroom_json["checklist"], list):
            boardroom_json["checklist"] = [sanitize_low_priority_language(item) for item in boardroom_json["checklist"]]
        
        # Sanitize final_markdown itself
        final_markdown = sanitize_low_priority_language(final_markdown)

    total_latency = int((time.time() - start_time) * 1000)

    decision_val = final_markdown
    rationale_val = boardroom_json.get("executive_summary", "")
    logger.info(
        f"[DIAGNOSTIC] Emitting decision.reached: "
        f"event_type=decision.reached, "
        f"workflow=signal_analysis, "
        f"decision_exists={bool(decision_val)}, "
        f"decision_len={len(decision_val) if decision_val else 0}, "
        f"rationale_exists={bool(rationale_val)}, "
        f"rationale_len={len(rationale_val) if rationale_val else 0}, "
        f"payload_keys={['decision', 'rationale', 'confidence', 'agents_consulted', 'agents_agreed', 'agents_dissented', 'debate_happened', 'latency_ms', 'workflow', 'next_action']}"
    )

    # If streaming, output decision and close out bus
    if bus:
        bus.emit("decision.reached", {
            "rationale": boardroom_json.get("executive_summary", ""),
            "confidence": boardroom_json.get("final_confidence", 9.0) / 10.0,
            "agents_consulted": specialist_ids,
            "agents_agreed": specialist_ids,
            "agents_dissented": [],
            "debate_happened": False,
            "latency_ms": total_latency,
            "workflow": "signal_analysis",
            "next_action": {
                "action": boardroom_json.get("action_title", f"Resolve: {title}"),
                "rationale": boardroom_json.get("action_description", description),
                "expected_impact": map_to_text(boardroom_json.get("final_impact", 5.0)),
                "effort": map_to_text(boardroom_json.get("final_effort", 3.0)),
                "timeframe": "this week"
            }
        })
        bus.emit("final.answer", {
            "workflow": "signal_analysis",
            "decision_id": str(uuid.uuid4())[:8],
            "message_id": str(uuid.uuid4())[:8],
            "answer": final_markdown,
            "answer_len": len(final_markdown),
            "boardroom_json": boardroom_json,
            "signal_id": signal_id,
            "project_id": project_id,
            "user_id": user_id
        })
        bus.emit("stream.end", {})

    # Store in memory for conversation context
    memory.store(final_markdown[:1000], role="assistant", mem_type="conversation", importance=0.8)

    return {
        "workflow": "signal_analysis",
        "response": final_markdown,
        "agents_used": ["nexus"] + specialist_ids,
        "latency_ms": total_latency,
        "confidence": boardroom_json.get("final_confidence", 9.0) / 10.0,
        "structured": boardroom_json,
        "signal_id": signal_id,
        "project_id": project_id,
        "user_id": user_id
    }
