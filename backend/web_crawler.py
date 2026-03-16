import os
import re
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from knowledge_base import get_knowledge_base


class WebCrawler:
    """Crawl websites and ingest content into the knowledge base."""

    COMMON_PATHS = [
        "", "/about", "/pricing", "/features", "/product", "/products",
        "/solutions", "/use-cases", "/platform", "/customers",
        "/case-studies", "/blog", "/resources", "/integrations",
        "/services", "/contact", "/faq", "/how-it-works"
    ]

    def __init__(self, knowledge_base=None):
        self.kb = knowledge_base or get_knowledge_base()

    def crawl_website(self, base_url, max_pages=15):
        """Crawl a website and store all pages in knowledge base."""
        from urllib.parse import urlparse
        import requests

        if not base_url.startswith("http"):
            base_url = "https://" + base_url
        base_url = base_url.rstrip("/")
        domain = urlparse(base_url).netloc

        results = {"pages_crawled": 0, "pages_failed": 0, "total_words": 0, "domain": domain}

        self.kb.delete_by_source(base_url)

        urls_to_crawl = [f"{base_url}{path}" for path in self.COMMON_PATHS[:max_pages]]
        brave_key = os.getenv("BRAVE_API_KEY", "")
        serper_key = os.getenv("SERPER_API_KEY", "")

        def fetch_page(url):
            path_part = url.replace(base_url, "").strip("/")
            query = f"site:{domain} {path_part}" if path_part else f"{domain}"

            if brave_key:
                try:
                    resp = requests.get(
                        "https://api.search.brave.com/res/v1/web/search",
                        params={"q": query, "count": 5},
                        headers={"X-Subscription-Token": brave_key},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        items = data.get("web", {}).get("results", [])
                        if items:
                            content = "\n".join(
                                f"{r.get('title','')}\n{r.get('description','')}"
                                for r in items[:5]
                            )
                            return {"url": url, "title": items[0].get("title", url),
                                    "content": content, "success": True}
                except Exception:
                    pass

            if serper_key:
                try:
                    resp = requests.post(
                        "https://google.serper.dev/search",
                        json={"q": query, "num": 5},
                        headers={"X-API-KEY": serper_key},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        organic = data.get("organic", [])
                        if organic:
                            content = "\n".join(
                                f"{r.get('title','')}\n{r.get('snippet','')}"
                                for r in organic[:5]
                            )
                            return {"url": url, "title": organic[0].get("title", url),
                                    "content": content, "success": True}
                except Exception:
                    pass

            return {"url": url, "success": False}

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_page, url): url for url in urls_to_crawl}
            for future in as_completed(futures, timeout=60):
                try:
                    result = future.result(timeout=15)
                    if result.get("success") and result.get("content"):
                        path = result["url"].replace(base_url, "").strip("/")
                        page_type = self._classify_page(path)
                        self.kb.add_document(
                            source_type=page_type,
                            source_url=result["url"],
                            title=result.get("title", path or "Homepage"),
                            content=result["content"],
                            metadata={
                                "domain": domain,
                                "path": path,
                                "crawled_at": datetime.now().isoformat(),
                            },
                        )
                        results["pages_crawled"] += 1
                        results["total_words"] += len(result["content"].split())
                    else:
                        results["pages_failed"] += 1
                except Exception:
                    results["pages_failed"] += 1

        return results

    def _classify_page(self, path):
        path_lower = path.lower()
        if not path_lower or path_lower == "/":
            return "website"
        if "blog" in path_lower or "article" in path_lower:
            return "blog"
        if "pricing" in path_lower or "plans" in path_lower:
            return "pricing"
        if "about" in path_lower or "team" in path_lower:
            return "website"
        if "case" in path_lower or "customer" in path_lower:
            return "social_proof"
        if "docs" in path_lower or "api" in path_lower:
            return "technical"
        if "competitor" in path_lower or " vs " in path_lower:
            return "competitor"
        return "website"

    def crawl_competitor(self, competitor_url, competitor_name):
        """Crawl a competitor website and tag as competitor data."""
        from urllib.parse import urlparse
        from db import get_connection

        results = self.crawl_website(competitor_url, max_pages=8)

        if not competitor_url.startswith("http"):
            competitor_url = "https://" + competitor_url
        domain = urlparse(competitor_url).netloc

        try:
            conn = get_connection()
            conn.execute(
                """UPDATE kb_documents
                   SET source_type = 'competitor',
                       metadata = json_set(metadata, '$.competitor_name', ?)
                   WHERE source_url LIKE ?""",
                (competitor_name, f"%{domain}%"),
            )
            conn.commit()
        except Exception:
            pass

        return results


_crawler_instance = None


def get_web_crawler():
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = WebCrawler()
    return _crawler_instance
