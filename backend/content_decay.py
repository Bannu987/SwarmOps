"""
Content Decay Detection for SwarmOps.
Identifies pages losing organic visibility using time-series performance data.
Works with any source — GSC API integration comes in P4.
"""
import logging

logger = logging.getLogger(__name__)


class ContentDecayDetector:
    """Detect and flag content that's losing organic performance."""

    CLICK_DECAY_THRESHOLD = -0.20       # 20% click drop = decay
    CTR_DECAY_THRESHOLD = -0.15         # 15% CTR drop = title/desc issue
    POSITION_DECAY_THRESHOLD = 2.0      # 2+ position drop = content quality issue
    IMPRESSION_STABLE_THRESHOLD = 0.05  # <5% impression change = stable

    def detect_decay(self, current_period: dict, previous_period: dict) -> list:
        """
        Compare two time periods to detect content decay.

        Args:
            current_period: {url: {clicks, impressions, ctr, position}}
            previous_period: {url: {clicks, impressions, ctr, position}}

        Returns:
            list of decay alerts sorted by severity (critical first)
        """
        alerts = []

        for url, current in current_period.items():
            if url not in previous_period:
                continue
            prev = previous_period[url]

            click_delta = self._pct_change(prev.get("clicks", 0), current.get("clicks", 0))
            impression_delta = self._pct_change(prev.get("impressions", 0), current.get("impressions", 0))
            ctr_delta = self._pct_change(prev.get("ctr", 0), current.get("ctr", 0))
            position_change = current.get("position", 0) - prev.get("position", 0)

            # Pattern 1: Content Decay — clicks AND impressions both dropping
            if click_delta < self.CLICK_DECAY_THRESHOLD and impression_delta < self.CLICK_DECAY_THRESHOLD:
                severity = "critical" if click_delta < -0.40 else "warning"
                alerts.append({
                    "url": url,
                    "decay_type": "content_decay",
                    "severity": severity,
                    "metrics": {
                        "click_change": f"{click_delta:+.1%}",
                        "impression_change": f"{impression_delta:+.1%}",
                        "position_change": f"{position_change:+.1f}",
                    },
                    "recommended_action": (
                        "Content refresh needed. Update with fresh data, new sections, "
                        "and current statistics. Check competitor content for gaps."
                    ),
                })

            # Pattern 2: Title/Description Decay — stable impressions, dropping CTR
            elif (
                abs(impression_delta) < self.IMPRESSION_STABLE_THRESHOLD
                and ctr_delta < self.CTR_DECAY_THRESHOLD
            ):
                alerts.append({
                    "url": url,
                    "decay_type": "title_decay",
                    "severity": "warning",
                    "metrics": {
                        "ctr_change": f"{ctr_delta:+.1%}",
                        "impressions": "stable",
                        "position": str(current.get("position", "N/A")),
                    },
                    "recommended_action": (
                        "Rewrite meta title and description. Competitor titles may be more "
                        "compelling. Check for new SERP features (AI Overviews, rich snippets) "
                        "stealing clicks."
                    ),
                })

            # Pattern 3: Position Drop — ranking deteriorated
            elif position_change > self.POSITION_DECAY_THRESHOLD:
                severity = "critical" if position_change > 5 else "warning"
                alerts.append({
                    "url": url,
                    "decay_type": "position_drop",
                    "severity": severity,
                    "metrics": {
                        "old_position": str(prev.get("position", "N/A")),
                        "new_position": str(current.get("position", "N/A")),
                        "position_drop": f"{position_change:+.1f}",
                    },
                    "recommended_action": (
                        "Content quality issue. Competitors likely published superior content. "
                        "Audit top-ranking pages, identify content gaps, and expand/update."
                    ),
                })

        severity_order = {"critical": 0, "warning": 1, "monitor": 2}
        alerts.sort(key=lambda a: severity_order.get(a["severity"], 3))
        return alerts

    def _pct_change(self, old_val, new_val) -> float:
        if old_val == 0:
            return 0.0 if new_val == 0 else 1.0
        return (new_val - old_val) / old_val

    def generate_refresh_brief(self, url: str, decay_alert: dict, brand_context: str = "") -> dict:
        """
        Generate a content refresh brief for a decaying page.
        Used by the Content agent to produce updated content.
        """
        return {
            "url": url,
            "decay_type": decay_alert["decay_type"],
            "severity": decay_alert["severity"],
            "task": "content_refresh",
            "instructions": (
                f"This page is experiencing {decay_alert['decay_type']}.\n"
                f"Metrics: {decay_alert['metrics']}\n\n"
                f"Refresh requirements:\n"
                f"1. Update all statistics and data points to current values\n"
                f"2. Add new sections covering topics competitors now rank for\n"
                f"3. Improve the introduction with a direct, citable answer (AEO format)\n"
                f"4. Add FAQ schema for common questions about this topic\n"
                f"5. Strengthen internal links to and from this page\n"
                f"6. Ensure every 150-200 words includes a specific, verifiable statistic\n\n"
                f"{brand_context}"
            ),
        }


# Module-level singleton
_detector = None


def get_content_decay_detector() -> ContentDecayDetector:
    global _detector
    if _detector is None:
        _detector = ContentDecayDetector()
    return _detector
