"""
Debate protocol. When specialists disagree significantly, they get a
second round to challenge each other. Increases output quality on
strategic questions.

Triggered when:
- 2+ specialists active AND
- max(confidence) - min(confidence) > 0.30 OR
- recommendations conflict (top recs point in different directions)
"""
import logging
from typing import List
from .schemas import AgentOutput

logger = logging.getLogger(__name__)


def should_debate(outputs: List[AgentOutput]) -> bool:
    """Decide whether the specialists should debate."""
    if len(outputs) < 2:
        return False

    confidences = [o.confidence for o in outputs]
    confidence_spread = max(confidences) - min(confidences)

    if confidence_spread > 0.30:
        return True

    # Check for conflicting top recommendations
    top_recs = []
    for o in outputs:
        if o.recommendations:
            top_recs.append((o.agent_id, o.recommendations[0].action.lower()))

    if len(top_recs) >= 2:
        # Simple heuristic: do top recs share <30% words?
        words_per_agent = {a: set(rec.split()) for a, rec in top_recs}
        agents = list(words_per_agent.keys())
        for i in range(len(agents)):
            for j in range(i + 1, len(agents)):
                a, b = words_per_agent[agents[i]], words_per_agent[agents[j]]
                overlap = len(a & b) / max(len(a), 1)
                if overlap < 0.3:
                    return True

    return False


def build_debate_prompt(my_output: AgentOutput, other_outputs: List[AgentOutput]) -> str:
    """Build a debate prompt for an agent to challenge others."""
    my_pos = (
        f"YOUR PREVIOUS POSITION ({my_output.agent_id}):\n"
        f"Conclusion: {my_output.conclusion}\n"
        f"Confidence: {int(my_output.confidence * 100)}%\n"
        f"Top recommendation: "
        f"{my_output.recommendations[0].action if my_output.recommendations else 'none'}"
    )

    others_text = "OTHER SPECIALISTS' POSITIONS:\n"
    for o in other_outputs:
        if o.agent_id == my_output.agent_id:
            continue
        top_rec = o.recommendations[0].action if o.recommendations else "none"
        assumptions = "; ".join(o.assumptions[:2]) if o.assumptions else "none stated"
        others_text += (
            f"\n--- {o.agent_id.upper()} ({int(o.confidence * 100)}% confidence) ---\n"
            f"Conclusion: {o.conclusion}\n"
            f"Top rec: {top_rec}\n"
            f"Their assumptions: {assumptions}\n"
        )

    return f"""{my_pos}

{others_text}

The other specialists disagree with you OR proposed conflicting actions.

Now you must respond:
1. Where do they have a point? What evidence supports their position?
2. Where do you stand firm? What's the strongest counter to their position?
3. Has your confidence shifted? (Up if they revealed evidence you missed,
   down if you realize your evidence was thinner than theirs.)

Return your updated position as the standard JSON schema.
Keep your conclusion if you're still right. Revise it if they convinced you.
Don't capitulate just to agree — your job is to find the truth, not consensus."""
