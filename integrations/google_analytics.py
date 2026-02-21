"""
Google Analytics 4 Integration - SwarmOps
Pulls real traffic, conversion, and behavioral data from GA4.

Requires:
  - google-analytics-data package (pip install google-analytics-data)
  - Google Cloud service account JSON with Analytics Data API enabled
  - GA4 Property ID in .env
"""

import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class GoogleAnalytics:
    def __init__(self):
        self.available = False
        self.client = None
        self.property_id = os.getenv("GA4_PROPERTY_ID", "")
        self.sa_file = os.getenv(
            "GOOGLE_SERVICE_ACCOUNT_JSON", "google_service_account.json"
        )
        self._initialize()

    def _initialize(self):
        if not os.path.exists(self.sa_file):
            print(f"⚠️  [GA4] Service account file not found: {self.sa_file}")
            return
        if not self.property_id:
            print("⚠️  [GA4] GA4_PROPERTY_ID not set in .env")
            return
        try:
            from google.analytics.data_v1beta import BetaAnalyticsDataClient
            from google.oauth2 import service_account

            credentials = service_account.Credentials.from_service_account_file(
                self.sa_file,
                scopes=["https://www.googleapis.com/auth/analytics.readonly"],
            )
            self.client = BetaAnalyticsDataClient(credentials=credentials)
            self.available = True
            print("✅ [GA4] Google Analytics 4 connected")
        except ImportError:
            print("⚠️  [GA4] Install: pip install google-analytics-data")
        except Exception as e:
            print(f"⚠️  [GA4] Connection failed: {e}")

    def _run_report(self, date_range, metrics, dimensions=None, order_bys=None, limit=None):
        """Helper: run a GA4 report with standard params."""
        from google.analytics.data_v1beta.types import RunReportRequest

        kwargs = {
            "property": f"properties/{self.property_id}",
            "date_ranges": [date_range],
            "metrics": metrics,
        }
        if dimensions:
            kwargs["dimensions"] = dimensions
        if order_bys:
            kwargs["order_bys"] = order_bys
        if limit:
            kwargs["limit"] = limit

        return self.client.run_report(RunReportRequest(**kwargs))

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def get_traffic_summary(self, days=30):
        """
        Traffic summary for the last N days.
        Returns: dict or None
        """
        if not self.available:
            return None
        try:
            from google.analytics.data_v1beta.types import DateRange, Metric

            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            resp = self._run_report(
                date_range=DateRange(start_date=start, end_date=end),
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="totalUsers"),
                    Metric(name="screenPageViews"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="newUsers"),
                    Metric(name="conversions"),
                ],
            )

            if not resp.rows:
                return None

            v = resp.rows[0].metric_values
            sessions = int(v[0].value)
            conversions = int(v[6].value)
            return {
                "sessions": sessions,
                "users": int(v[1].value),
                "pageviews": int(v[2].value),
                "bounce_rate": round(float(v[3].value) * 100, 1),
                "avg_session_duration": round(float(v[4].value), 1),
                "new_users": int(v[5].value),
                "conversions": conversions,
                "conversion_rate": round((conversions / sessions * 100), 2) if sessions else 0,
                "period_days": days,
            }
        except Exception as e:
            print(f"❌ [GA4] Traffic summary error: {e}")
            return None

    def get_traffic_sources(self, days=30):
        """
        Traffic breakdown by source / medium with conversions.
        Returns: list[dict] or None
        """
        if not self.available:
            return None
        try:
            from google.analytics.data_v1beta.types import (
                DateRange, Dimension, Metric, OrderBy,
            )

            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            resp = self._run_report(
                date_range=DateRange(start_date=start, end_date=end),
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="conversions"),
                    Metric(name="totalUsers"),
                ],
                dimensions=[
                    Dimension(name="sessionSource"),
                    Dimension(name="sessionMedium"),
                ],
                order_bys=[
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(name="sessions"),
                        descending=True,
                    )
                ],
                limit=20,
            )

            sources = []
            for row in resp.rows:
                sessions = int(row.metric_values[0].value)
                conversions = int(row.metric_values[1].value)
                sources.append(
                    {
                        "source": row.dimension_values[0].value,
                        "medium": row.dimension_values[1].value,
                        "sessions": sessions,
                        "conversions": conversions,
                        "users": int(row.metric_values[2].value),
                        "conversion_rate": round((conversions / sessions * 100), 1)
                        if sessions
                        else 0,
                    }
                )
            return sources
        except Exception as e:
            print(f"❌ [GA4] Traffic sources error: {e}")
            return None

    def get_page_performance(self, days=30, top_n=50):
        """
        Per-page performance: sessions, bounce rate, duration, conversions.
        Returns: list[dict] or None
        """
        if not self.available:
            return None
        try:
            from google.analytics.data_v1beta.types import (
                DateRange, Dimension, Metric, OrderBy,
            )

            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            resp = self._run_report(
                date_range=DateRange(start_date=start, end_date=end),
                metrics=[
                    Metric(name="sessions"),
                    Metric(name="bounceRate"),
                    Metric(name="averageSessionDuration"),
                    Metric(name="conversions"),
                ],
                dimensions=[Dimension(name="pagePath")],
                order_bys=[
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(name="sessions"),
                        descending=True,
                    )
                ],
                limit=top_n,
            )

            pages = []
            for row in resp.rows:
                sessions = int(row.metric_values[0].value)
                conversions = int(row.metric_values[3].value)
                pages.append(
                    {
                        "page_path": row.dimension_values[0].value,
                        "sessions": sessions,
                        "bounce_rate": round(float(row.metric_values[1].value) * 100, 1),
                        "avg_duration": round(float(row.metric_values[2].value), 1),
                        "conversions": conversions,
                        "conversion_rate": round((conversions / sessions * 100), 1)
                        if sessions
                        else 0,
                    }
                )
            return pages
        except Exception as e:
            print(f"❌ [GA4] Page performance error: {e}")
            return None

    def get_conversion_events(self, days=30):
        """
        Key events / conversion events with counts.
        Returns: dict{event_name: {count, conversions}} or None
        """
        if not self.available:
            return None
        try:
            from google.analytics.data_v1beta.types import (
                DateRange, Dimension, Metric, OrderBy,
            )

            end = datetime.now().strftime("%Y-%m-%d")
            start = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            resp = self._run_report(
                date_range=DateRange(start_date=start, end_date=end),
                metrics=[Metric(name="eventCount"), Metric(name="conversions")],
                dimensions=[Dimension(name="eventName")],
                order_bys=[
                    OrderBy(
                        metric=OrderBy.MetricOrderBy(name="eventCount"),
                        descending=True,
                    )
                ],
                limit=30,
            )

            events = {}
            for row in resp.rows:
                events[row.dimension_values[0].value] = {
                    "count": int(row.metric_values[0].value),
                    "conversions": int(row.metric_values[1].value),
                }
            return events
        except Exception as e:
            print(f"❌ [GA4] Conversion events error: {e}")
            return None

    def detect_anomalies(self, days=7):
        """
        Compare last N days to the previous N-day window.
        Flags any metric that changed by more than 20%.
        Returns: dict{anomalies: [...], checked_at} or None
        """
        if not self.available:
            return None
        try:
            from google.analytics.data_v1beta.types import DateRange, Metric

            now = datetime.now()
            metrics = [
                Metric(name="sessions"),
                Metric(name="totalUsers"),
                Metric(name="conversions"),
                Metric(name="bounceRate"),
            ]
            labels = ["Sessions", "Users", "Conversions", "Bounce Rate"]

            def _period(start_dt, end_dt):
                resp = self._run_report(
                    date_range=DateRange(
                        start_date=start_dt.strftime("%Y-%m-%d"),
                        end_date=end_dt.strftime("%Y-%m-%d"),
                    ),
                    metrics=metrics,
                )
                if resp.rows:
                    return [float(v.value) for v in resp.rows[0].metric_values]
                return None

            current = _period(now - timedelta(days=days), now)
            previous = _period(now - timedelta(days=days * 2), now - timedelta(days=days))

            if not current or not previous:
                return None

            anomalies = []
            for i, label in enumerate(labels):
                if previous[i] == 0:
                    continue
                change_pct = ((current[i] - previous[i]) / previous[i]) * 100
                if abs(change_pct) > 20:
                    anomalies.append(
                        {
                            "metric": label,
                            "current": round(current[i], 2),
                            "previous": round(previous[i], 2),
                            "change_pct": round(change_pct, 1),
                            "direction": "up" if change_pct > 0 else "down",
                            "severity": "critical" if abs(change_pct) > 50 else "warning",
                        }
                    )

            return {
                "anomalies": anomalies,
                "checked_at": now.isoformat(),
                "period_days": days,
            }
        except Exception as e:
            print(f"❌ [GA4] Anomaly detection error: {e}")
            return None
