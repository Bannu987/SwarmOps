"""
WordPress Integration - MarketingOS 2.0
Publish posts and pages directly to WordPress via the REST API.

Requires:
  - WORDPRESS_URL, WORDPRESS_USERNAME, WORDPRESS_APP_PASSWORD in .env
  - Application Passwords enabled in WordPress (Settings → Users → Profile)
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()


class WordPress:
    def __init__(self):
        self.available = False
        self.base_url = os.getenv("WORDPRESS_URL", "").rstrip("/")
        self.username = os.getenv("WORDPRESS_USERNAME", "")
        self.app_password = os.getenv("WORDPRESS_APP_PASSWORD", "")
        self._initialize()

    def _initialize(self):
        if not self.base_url:
            print("⚠️  [WordPress] WORDPRESS_URL not set")
            return
        if not self.username or not self.app_password:
            print("⚠️  [WordPress] WORDPRESS_USERNAME / WORDPRESS_APP_PASSWORD not set")
            return
        try:
            resp = requests.get(
                f"{self.base_url}/wp-json/wp/v2/posts?per_page=1",
                auth=(self.username, self.app_password),
                timeout=10,
            )
            if resp.status_code == 200:
                self.available = True
                print("✅ [WordPress] Connected")
            else:
                print(f"⚠️  [WordPress] Connection returned {resp.status_code}")
        except Exception as e:
            print(f"⚠️  [WordPress] Connection failed: {e}")

    def _url(self, endpoint):
        return f"{self.base_url}/wp-json/wp/v2/{endpoint}"

    def _auth(self):
        return (self.username, self.app_password)

    # ------------------------------------------------------------------

    def create_post(self, title, content, status="draft", categories=None, tags=None):
        """
        Create a blog post.
        status: 'draft' or 'publish'
        Returns: {post_id, url, status, title} or None
        """
        if not self.available:
            return None
        try:
            payload = {"title": title, "content": content, "status": status}
            if categories:
                payload["categories"] = categories
            if tags:
                payload["tags"] = tags

            resp = requests.post(
                self._url("posts"),
                auth=self._auth(),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "post_id": data.get("id"),
                "url": data.get("link", ""),
                "status": data.get("status", ""),
                "title": data.get("title", {}).get("rendered", title),
                "created_at": data.get("date", ""),
            }
        except Exception as e:
            print(f"❌ [WordPress] Create post: {e}")
            return None

    def publish_post(self, post_id):
        """Publish a draft post by ID."""
        if not self.available:
            return None
        try:
            resp = requests.post(
                self._url(f"posts/{post_id}"),
                auth=self._auth(),
                json={"status": "publish"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "post_id": post_id,
                "status": "published",
                "url": data.get("link", ""),
            }
        except Exception as e:
            print(f"❌ [WordPress] Publish post: {e}")
            return None

    def update_post(self, post_id, title=None, content=None):
        """Update an existing post's title and/or content."""
        if not self.available:
            return None
        try:
            payload = {}
            if title:
                payload["title"] = title
            if content:
                payload["content"] = content

            resp = requests.post(
                self._url(f"posts/{post_id}"),
                auth=self._auth(),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            return {"post_id": post_id, "status": "updated", "url": resp.json().get("link", "")}
        except Exception as e:
            print(f"❌ [WordPress] Update post: {e}")
            return None

    def get_posts(self, per_page=20, status="publish", search=None, category_id=None):
        """
        Get existing posts.
        Returns: list[{id, title, url, date, status}] or None
        """
        if not self.available:
            return None
        try:
            params = {"per_page": per_page, "status": status, "orderby": "date", "order": "DESC"}
            if search:
                params["search"] = search
            if category_id:
                params["categories"] = category_id

            resp = requests.get(
                self._url("posts"), auth=self._auth(), params=params, timeout=10
            )
            resp.raise_for_status()
            return [
                {
                    "id": p.get("id"),
                    "title": p.get("title", {}).get("rendered", ""),
                    "url": p.get("link", ""),
                    "date": p.get("date", ""),
                    "status": p.get("status", ""),
                }
                for p in resp.json()
            ]
        except Exception as e:
            print(f"❌ [WordPress] Get posts: {e}")
            return None

    def create_page(self, title, content, slug=None, status="publish"):
        """
        Create a WordPress page (not a blog post).
        Returns: {page_id, url, status, title} or None
        """
        if not self.available:
            return None
        try:
            payload = {"title": title, "content": content, "status": status}
            if slug:
                payload["slug"] = slug

            resp = requests.post(
                self._url("pages"),
                auth=self._auth(),
                json=payload,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            return {
                "page_id": data.get("id"),
                "url": data.get("link", ""),
                "status": data.get("status", ""),
                "title": title,
            }
        except Exception as e:
            print(f"❌ [WordPress] Create page: {e}")
            return None

    def get_categories(self):
        """Get all categories. Returns: list[{id, name, slug, count}] or None"""
        if not self.available:
            return None
        try:
            resp = requests.get(
                self._url("categories"),
                auth=self._auth(),
                params={"per_page": 100},
                timeout=10,
            )
            resp.raise_for_status()
            return [
                {
                    "id": c.get("id"),
                    "name": c.get("name", ""),
                    "slug": c.get("slug", ""),
                    "count": c.get("count", 0),
                }
                for c in resp.json()
            ]
        except Exception as e:
            print(f"❌ [WordPress] Get categories: {e}")
            return None
