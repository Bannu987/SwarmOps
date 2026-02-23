"""
Benchmarks - SwarmOps
Real industry benchmark data for all marketing agents.
Sources: WordStream, HubSpot, Mailchimp, Google, Statista (2024-2025)
"""

# ---------------------------------------------------------------------------
# INDUSTRY BENCHMARKS
# ---------------------------------------------------------------------------

BENCHMARKS = {
    "ecommerce": {
        "avg_conversion_rate": 2.86,
        "avg_bounce_rate": 47.0,
        "avg_session_duration": 138,        # seconds
        "avg_email_open_rate": 15.68,
        "avg_email_ctr": 2.01,
        "avg_cac": 45.27,
        "avg_ltv": 168.0,
        "avg_roas": 4.0,
        "avg_cpc_google": 1.16,
        "avg_cpc_facebook": 0.70,
        "avg_organic_ctr_pos1": 27.6,
        "avg_cart_abandonment": 69.8,
        "avg_repeat_purchase_rate": 28.2,
        "avg_email_revenue_per_send": 0.08,
    },
    "saas": {
        "avg_conversion_rate": 3.0,
        "avg_bounce_rate": 38.0,
        "avg_trial_to_paid": 15.0,
        "avg_churn_rate": 5.0,
        "avg_email_open_rate": 21.5,
        "avg_email_ctr": 2.4,
        "avg_cac": 205.0,
        "avg_ltv": 2400.0,
        "avg_roas": 3.5,
        "avg_cpc_google": 1.91,
        "avg_payback_period_months": 12,
        "avg_nps": 31,
        "avg_mrr_growth_rate": 10.0,
    },
    "local_business": {
        "avg_conversion_rate": 3.5,
        "avg_bounce_rate": 42.0,
        "avg_google_maps_ctr": 5.0,
        "avg_cpc_google": 2.12,
        "avg_email_open_rate": 19.7,
        "avg_review_response_rate": 53.0,
        "avg_repeat_customer_rate": 40.0,
        "avg_referral_rate": 16.0,
    },
    "b2b": {
        "avg_conversion_rate": 2.23,
        "avg_bounce_rate": 56.0,
        "avg_email_open_rate": 15.14,
        "avg_email_ctr": 2.44,
        "avg_cac": 536.0,
        "avg_deal_cycle_days": 102,
        "avg_lead_to_close": 2.0,          # percent
        "avg_content_engagement_rate": 3.5,
        "avg_linkedin_engagement": 0.54,
        "avg_cold_email_reply_rate": 8.5,
    },
    "healthcare": {
        "avg_conversion_rate": 3.36,
        "avg_cpc_google": 2.62,
        "avg_email_open_rate": 21.48,
        "avg_bounce_rate": 58.0,
        "avg_appointment_no_show": 19.0,
        "avg_patient_retention": 70.0,
    },
    "education": {
        "avg_conversion_rate": 3.6,
        "avg_cpc_google": 2.40,
        "avg_email_open_rate": 23.42,
        "avg_email_ctr": 2.75,
        "avg_bounce_rate": 49.0,
        "avg_course_completion_rate": 15.0,
    },
    "fintech": {
        "avg_conversion_rate": 2.2,
        "avg_cpc_google": 3.44,
        "avg_email_open_rate": 18.0,
        "avg_churn_rate": 3.5,
        "avg_bounce_rate": 44.0,
        "avg_activation_rate": 35.0,
        "avg_referral_conversion": 12.0,
    },
    "real_estate": {
        "avg_conversion_rate": 2.47,
        "avg_cpc_google": 2.37,
        "avg_email_open_rate": 19.17,
        "avg_bounce_rate": 52.0,
        "avg_lead_response_time_hours": 5.0,
    },
    "general": {
        "avg_conversion_rate": 2.9,
        "avg_bounce_rate": 47.0,
        "avg_email_open_rate": 17.8,
        "avg_email_ctr": 2.2,
        "avg_cac": 100.0,
        "avg_roas": 3.0,
        "avg_cpc_google": 1.72,
        "avg_session_duration": 120,
    },
}

# Platform-specific benchmarks
SOCIAL_BENCHMARKS = {
    "instagram": {
        "avg_engagement_rate": 1.22,        # percent of followers
        "avg_reach_rate": 9.4,
        "avg_story_completion_rate": 75.0,
        "avg_reel_plays_per_follower": 0.4,
        "best_post_times": ["6am-9am", "12pm-2pm", "5pm-7pm"],
        "best_post_days": ["Tuesday", "Wednesday", "Friday"],
    },
    "linkedin": {
        "avg_engagement_rate": 0.54,
        "avg_click_through_rate": 0.44,
        "avg_share_rate": 0.21,
        "best_post_times": ["7am-9am", "12pm"],
        "best_post_days": ["Tuesday", "Wednesday", "Thursday"],
    },
    "twitter": {
        "avg_engagement_rate": 0.045,
        "avg_retweet_rate": 0.012,
        "best_post_times": ["9am", "12pm", "6pm"],
        "best_post_days": ["Tuesday", "Wednesday"],
    },
    "facebook": {
        "avg_organic_reach_rate": 5.2,
        "avg_engagement_rate": 0.18,
        "avg_video_completion_rate": 21.0,
        "best_post_times": ["1pm-4pm"],
        "best_post_days": ["Wednesday", "Thursday", "Friday"],
    },
    "tiktok": {
        "avg_engagement_rate": 4.25,
        "avg_video_completion_rate": 52.0,
        "avg_follower_growth_rate": 8.0,
        "best_post_times": ["6am-10am", "7pm-11pm"],
    },
}

# SEO benchmarks
SEO_BENCHMARKS = {
    "organic_ctr_by_position": {
        1: 27.6, 2: 15.8, 3: 11.0, 4: 8.4, 5: 6.3,
        6: 4.9, 7: 3.9, 8: 3.1, 9: 2.6, 10: 2.2,
    },
    "avg_page_load_time_acceptable": 2.5,       # seconds
    "avg_core_web_vitals_lcp_good": 2.5,        # seconds
    "avg_core_web_vitals_fid_good": 100,         # ms
    "avg_core_web_vitals_cls_good": 0.1,
    "avg_domain_authority_new_site": 20,
    "avg_backlinks_per_ranking_page": 35,
    "avg_word_count_top10": 1447,
}


# ---------------------------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------------------------

def get_benchmark(industry: str = "general") -> dict:
    """
    Get benchmark data for an industry.
    Falls back to 'general' if industry not found.

    Args:
        industry: Industry name (case-insensitive)
    Returns:
        dict of benchmark metrics
    """
    industry_lower = industry.lower().strip()

    # Try exact match first
    if industry_lower in BENCHMARKS:
        return BENCHMARKS[industry_lower]

    # Fuzzy matching for common variations
    aliases = {
        "e-commerce": "ecommerce",
        "e commerce": "ecommerce",
        "online store": "ecommerce",
        "online retail": "ecommerce",
        "software": "saas",
        "software as a service": "saas",
        "tech": "saas",
        "startup": "saas",
        "b2b saas": "saas",
        "restaurant": "local_business",
        "retail": "local_business",
        "service business": "local_business",
        "marketing agency": "b2b",
        "consulting": "b2b",
        "enterprise": "b2b",
        "finance": "fintech",
        "banking": "fintech",
        "insurance": "fintech",
        "health": "healthcare",
        "medical": "healthcare",
        "dental": "healthcare",
        "university": "education",
        "school": "education",
        "online course": "education",
        "property": "real_estate",
        "housing": "real_estate",
    }

    for alias, canonical in aliases.items():
        if alias in industry_lower:
            return BENCHMARKS[canonical]

    return BENCHMARKS["general"]


def compare_to_benchmark(metric_name: str, actual_value: float, industry: str = "general") -> dict:
    """
    Compare a metric to industry benchmark.

    Args:
        metric_name: e.g., "avg_conversion_rate"
        actual_value: The actual metric value
        industry: Industry for comparison

    Returns:
        {
            "benchmark": 2.86,
            "actual": 1.8,
            "delta": -1.06,
            "delta_pct": -37.1,
            "rating": "below_average",
            "interpretation": "Your conversion rate of 1.8% is 37% below the ecommerce average of 2.86%",
            "opportunity": "Improving to benchmark could mean +X% more conversions"
        }
    """
    benchmarks = get_benchmark(industry)
    benchmark_value = benchmarks.get(metric_name)

    if benchmark_value is None:
        return {
            "benchmark": None,
            "actual": actual_value,
            "delta": None,
            "delta_pct": None,
            "rating": "no_benchmark",
            "interpretation": f"No {industry} benchmark available for {metric_name}",
        }

    delta = actual_value - benchmark_value
    delta_pct = (delta / benchmark_value) * 100 if benchmark_value != 0 else 0

    # Rating
    if delta_pct >= 20:
        rating = "excellent"
    elif delta_pct >= 5:
        rating = "above_average"
    elif delta_pct >= -5:
        rating = "average"
    elif delta_pct >= -20:
        rating = "below_average"
    else:
        rating = "poor"

    # Human-readable name
    readable = metric_name.replace("avg_", "").replace("_", " ")
    industry_readable = industry.replace("_", " ")

    interpretation = (
        f"Your {readable} of {actual_value} is "
        f"{'above' if delta >= 0 else 'below'} the {industry_readable} "
        f"benchmark of {benchmark_value} ({delta_pct:+.1f}%)"
    )

    return {
        "benchmark": benchmark_value,
        "actual": actual_value,
        "delta": round(delta, 4),
        "delta_pct": round(delta_pct, 1),
        "rating": rating,
        "interpretation": interpretation,
        "industry": industry,
    }


def get_all_benchmarks_summary(industry: str = "general") -> str:
    """
    Return a formatted string summary of benchmarks for an industry.
    Useful for injecting into agent prompts.
    """
    b = get_benchmark(industry)
    industry_readable = industry.replace("_", " ").title()

    lines = [f"INDUSTRY BENCHMARKS ({industry_readable}):"]

    metric_labels = {
        "avg_conversion_rate": "Conversion Rate",
        "avg_bounce_rate": "Bounce Rate",
        "avg_email_open_rate": "Email Open Rate",
        "avg_email_ctr": "Email CTR",
        "avg_cac": "Customer Acquisition Cost",
        "avg_ltv": "Customer Lifetime Value",
        "avg_roas": "Return on Ad Spend",
        "avg_cpc_google": "Google Ads CPC",
        "avg_churn_rate": "Monthly Churn Rate",
        "avg_session_duration": "Avg Session Duration (sec)",
    }

    for key, label in metric_labels.items():
        if key in b:
            unit = "$" if "cac" in key or "ltv" in key or "cpc" in key else ""
            suffix = "%" if "rate" in key or "bounce" in key else ""
            lines.append(f"  - {label}: {unit}{b[key]}{suffix}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(get_all_benchmarks_summary("saas"))
    print()
    result = compare_to_benchmark("avg_conversion_rate", 1.8, "ecommerce")
    print(result["interpretation"])
