"""
Skeptic Agent - SwarmOps Quality Control
Reviews every agent's output before it reaches the user.
Catches generic, low-quality, or incomplete responses and forces a revision.
Uses tier 1 (Groq) for fast evaluation.
"""

import json
from model_router import call_model_sync


class SkepticAgent:
    """
    The Skeptic — quality control layer for SwarmOps.
    Critiques agent outputs and triggers revisions when needed.
    """

    def __init__(self):
        pass

    def critique(self, department: str, original_task: str, agent_output: str) -> dict:
        """
        Evaluate agent output on 5 quality dimensions.

        Dimensions (0-100 each):
          SPECIFICITY (25%) — real numbers, names, timelines, not vague platitudes
          ACTIONABILITY (25%) — can the user act on this TODAY with concrete steps?
          DATA_GROUNDING (20%) — backed by real data or clearly-labeled estimates?
          DEPTH (15%) — scenarios, trade-offs, priorities, competitive context?
          HONESTY (15%) — acknowledges uncertainty, data gaps, limitations?

        Weighted confidence = (spec*0.25 + act*0.25 + dg*0.20 + dep*0.15 + hon*0.15) / 100
        Approved if confidence >= 0.65
        """
        truncated = agent_output[:3000] if len(agent_output) > 3000 else agent_output

        prompt = f"""You are The Skeptic — a strict, senior quality reviewer for SwarmOps.
You received output from the {department} agent for this task: "{original_task}"

OUTPUT TO REVIEW:
---
{truncated}
---

Score each dimension 0-100 (integers only):

1. SPECIFICITY (0-100):
   0="Increase your ad budget" | 50=has terms but no numbers | 100=specific $, %, timelines, page names
   PENALIZE: vague advice, missing numbers, generic best practices without specifics

2. ACTIONABILITY (0-100):
   0="Consider improving SEO" | 50=steps but vague | 100=clear steps with tools, executable TODAY
   PENALIZE: theoretical, no first action, missing tools/platforms

3. DATA_GROUNDING (0-100):
   0=fabricated metrics | 50=general knowledge, no confidence labels | 100=real data OR clearly-labeled estimates
   PENALIZE: fake numbers, overconfident claims, no benchmark references

4. DEPTH (0-100):
   0=one paragraph surface advice | 50=multiple obvious points | 100=scenarios, trade-offs, priorities, risks
   PENALIZE: shallow, no alternatives, no risk/priority analysis

5. HONESTY (0-100):
   0=everything presented as certain | 50=some caveats | 100=data gaps stated, estimates labeled, uncertainty acknowledged
   PENALIZE: ignoring missing data, overconfident without basis

Return ONLY valid JSON (no markdown):
{{"confidence":0.73,"approved":true,"breakdown":{{"specificity":75,"actionability":80,"data_grounding":65,"depth":70,"honesty":75}},"strengths":["strength 1"],"weaknesses":["weakness 1"],"suggestions":["fix 1"]}}"""

        try:
            result = call_model_sync(prompt=prompt, tier=1, max_tokens=600, temperature=0.2)
            text = result["content"].strip()

            # Strip markdown fences
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                if "```" in text:
                    text = text[:text.rfind("```")]
                text = text.strip()

            parsed = json.loads(text)

            # Compute weighted confidence from breakdown
            breakdown = parsed.get("breakdown", {})
            spec = float(breakdown.get("specificity", 60))
            act = float(breakdown.get("actionability", 60))
            dg = float(breakdown.get("data_grounding", 60))
            dep = float(breakdown.get("depth", 60))
            hon = float(breakdown.get("honesty", 60))
            weighted = (spec * 0.25 + act * 0.25 + dg * 0.20 + dep * 0.15 + hon * 0.15) / 100

            # Sanity-check against parsed confidence
            parsed_conf = float(parsed.get("confidence", weighted))
            confidence = weighted if abs(parsed_conf - weighted) > 0.15 else parsed_conf
            confidence = round(min(0.95, max(0.1, confidence)), 3)

            return {
                "confidence": confidence,
                "approved": confidence >= 0.65,
                "breakdown": {
                    "specificity": int(spec),
                    "actionability": int(act),
                    "data_grounding": int(dg),
                    "depth": int(dep),
                    "honesty": int(hon),
                },
                "strengths": parsed.get("strengths", []),
                "weaknesses": parsed.get("weaknesses", []),
                "suggestions": parsed.get("suggestions", []),
            }
        except Exception:
            return {
                "confidence": 0.6,
                "approved": False,
                "breakdown": {},
                "strengths": [],
                "weaknesses": ["Skeptic evaluation failed — could not parse critique"],
                "suggestions": [],
            }

    def review_and_improve(
        self,
        department: str,
        original_task: str,
        agent_output: str,
        agent_function,
    ) -> dict:
        """
        Full review cycle:
        1. Critique the output
        2. If confidence < 0.7, build a revision prompt and re-call the agent
        3. Critique the revised output
        4. Return the best version

        Max 1 revision (2 critique calls max).

        Args:
            department: Agent name (e.g. "seo")
            original_task: User's original message
            agent_output: Agent's first output
            agent_function: Callable that accepts a prompt string and returns a string

        Returns:
            {
                "output": str (final agent output),
                "revised": bool,
                "critique": { confidence, approved, strengths, weaknesses, suggestions }
            }
        """
        # First critique
        critique1 = self.critique(department, original_task, agent_output)

        if critique1["approved"]:
            return {
                "output": agent_output,
                "revised": False,
                "critique": critique1,
            }

        # Build revision prompt with specific feedback from breakdown
        breakdown = critique1.get("breakdown", {})
        weak_dims = []
        dim_labels = {
            "specificity": "specificity (add specific numbers, names, dollar amounts)",
            "actionability": "actionability (add concrete first steps the user can take today)",
            "data_grounding": "data grounding (label estimates with confidence levels, cite benchmarks)",
            "depth": "depth (add scenarios, trade-offs, priority rankings)",
            "honesty": "honesty (acknowledge data gaps, state what information is missing)",
        }
        for dim, label in dim_labels.items():
            if breakdown.get(dim, 100) < 60:
                weak_dims.append(label)

        weaknesses = "; ".join(critique1["weaknesses"]) if critique1["weaknesses"] else "quality issues detected"
        suggestions = "; ".join(critique1["suggestions"]) if critique1["suggestions"] else "be more specific and actionable"
        dim_feedback = f"Improve: {', '.join(weak_dims)}. " if weak_dims else ""

        revision_prompt = (
            f"Your previous response scored {critique1['confidence']:.0%} quality. "
            f"{dim_feedback}"
            f"Issues found: {weaknesses}. "
            f"How to fix: {suggestions}. "
            f"Rewrite to be more specific, data-driven, and actionable. "
            f"Original task: {original_task}"
        )

        best_output = agent_output
        best_critique = critique1
        revised = False

        # Up to 2 revision cycles
        for cycle in range(2):
            if best_critique["approved"]:
                break
            try:
                revised_output = agent_function(revision_prompt)
                if isinstance(revised_output, dict):
                    revised_output = revised_output.get("content", str(revised_output))
                if not revised_output or len(revised_output) < 20:
                    break
            except Exception:
                break

            new_critique = self.critique(department, original_task, revised_output)

            if new_critique["confidence"] >= best_critique["confidence"]:
                best_output = revised_output
                best_critique = new_critique
                revised = True

            if best_critique["approved"]:
                break

            # Build prompt for next cycle if needed
            if cycle == 0:
                revision_prompt = (
                    f"Still needs improvement (score: {best_critique['confidence']:.0%}). "
                    f"Be much more specific with REAL numbers, exact steps, and specific recommendations. "
                    f"Original task: {original_task}"
                )

        return {
            "output": best_output,
            "revised": revised,
            "revision_reason": f"Improved from {critique1['confidence']:.0%} to {best_critique['confidence']:.0%}" if revised else None,
            "critique": best_critique,
        }


# Test
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TESTING SKEPTIC AGENT")
    print("=" * 60)

    skeptic = SkepticAgent()

    # Test critique on a sample output
    sample_output = """Here are some SEO tips:
1. Use keywords in your content
2. Build backlinks
3. Optimize meta tags
4. Create quality content
5. Improve site speed"""

    result = skeptic.critique("seo", "How do I improve my website SEO?", sample_output)
    print(f"\nConfidence: {result['confidence']}")
    print(f"Approved: {result['approved']}")
    print(f"Strengths: {result['strengths']}")
    print(f"Weaknesses: {result['weaknesses']}")
    print(f"Suggestions: {result['suggestions']}")
    print("=" * 60)
