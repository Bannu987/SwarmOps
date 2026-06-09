import logging
from typing import Dict, List, Optional
from .registry import CANONICAL_REGISTRY
from ..supabase_client import get_admin_client

logger = logging.getLogger(__name__)

def calculate_priority_score(impact: float, urgency: float, confidence: float, business_relevance: float, effort: float) -> float:
    """
    Calculate priority score using the formula:
    ((impact * 0.45) + (urgency * 0.25) + (confidence * 0.20) + (business_relevance * 0.10)) / max(effort, 1)
    """
    numerator = (impact * 0.45) + (urgency * 0.25) + (confidence * 0.20) + (business_relevance * 0.10)
    denominator = max(effort, 1.0)
    return round(numerator / denominator, 2)

def get_priority_bucket(score: float) -> str:
    """Bucket a priority score into Low, Medium, High, or Critical."""
    if score >= 7.0:
        return "Critical"
    elif score >= 5.0:
        return "High"
    elif score >= 3.0:
        return "Medium"
    else:
        return "Low"

def map_signal_to_registry_key(signal_title: str, signal_type_db: str) -> Optional[str]:
    """Map database signal title/type to canonical registry keys."""
    title_lower = signal_title.lower()
    if "robots.txt" in title_lower:
        if "block" in title_lower:
            return "robots_txt_blocks_all"
        return "missing_robots_txt"
    if "sitemap" in title_lower:
        return "missing_sitemap"
    if "meta description" in title_lower:
        if "duplicate" in title_lower:
            return "duplicate_meta_description"
        return "missing_meta_description"
    if "title" in title_lower:
        if "duplicate" in title_lower:
            return "duplicate_title"
        return "missing_title"
    if "canonical" in title_lower:
        return "missing_canonical"
    if "json-ld" in title_lower or "schema" in title_lower:
        if "person" in title_lower:
            return "missing_person_schema"
        if "organization" in title_lower or "company" in title_lower:
            return "missing_organization_schema"
        return "missing_json_ld"
    if "open graph" in title_lower or "og:" in title_lower:
        return "missing_open_graph"
    if "analytics" in title_lower or "gtm" in title_lower or "ga4" in title_lower:
        return "missing_ga4_or_gtm"
    if "cta" in title_lower or "call to action" in title_lower:
        return "missing_primary_cta"
    if "lead capture" in title_lower or "form" in title_lower:
        return "missing_lead_capture"
    if "trust" in title_lower or "testimonial" in title_lower or "review" in title_lower:
        return "weak_trust_signals"
    return None

def recalculate_project_health(project_id: str, user_id: str) -> Dict[str, float]:
    """Recalculate category-specific and overall health scores for a project."""
    scores = {
        "seo": 100.0,
        "aeo": 100.0,
        "tracking": 100.0,
        "conversion": 100.0,
        "trust": 100.0
    }
    
    admin = get_admin_client()
    if not admin:
        return scores
        
    try:
        # Fetch active signals for the project
        res = admin.table("signals").select("*").eq("project_id", project_id).eq("status", "active").execute()
        active_signals = res.data or []
    except Exception as e:
        logger.warning(f"Failed to fetch active signals for project health calculation: {e}")
        return scores

    # Deduct points based on signal impact
    for sig in active_signals:
        title = sig.get("title", "")
        db_type = sig.get("signal_type", "")
        reg_key = map_signal_to_registry_key(title, db_type)
        
        impact = 5.0  # default fallback impact
        category = "seo"
        
        if reg_key and reg_key in CANONICAL_REGISTRY:
            entry = CANONICAL_REGISTRY[reg_key]
            impact = entry.default_impact_score
            category = entry.category
            
        deduction = impact * 1.5
        
        if category == "seo" or reg_key in ["missing_robots_txt", "robots_txt_blocks_all", "missing_sitemap", "missing_canonical", "missing_title", "duplicate_title", "missing_meta_description", "duplicate_meta_description"]:
            scores["seo"] -= deduction
        elif category == "aeo" or reg_key in ["missing_json_ld", "missing_person_schema", "missing_organization_schema"]:
            scores["aeo"] -= deduction
        elif category == "analytics" or reg_key in ["missing_ga4_or_gtm"]:
            scores["tracking"] -= deduction
        elif category == "cro" or reg_key in ["missing_primary_cta", "missing_lead_capture"]:
            scores["conversion"] -= deduction
        elif reg_key in ["weak_trust_signals"]:
            scores["trust"] -= deduction
            
    # Cap scores between 0 and 100
    for k in scores:
        scores[k] = max(0.0, min(100.0, round(scores[k], 1)))
        
    overall_score = round(sum(scores.values()) / len(scores), 1)
    
    # Try to persist to database
    try:
        # Check if health_scores entry exists
        h_res = admin.table("health_scores").select("id").eq("project_id", project_id).execute()
        health_data = {
            "user_id": user_id,
            "project_id": project_id,
            "overall_score": overall_score,
            "seo_score": scores["seo"],
            "aeo_score": scores["aeo"],
            "tracking_score": scores["tracking"],
            "conversion_score": scores["conversion"],
            "trust_score": scores["trust"]
        }
        if h_res.data:
            admin.table("health_scores").update(health_data).eq("project_id", project_id).execute()
        else:
            admin.table("health_scores").insert(health_data).execute()
    except Exception as e:
        logger.warning(f"Could not persist health score to database (migration might be pending): {e}")
        
    return {
        "overall": overall_score,
        **scores
    }
