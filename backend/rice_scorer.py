"""
RICE Scorer — prioritizes marketing recommendations.
RICE = Reach × Impact × Confidence / Effort

All components are normalized 0–10.
"""
import re
from typing import List, Dict


class RICEScorer:
    """Score and rank marketing recommendations by RICE framework."""

    # Reach signals — who does this affect?
    _HIGH_REACH = ["all users", "all visitors", "entire", "everyone", "all customers",
                   "homepage", "landing page", "checkout", "global", "site-wide"]
    _LOW_REACH = ["niche", "segment", "subset", "specific", "targeted", "small"]

    # Impact signals — how much does this move the needle?
    _HIGH_IMPACT = ["revenue", "conversion", "sales", "leads", "traffic", "retention",
                    "churn", "acquisition", "sign-up", "purchase", "booking", "demo"]
    _LOW_IMPACT = ["branding", "awareness", "engagement", "likes", "followers",
                   "impression", "visibility", "tone", "style"]

    # Effort signals — how hard is this to implement?
    _LOW_EFFORT = ["quick win", "easy", "simple", "one-time", "template", "copy",
                   "update", "tweak", "adjust", "add", "enable", "turn on",
                   "meta", "title tag", "alt text", "cta button"]
    _HIGH_EFFORT = ["rebuild", "redesign", "overhaul", "rewrite", "migrate",
                    "integrate", "develop", "build", "launch", "restructure",
                    "new system", "full", "complete", "comprehensive"]

    # Confidence — how certain are we this will work?
    _HIGH_CONFIDENCE = ["proven", "data shows", "studies show", "benchmark",
                        "industry standard", "best practice", "tested", "a/b",
                        "split test", "statistically"]
    _LOW_CONFIDENCE = ["might", "could potentially", "possibly", "unsure",
                       "experimental", "new", "untested", "hypothesis"]

    def score(self, recommendation: str) -> Dict:
        """
        Score a single recommendation string.

        Returns:
            dict with reach, impact, confidence, effort, rice_score, priority_tier
        """
        text = recommendation.lower()

        reach = self._score_reach(text)
        impact = self._score_impact(text)
        confidence = self._score_confidence(text)
        effort = self._score_effort(text)

        # RICE = (R × I × C) / E  — normalized to 0-100
        # Max theoretical: 10×10×10/1=1000 → divide by 10 to get 0-100 range
        if effort == 0:
            effort = 1
        raw = (reach * impact * confidence) / effort
        rice_score = round(min(raw / 10, 100), 1)

        if rice_score >= 8:
            priority_tier = "P0 — Do immediately"
        elif rice_score >= 4:
            priority_tier = "P1 — Do this quarter"
        elif rice_score >= 2:
            priority_tier = "P2 — Plan for next quarter"
        else:
            priority_tier = "P3 — Backlog"

        return {
            "text": recommendation,
            "reach": reach,
            "impact": impact,
            "confidence": confidence,
            "effort": effort,
            "rice_score": rice_score,
            "priority_tier": priority_tier,
        }

    def rank_recommendations(self, recommendations: List[str]) -> List[Dict]:
        """Score and rank a list of recommendation strings by RICE score."""
        scored = [self.score(r) for r in recommendations]
        scored.sort(key=lambda x: x["rice_score"], reverse=True)
        return scored

    def classify_intent_impact(self, message: str) -> str:
        """
        Classify what type of business impact the user's request targets.

        Returns one of: revenue | leads | traffic | retention | brand | unknown
        """
        msg = message.lower()
        if any(w in msg for w in ["revenue", "sales", "conversion", "sell", "purchase", "checkout"]):
            return "revenue"
        if any(w in msg for w in ["leads", "lead gen", "prospect", "sign-up", "signup", "demo request"]):
            return "leads"
        if any(w in msg for w in ["traffic", "visitors", "organic", "seo", "search", "ranking"]):
            return "traffic"
        if any(w in msg for w in ["retain", "churn", "loyalty", "repeat", "customer success", "ltv"]):
            return "retention"
        if any(w in msg for w in ["brand", "awareness", "perception", "reputation", "social"]):
            return "brand"
        return "unknown"

    # ------------------------------------------------------------------
    # Private scoring helpers — each returns 1–10
    # ------------------------------------------------------------------

    def _score_reach(self, text: str) -> float:
        score = 5.0
        for s in self._HIGH_REACH:
            if s in text:
                score = min(score + 2, 10)
                break
        for s in self._LOW_REACH:
            if s in text:
                score = max(score - 2, 1)
                break
        return score

    def _score_impact(self, text: str) -> float:
        score = 4.0
        hits = sum(1 for s in self._HIGH_IMPACT if s in text)
        score += min(hits * 1.5, 4)
        for s in self._LOW_IMPACT:
            if s in text:
                score = max(score - 1.5, 1)
                break
        return min(score, 10)

    def _score_effort(self, text: str) -> float:
        """Higher effort number = harder. We want low effort to boost RICE."""
        score = 5.0
        for s in self._LOW_EFFORT:
            if s in text:
                score = max(score - 2, 1)
                break
        for s in self._HIGH_EFFORT:
            if s in text:
                score = min(score + 2, 10)
                break
        # Word count proxy for complexity
        word_count = len(text.split())
        if word_count > 50:
            score = min(score + 1, 10)
        return score

    def _score_confidence(self, text: str) -> float:
        score = 5.0
        for s in self._HIGH_CONFIDENCE:
            if s in text:
                score = min(score + 2, 10)
                break
        for s in self._LOW_CONFIDENCE:
            if s in text:
                score = max(score - 2, 1)
                break
        return score


# Module-level singleton
_scorer = None

def get_rice_scorer() -> RICEScorer:
    global _scorer
    if _scorer is None:
        _scorer = RICEScorer()
    return _scorer
