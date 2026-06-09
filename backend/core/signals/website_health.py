"""
Website health scanner. Fetches the user's URL and detects:
- HTTP errors (4xx, 5xx)
- Slow response times
- Missing essential meta tags (title, description, canonical)
- Missing schema markup (JSON-LD, Person, Organization)
- Missing open graph tags
- Missing GA4 or GTM
- Missing primary CTA, lead capture, and trust signals
- No robots.txt or sitemap
"""
import time
import logging
import httpx
import socket
import ipaddress
from typing import List, Dict
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

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

        # Crawl Safety Guard
        try:
            parsed_url = urlparse(url)
            if parsed_url.scheme not in ["http", "https"]:
                logger.warning(f"[CRAWL GUARD] Blocked URL scan attempt (invalid scheme): {url}")
                return []
            
            hostname = parsed_url.hostname
            if not hostname:
                logger.warning(f"[CRAWL GUARD] Blocked URL scan attempt (no hostname): {url}")
                return []
                
            # Block localhost and private/internal IP ranges (RFC 1918)
            ip_addr = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_addr)
            if ip_obj.is_private or ip_obj.is_loopback:
                logger.warning(f"[CRAWL GUARD] Blocked URL scan attempt (private/loopback IP {ip_addr}): {url}")
                return []
        except Exception as e:
            logger.warning(f"[CRAWL GUARD] Safety check failed to resolve host for {url}: {e}")
            # Never expose internal DNS errors or crash; return empty signals list safely
            return []

        signals: List[Signal] = []

        # Fetch homepage using client with redirect limits and custom headers
        try:
            start = time.time()
            with httpx.Client(
                follow_redirects=True, 
                max_redirects=3, 
                timeout=10.0, 
                headers={"User-Agent": "SwarmOps-Scanner/1.0"}
            ) as client:
                response = client.get(url)
            duration_ms = int((time.time() - start) * 1000)
        except httpx.TimeoutException:
            signals.append(Signal(
                signal_type="risk_alert",
                title="Website not responding",
                description="Your website homepage timed out after 10 seconds. This affects organic visitor traffic and search accessibility.",
                severity="critical",
                category="risk",
                source_agent="seo",
                source_detail=url,
                evidence=[{"claim": "Site fetch timeout", "source": "crawler", "value": "10s+"}],
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
                description=f"Your website's homepage returned a {response.status_code} status code, meaning visitors and search bots cannot access the content.",
                severity="critical" if response.status_code >= 500 else "high",
                category="risk",
                source_agent="seo",
                source_detail=url,
                evidence=[{"claim": "HTTP error status", "source": "crawler", "value": str(response.status_code)}],
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
                    "Google Core Web Vitals benchmark recommends under 2500ms."
                ),
                severity=severity,
                category="risk",
                source_agent="seo",
                source_detail=url,
                evidence=[
                    {"claim": "Slow response duration", "source": "crawler", "value": f"{duration_ms}ms"},
                    {"claim": "Core Web Vitals recommended threshold", "source": "benchmark", "value": "2500ms"},
                ],
                raw_data={"duration_ms": duration_ms},
                expires_in_hours=168,
            ))

        # Check DOM details via BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        html_lower = response.text.lower()

        # Check 3: Missing Title
        title_tag = soup.find("title")
        if not title_tag or not title_tag.get_text().strip():
            signals.append(Signal(
                signal_type="risk_alert",
                title="Missing or empty <title> tag",
                description="Your homepage lacks a populated <title> tag in the HTML head. A descriptive title tag defines the page subject for search bots and browsers.",
                severity="high",
                category="risk",
                source_agent="seo",
                source_detail=url,
                evidence=[{"claim": "Missing or empty title tag", "source": "html", "value": "missing"}],
                expires_in_hours=168,
            ))

        # Check 4: Missing Meta Description
        desc_meta = soup.find("meta", attrs={"name": "description"})
        if not desc_meta or not desc_meta.get("content", "").strip():
            signals.append(Signal(
                signal_type="opportunity_window",
                title="Missing meta description on key pages",
                description="A clear meta description may improve snippet quality and click appeal when search engines choose to display it.",
                severity="medium",
                category="opportunity",
                source_agent="seo",
                source_detail=url,
                evidence=[{"claim": "No meta description tag", "source": "html", "value": "missing"}],
                expires_in_hours=168,
            ))

        # Check 5: Missing Canonical
        canonical_link = soup.find("link", rel="canonical")
        if not canonical_link or not canonical_link.get("href", "").strip():
            signals.append(Signal(
                signal_type="opportunity_window",
                title="Missing canonical URL tag",
                description="Canonical link tags specify the preferred indexable URL of the page, preventing duplicate content dilution.",
                severity="medium",
                category="opportunity",
                source_agent="seo",
                source_detail=url,
                evidence=[{"claim": "No rel='canonical' link tag", "source": "html", "value": "missing"}],
                expires_in_hours=168,
            ))

        # Check 6: JSON-LD Schema detection
        json_ld_scripts = soup.find_all("script", type="application/ld+json")
        has_json_ld = len(json_ld_scripts) > 0
        
        if not has_json_ld:
            signals.append(Signal(
                signal_type="opportunity_window",
                title="No JSON-LD schema detected",
                description="Structured data gives search engines explicit clues about the meaning of a page and can support machine understanding.",
                severity="medium",
                category="opportunity",
                source_agent="aeo",
                source_detail=url,
                evidence=[{"claim": "No application/ld+json schema scripts", "source": "html", "value": "missing"}],
                expires_in_hours=168,
            ))
        else:
            # Analyze contents for Person and Organization schemas
            has_person = False
            has_org = False
            for script in json_ld_scripts:
                try:
                    script_content = script.get_text().lower()
                    if '"person"' in script_content or '"@type": "person"' in script_content:
                        has_person = True
                    if '"organization"' in script_content or '"@type": "organization"' in script_content or '"brand"' in script_content:
                        has_org = True
                except Exception:
                    pass

            if not has_person:
                signals.append(Signal(
                    signal_type="opportunity_window",
                    title="Missing Person schema markup",
                    description="Person structured schema connects personal brand entities, biographical profiles, and author details to search knowledge bases.",
                    severity="medium",
                    category="opportunity",
                    source_agent="aeo",
                    source_detail=url,
                    evidence=[{"claim": "Person entity type schema", "source": "html", "value": "missing"}],
                    expires_in_hours=168,
                ))
            if not has_org:
                signals.append(Signal(
                    signal_type="opportunity_window",
                    title="Missing Organization schema markup",
                    description="Organization schema defines corporate identity, logo, brand assets, and contact metadata for search engines.",
                    severity="medium",
                    category="opportunity",
                    source_agent="aeo",
                    source_detail=url,
                    evidence=[{"claim": "Organization entity type schema", "source": "html", "value": "missing"}],
                    expires_in_hours=168,
                ))

        # Check 7: Open Graph tags
        og_title = soup.find("meta", property="og:title")
        og_image = soup.find("meta", property="og:image")
        if not og_title or not og_image:
            signals.append(Signal(
                signal_type="opportunity_window",
                title="Missing Open Graph metadata tags",
                description="Open Graph tags structure title, image, and description properties for rich preview rendering on social links.",
                severity="low",
                category="opportunity",
                source_agent="content",
                source_detail=url,
                evidence=[
                    {"claim": "og:title tag", "source": "html", "value": "present" if og_title else "missing"},
                    {"claim": "og:image tag", "source": "html", "value": "present" if og_image else "missing"}
                ],
                expires_in_hours=168,
            ))

        # Check 8: GA4 or GTM
        has_gtm = ("googletagmanager.com" in html_lower) or ("gtm-" in html_lower)
        has_ga4 = ("gtag(" in html_lower) or ("analytics.js" in html_lower) or ("g-" in html_lower)
        if not has_gtm and not has_ga4:
            signals.append(Signal(
                signal_type="opportunity_window",
                title="Missing Google Analytics (GA4) or GTM tag",
                description="Analytics tags collect visitor metrics to measure marketing performance and landing page attribution.",
                severity="high",
                category="opportunity",
                source_agent="analytics",
                source_detail=url,
                evidence=[{"claim": "Google GTM/GA4 tracking code", "source": "html", "value": "missing"}],
                expires_in_hours=168,
            ))

        # Check 9: CTA (Primary Call to Action)
        cta_keywords = ["signup", "sign up", "register", "join", "get started", "free", "demo", "contact", "subscribe", "buy"]
        ctas = []
        for tag in soup.find_all(["a", "button"]):
            text = tag.get_text().strip().lower()
            if any(k in text for k in cta_keywords):
                ctas.append(tag)
        
        if not ctas:
            signals.append(Signal(
                signal_type="opportunity_window",
                title="Missing clear primary Call to Action (CTA)",
                description="Clear primary calls-to-action guide visitors toward conversion next steps, focusing buyer attention above the fold.",
                severity="medium",
                category="opportunity",
                source_agent="cro",
                source_detail=url,
                evidence=[{"claim": "Visible header/hero CTA buttons", "source": "heuristic", "value": "0 found"}],
                expires_in_hours=168,
            ))

        # Check 10: Lead Capture Form
        inputs = soup.find_all("input")
        has_email_input = any(inp.get("type") == "email" or "email" in inp.get("name", "").lower() for inp in inputs)
        has_form = len(soup.find_all("form")) > 0
        if not has_email_input and not has_form:
            signals.append(Signal(
                signal_type="opportunity_window",
                title="No lead capture form detected",
                description="Lead capture forms allow interested visitors to submit contact requests or subscribe to campaign lifecycles.",
                severity="medium",
                category="opportunity",
                source_agent="cro",
                source_detail=url,
                evidence=[{"claim": "Email input fields or form tags", "source": "heuristic", "value": "missing"}],
                expires_in_hours=168,
            ))

        # Check 11: Weak Trust Signals
        trust_keywords = ["review", "reviews", "testimonial", "testimonials", "rating", "trustpilot", "customer logo", "our clients"]
        has_trust = any(k in html_lower for k in trust_keywords)
        if not has_trust:
            signals.append(Signal(
                signal_type="opportunity_window",
                title="Weak trust signals detected",
                description="Testimonials and reviews help establish commercial trust for landing page visitors by reducing friction.",
                severity="medium",
                category="opportunity",
                source_agent="cro",
                source_detail=url,
                evidence=[{"claim": "Testimonials, review text, or rating widgets", "source": "heuristic", "value": "not detected"}],
                expires_in_hours=168,
            ))

        # Check 12: Robots.txt existence & content
        try:
            robots_url = urljoin(url, "/robots.txt")
            with httpx.Client(timeout=5.0) as client:
                robots_response = client.get(robots_url)
            
            if robots_response.status_code != 200:
                signals.append(Signal(
                    signal_type="opportunity_window",
                    title="No robots.txt file",
                    description="A robots.txt file gives you control over how search engines crawl your site, guiding crawler access.",
                    severity="low",
                    category="opportunity",
                    source_agent="seo",
                    source_detail=robots_url,
                    evidence=[{"claim": "robots.txt HTTP status", "source": "crawler", "value": str(robots_response.status_code)}],
                    expires_in_hours=720,  # 30 days
                ))
            else:
                # Check blocks all rule
                robots_txt = robots_response.text.lower()
                clean_lines = [l.strip() for l in robots_txt.split("\n") if l.strip() and not l.strip().startswith("#")]
                
                # Check for "user-agent: *" followed closely by "disallow: /" (wildcard block)
                is_blocking = False
                current_agent_wildcard = False
                for line in clean_lines:
                    if line.startswith("user-agent:"):
                        agent = line.split(":", 1)[1].strip()
                        current_agent_wildcard = (agent == "*")
                    elif line.startswith("disallow:") and current_agent_wildcard:
                        path = line.split(":", 1)[1].strip()
                        if path == "/" or path == "":
                            is_blocking = True
                            
                if is_blocking:
                    signals.append(Signal(
                        signal_type="risk_alert",
                        title="Robots.txt blocks search indexing",
                        description="Your robots.txt file contains a wild disallow directive blocking all search bots. This blocks search crawlers from discovering or indexing content.",
                        severity="critical",
                        category="risk",
                        source_agent="seo",
                        source_detail=robots_url,
                        evidence=[{"claim": "User-agent * Disallow / block", "source": "crawler", "value": "active"}],
                        expires_in_hours=168,
                    ))

                # Check if sitemap is referenced
                if "sitemap:" not in robots_txt:
                    # Let's check sitemap.xml directly before alerting
                    sitemap_url = urljoin(url, "/sitemap.xml")
                    try:
                        with httpx.Client(timeout=5.0) as client:
                            sitemap_res = client.get(sitemap_url)
                        sitemap_exists = (sitemap_res.status_code == 200)
                    except Exception:
                        sitemap_exists = False

                    if not sitemap_exists:
                        signals.append(Signal(
                            signal_type="opportunity_window",
                            title="Missing XML sitemap reference",
                            description="XML sitemaps provide an explicit crawler roadmap for page discovery, assisting bots to index new campaign structures.",
                            severity="medium",
                            category="opportunity",
                            source_agent="seo",
                            source_detail=robots_url,
                            evidence=[
                                {"claim": "Sitemap reference in robots.txt", "source": "crawler", "value": "missing"},
                                {"claim": "/sitemap.xml presence", "source": "crawler", "value": "404/error"}
                            ],
                            expires_in_hours=168,
                        ))
        except Exception as e:
            logger.warning(f"Robots.txt fetch check failed: {e}")

        return signals
