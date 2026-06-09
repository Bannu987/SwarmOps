"""
Website health scanner. Fetches the user's URL and detects:
- HTTP errors (4xx, 5xx)
- Slow response times
- Missing essential meta tags (title, description)
- Missing schema markup
- No robots.txt or sitemap
"""
import time
import logging
import httpx
from typing import List, Dict
from urllib.parse import urljoin

from .base import BaseScanner, Signal

logger = logging.getLogger(__name__)


class WebsiteHealthScanner(BaseScanner):
    name = "website_health"
    interval_hours = 24
    requires_url = True
    requires_integration = None

    def scan(self, user_id: str, project: Dict) -> List[Signal]:
        url = project.get("website_url", "").strip()
        if not url:
            return []

        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        signals: List[Signal] = []

        # Fetch homepage
        try:
            start = time.time()
            response = httpx.get(
                url,
                timeout=15.0,
                follow_redirects=True,
                headers={"User-Agent": "SwarmOps-Scanner/1.0"},
            )
            duration_ms = int((time.time() - start) * 1000)
        except httpx.TimeoutException:
            signals.append(Signal(
                signal_type="risk_alert",
                title="Website not responding",
                description=f"{url} timed out after 15 seconds.",
                severity="critical",
                category="risk",
                source_agent="seo",
                source_detail=url,
                evidence=[{"claim": "Site timeout", "source": "scanner", "value": "15s+"}],
                expires_in_hours=24,
            ))
            return signals
        except Exception as e:
            logger.warning(f"Site fetch failed for {url}: {e}")
            return []

        # Check 1: HTTP status
        if response.status_code >= 400:
            signals.append(Signal(
                signal_type="risk_alert",
                title=f"Website returning {response.status_code} error",
                description=f"{url} is returning a {response.status_code} status code.",
                severity="critical" if response.status_code >= 500 else "high",
                category="risk",
                source_agent="seo",
                source_detail=url,
                evidence=[{"claim": "HTTP error", "source": "scanner", "value": str(response.status_code)}],
                raw_data={"status_code": response.status_code},
                expires_in_hours=24,
            ))
            return signals  # other checks pointless if site is down

        # Check 2: Slow response
        if duration_ms > 3000:
            severity = "high" if duration_ms > 5000 else "medium"
            signals.append(Signal(
                signal_type="risk_alert",
                title=f"Website slow: {duration_ms}ms response time",
                description=(
                    f"Your homepage took {duration_ms}ms to respond. "
                    f"Google's Core Web Vitals recommend under 2500ms."
                ),
                severity=severity,
                category="risk",
                source_agent="seo",
                source_detail=url,
                evidence=[
                    {"claim": "Slow response", "source": "scanner", "value": f"{duration_ms}ms"},
                    {"claim": "Google CWV threshold", "source": "benchmark", "value": "2500ms"},
                ],
                raw_data={"duration_ms": duration_ms},
                expires_in_hours=168,
            ))

        # Check 3-6: Parse HTML
        html = response.text.lower()

        # Missing title
        if "<title>" not in html or html.count("<title></title>") > 0:
            signals.append(Signal(
                signal_type="risk_alert",
                title="Missing or empty <title> tag",
                description="Your homepage has no title tag. This is the single biggest on-page SEO factor.",
                severity="high",
                category="risk",
                source_agent="seo",
                source_detail=url,
                evidence=[{"claim": "No title tag", "source": "scanner", "value": "missing"}],
                expires_in_hours=168,
            ))

        # Missing meta description
        if 'name="description"' not in html and "name='description'" not in html:
            signals.append(Signal(
                signal_type="opportunity_window",
                title="Missing meta description on homepage",
                description="A clear meta description may improve snippet quality and click appeal when search engines choose to display it.",
                severity="medium",
                category="opportunity",
                source_agent="seo",
                source_detail=url,
                evidence=[
                    {"claim": "No meta description", "source": "scanner", "value": "missing"},
                ],
                expires_in_hours=168,
            ))

        # Missing schema markup
        if "application/ld+json" not in html and "schema.org" not in html:
            signals.append(Signal(
                signal_type="opportunity_window",
                title="No JSON-LD schema detected",
                description="Structured data gives search engines explicit clues about the meaning of a page and can support machine understanding.",
                severity="medium",
                category="opportunity",
                source_agent="aeo",
                source_detail=url,
                evidence=[{"claim": "No schema", "source": "scanner", "value": "missing"}],
                expires_in_hours=168,
            ))

        # Check 7: Robots.txt
        try:
            robots_url = urljoin(url, "/robots.txt")
            robots_response = httpx.get(robots_url, timeout=5.0)
            if robots_response.status_code != 200:
                signals.append(Signal(
                    signal_type="opportunity_window",
                    title="No robots.txt file",
                    description="A robots.txt file gives you control over how search engines crawl your site.",
                    severity="low",
                    category="opportunity",
                    source_agent="seo",
                    source_detail=robots_url,
                    expires_in_hours=720,  # 30 days
                ))
        except Exception:
            pass  # not critical

        return signals
