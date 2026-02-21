"""
Skeptic Agent - MarketingOS 2.0 Quality Control
Reviews every agent's output before it reaches the user.
Catches generic, low-quality, or incomplete responses and forces a revision.
Uses tier 1 (Groq) for fast evaluation.
"""

import json
from model_router import call_model_sync


class SkepticAgent:
    """
    The Skeptic — quality control layer for MarketingOS.
    Critiques agent outputs and triggers revisions when needed.
    """

    def __init__(self):
        pass

    def critique(self, department: str, original_task: str, agent_output: str) -> dict:
        """
        Evaluate agent output quality.

        Args:
            department: Which agent produced the output (e.g. "seo", "content")
            original_task: The user's original message/request
            agent_output: The agent's raw output text

        Returns:
            {
                "confidence": 0.0-1.0,
                "approved": bool (true if confidence >= 0.7),
                "strengths": ["..."],
                "weaknesses": ["..."],
                "suggestions": ["..."]
            }
        """
        # Truncate very long outputs to keep the critique prompt manageable
        truncated = agent_output[:3000] if len(agent_output) > 3000 else agent_output

        prompt = f"""You are The Skeptic, a strict quality control reviewer for MarketingOS.
You received output from the {department} agent for this task: "{original_task}"

OUTPUT TO REVIEW:
---
{truncated}
---

Score each dimension 0.0-1.0, then average for final confidence:
1. RELEVANCE — Does it directly address what the user asked? (0.0=off-topic, 1.0=perfect match)
2. SPECIFICITY — Does it include real data, numbers, names, or actionable details? (0.0=generic platitudes, 1.0=highly specific)
3. COMPLETENESS — Are there obvious missing sections or gaps? (0.0=barely started, 1.0=thorough)
4. ACTIONABILITY — Could someone execute this immediately? (0.0=vague advice, 1.0=step-by-step ready)
5. ACCURACY — Are claims realistic and well-reasoned? (0.0=made-up numbers, 1.0=well-supported)

SCORING RULES:
- Generic advice with no specifics (e.g. "use keywords", "create quality content") = 0.4-0.55
- Decent structure but uses placeholder data or lacks depth = 0.6-0.72
- Good analysis with real insights and minor gaps = 0.73-0.85
- Exceptional output with specific data, clear strategy, and complete coverage = 0.86-0.95
- NEVER score above 0.95 — nothing is perfect

Calculate: confidence = average of your 5 dimension scores. Do NOT default to 0.8.

Respond ONLY as valid JSON (no markdown, no code fences):
{{"confidence":0.73,"approved":true,"strengths":["specific strength 1","specific strength 2"],"weaknesses":["specific weakness 1"],"suggestions":["specific improvement 1"]}}"""

        try:
            result = call_model_sync(prompt=prompt, tier=1, max_tokens=500, temperature=0.3)
            text = result["content"].strip()

            # Strip markdown fences if model wraps in ```json ... ```
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                if text.endswith("```"):
                    text = text[:-3]
                text = text.strip()

            parsed = json.loads(text)

            # Normalise fields
            confidence = float(parsed.get("confidence", 0.6))
            return {
                "confidence": confidence,
                "approved": confidence >= 0.7,
                "strengths": parsed.get("strengths", []),
                "weaknesses": parsed.get("weaknesses", []),
                "suggestions": parsed.get("suggestions", []),
            }
        except Exception:
            # If the Skeptic itself fails, default to cautious pass
            return {
                "confidence": 0.6,
                "approved": False,
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

        # Build revision prompt
        weaknesses = "; ".join(critique1["weaknesses"]) if critique1["weaknesses"] else "quality issues detected"
        suggestions = "; ".join(critique1["suggestions"]) if critique1["suggestions"] else "be more specific and actionable"

        revision_prompt = (
            f"Revise your response. Issues: {weaknesses}. "
            f"Suggestions: {suggestions}. "
            f"Original task: {original_task}"
        )

        try:
            revised_output = agent_function(revision_prompt)
            # Handle case where agent_function returns dict (from call_model_sync)
            if isinstance(revised_output, dict):
                revised_output = revised_output.get("content", str(revised_output))
        except Exception:
            # Revision failed — return original with first critique
            return {
                "output": agent_output,
                "revised": False,
                "critique": critique1,
            }

        # Second critique on revised output
        critique2 = self.critique(department, original_task, revised_output)

        # Return whichever version is better
        if critique2["confidence"] >= critique1["confidence"]:
            return {
                "output": revised_output,
                "revised": True,
                "critique": critique2,
            }
        else:
            return {
                "output": agent_output,
                "revised": False,
                "critique": critique1,
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
