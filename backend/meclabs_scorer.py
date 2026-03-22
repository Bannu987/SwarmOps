"""
MECLABS Conversion Heuristic Scorer for SwarmOps.
C = 4m + 3v + 2(i-f) - 2a

Pure Python — no dependencies.
"""


class MECLABSScorer:
    """Score conversion probability using MECLABS heuristic."""

    def score(self, motivation, value_prop, incentive, friction, anxiety):
        """
        Calculate MECLABS conversion score.
        All inputs: 1-10 scale.
        Returns dict with score, grade, components, weakest factor.
        """
        m = max(1, min(10, motivation))
        v = max(1, min(10, value_prop))
        i = max(1, min(10, incentive))
        f = max(1, min(10, friction))
        a = max(1, min(10, anxiety))

        c = 4 * m + 3 * v + 2 * (i - f) - 2 * a

        if c >= 60:
            grade = "Strong"
        elif c >= 40:
            grade = "Moderate"
        elif c >= 20:
            grade = "Weak"
        else:
            grade = "Critical"

        # Identify weakest factor by contribution
        factors = {
            "motivation":        {"score": m, "contribution": 4 * m,  "inverted": False},
            "value_proposition": {"score": v, "contribution": 3 * v,  "inverted": False},
            "incentive":         {"score": i, "contribution": 2 * i,  "inverted": False},
            "friction":          {"score": f, "contribution": -2 * f, "inverted": True},
            "anxiety":           {"score": a, "contribution": -2 * a, "inverted": True},
        }

        weakest = min(
            factors,
            key=lambda name: (
                -factors[name]["contribution"]   # high negative = worst
                if factors[name]["inverted"]
                else factors[name]["contribution"]  # low positive = worst
            )
        )

        return {
            "total_score": c,
            "grade": grade,
            "max_possible": 86,
            "components": {
                "motivation":        {"score": m, "weighted": 4 * m},
                "value_proposition": {"score": v, "weighted": 3 * v},
                "incentive":         {"score": i, "weighted": 2 * i},
                "friction":          {"score": f, "weighted": -2 * f},
                "anxiety":           {"score": a, "weighted": -2 * a},
            },
            "weakest_factor": weakest,
            "formula": f"C = 4({m}) + 3({v}) + 2({i}-{f}) - 2({a}) = {c}",
        }

    def lift_model_score(self, value_prop, clarity, relevance,
                         distraction, urgency, anxiety):
        """
        Score a page using the LIFT Model (1-10 each).
        Drivers: Value Prop, Clarity, Relevance, Urgency
        Inhibitors: Distraction, Anxiety
        """
        drivers_avg = (value_prop + clarity + relevance + urgency) / 4
        inhibitors_avg = (distraction + anxiety) / 2
        lift_score = round(drivers_avg * 10 - inhibitors_avg * 5, 1)

        drivers = {
            "value_proposition": value_prop,
            "clarity": clarity,
            "relevance": relevance,
            "urgency": urgency,
        }
        inhibitors = {
            "distraction": distraction,
            "anxiety": anxiety,
        }

        weakest_driver = min(drivers, key=drivers.get)
        strongest_inhibitor = max(inhibitors, key=inhibitors.get)

        return {
            "lift_score": lift_score,
            "factors": {**drivers, **inhibitors},
            "weakest_driver": weakest_driver,
            "strongest_inhibitor": strongest_inhibitor,
            "priority_fix": (
                weakest_driver if drivers[weakest_driver] < 5
                else strongest_inhibitor
            ),
        }


# Module-level singleton
_scorer = None


def get_meclabs_scorer() -> MECLABSScorer:
    global _scorer
    if _scorer is None:
        _scorer = MECLABSScorer()
    return _scorer
