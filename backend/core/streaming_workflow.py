"""
Streaming workflow engine. Same logic as run_workflow but emits SSE
events at every step so the frontend can show the swarm working.
"""
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from .agent_runner import run_agent_structured
from .schemas import AgentOutput, SwarmDecision
from .confidence import compute_confidence
from .events import EventBus
from .debate import should_debate, build_debate_prompt
from .workflow_engine import WORKFLOWS, _build_synthesis_input
from .memory import get_memory
from .context import get_context

logger = logging.getLogger(__name__)


def run_workflow_streaming(
    workflow_name: str,
    message: str,
    conversation_id: str,
    bus: EventBus,
) -> dict:
    """
    Run a workflow with live event emission.
    Returns final result; bus emits intermediate events.
    """
    if workflow_name not in WORKFLOWS:
        bus.emit("error", {"message": f"Unknown workflow: {workflow_name}"})
        return {"error": f"Unknown workflow: {workflow_name}"}

    config = WORKFLOWS[workflow_name]
    agents = config["agents"]

    ctx = get_context(conversation_id)
    memory = get_memory(conversation_id)
    memory.store(message, role="user", mem_type="conversation")

    bus.emit("workflow.started", {
        "workflow": workflow_name,
        "agents": agents,
        "message": message[:200],
    })

    start = time.time()

    # ============================================
    # PHASE 1: Specialists respond in parallel
    # ============================================
    bus.emit("phase.started", {"phase": "specialist_round_1", "agents": agents})

    specialist_outputs: List[AgentOutput] = []

    def run_one_agent(agent_id: str) -> AgentOutput:
        bus.emit("agent.started", {"agent_id": agent_id}, agent_id=agent_id)
        try:
            output = run_agent_structured(agent_id, message, conversation_id)
            bus.emit("agent.responded", {
                "agent_id": agent_id,
                "conclusion": output.conclusion,
                "confidence": output.confidence,
                "evidence_count": len(output.evidence),
                "recommendations_count": len(output.recommendations),
                "tier_used": output.tier_used,
            }, agent_id=agent_id)
            return output
        except Exception as e:
            logger.error(f"Agent {agent_id} failed: {e}")
            bus.emit("agent.failed", {"agent_id": agent_id, "error": str(e)}, agent_id=agent_id)
            raise

    with ThreadPoolExecutor(max_workers=min(len(agents), 5)) as executor:
        futures = {executor.submit(run_one_agent, a): a for a in agents}
        for future in as_completed(futures):
            try:
                specialist_outputs.append(future.result())
            except Exception:
                continue  # agent.failed already emitted

    if not specialist_outputs:
        bus.emit("error", {"message": "All agents failed"})
        return {"error": "All agents failed"}

    # Recalc confidence with cross-agent agreement
    for output in specialist_outputs:
        others = [o for o in specialist_outputs if o.agent_id != output.agent_id]
        new_confidence = compute_confidence(output, others)
        if abs(new_confidence - output.confidence) > 0.05:
            bus.emit("confidence.shifted", {
                "agent_id": output.agent_id,
                "from": output.confidence,
                "to": new_confidence,
                "reason": "cross_agent_agreement",
            }, agent_id=output.agent_id)
        output.confidence = new_confidence

    bus.emit("phase.completed", {
        "phase": "specialist_round_1",
        "specialists": [
            {"agent_id": o.agent_id, "confidence": o.confidence}
            for o in specialist_outputs
        ],
    })

    # ============================================
    # PHASE 2: Debate (only if specialists disagree)
    # ============================================
    debate_happened = False

    if should_debate(specialist_outputs):
        spread = round(
            max(o.confidence for o in specialist_outputs) -
            min(o.confidence for o in specialist_outputs),
            2,
        )
        bus.emit("phase.started", {
            "phase": "debate",
            "reason": "specialists_disagree",
            "spread": spread,
        })
        debate_happened = True

        updated_outputs: List[AgentOutput] = []

        def run_debate_round(my_output: AgentOutput) -> AgentOutput:
            bus.emit("agent.challenged", {
                "agent_id": my_output.agent_id,
                "original_confidence": my_output.confidence,
            }, agent_id=my_output.agent_id)

            debate_prompt = build_debate_prompt(my_output, specialist_outputs)
            updated = run_agent_structured(
                my_output.agent_id, debate_prompt, conversation_id,
                other_agent_outputs=specialist_outputs,
            )

            if abs(updated.confidence - my_output.confidence) > 0.05:
                bus.emit("confidence.shifted", {
                    "agent_id": my_output.agent_id,
                    "from": my_output.confidence,
                    "to": updated.confidence,
                    "reason": "debate_round",
                }, agent_id=my_output.agent_id)

            return updated

        with ThreadPoolExecutor(max_workers=min(len(specialist_outputs), 5)) as executor:
            futures = {executor.submit(run_debate_round, o): o.agent_id for o in specialist_outputs}
            for future in as_completed(futures):
                try:
                    updated_outputs.append(future.result())
                except Exception as e:
                    logger.error(f"Debate round failed: {e}")

        if updated_outputs:
            specialist_outputs = updated_outputs

        bus.emit("phase.completed", {"phase": "debate"})

    # ============================================
    # PHASE 3: Nexus synthesis (always Tier 3)
    # ============================================
    bus.emit("phase.started", {"phase": "synthesis", "agent_id": "nexus"})
    bus.emit("agent.started", {"agent_id": "nexus", "role": "synthesizer"}, agent_id="nexus")

    synthesis_input = _build_synthesis_input(message, specialist_outputs)
    nexus_output = run_agent_structured(
        "nexus", synthesis_input, conversation_id,
        specialist_outputs, is_synthesis=True,
    )

    bus.emit("agent.responded", {
        "agent_id": "nexus",
        "conclusion": nexus_output.conclusion,
        "confidence": nexus_output.confidence,
        "tier_used": nexus_output.tier_used,
    }, agent_id="nexus")

    # ============================================
    # PHASE 4: Build SwarmDecision
    # ============================================
    avg_confidence = sum(o.confidence for o in specialist_outputs) / len(specialist_outputs)
    agreed = [o.agent_id for o in specialist_outputs if o.confidence > 0.5]
    dissented = [o.agent_id for o in specialist_outputs if o.confidence <= 0.5]

    swarm_decision = SwarmDecision(
        decision=nexus_output.conclusion,
        rationale=nexus_output.summary,
        agents_consulted=[o.agent_id for o in specialist_outputs],
        agents_agreed=agreed,
        agents_dissented=dissented,
        confidence=round((nexus_output.confidence + avg_confidence) / 2, 2),
        next_action=nexus_output.recommendations[0] if nexus_output.recommendations else None,
        dissent_notes=f"{len(dissented)} agents dissented" if dissented else None,
    )

    memory.store(
        nexus_output.conclusion[:500],
        role="assistant",
        mem_type="workflow",
        importance=0.7,
    )

    elapsed_ms = int((time.time() - start) * 1000)

    bus.emit("decision.reached", {
        "decision": swarm_decision.decision,
        "confidence": swarm_decision.confidence,
        "agents_consulted": swarm_decision.agents_consulted,
        "agents_agreed": swarm_decision.agents_agreed,
        "agents_dissented": swarm_decision.agents_dissented,
        "debate_happened": debate_happened,
        "latency_ms": elapsed_ms,
        "next_action": swarm_decision.next_action.dict() if swarm_decision.next_action else None,
    })

    bus.emit("stream.end", {})

    return {
        "workflow": workflow_name,
        "response": nexus_output.summary or nexus_output.conclusion,
        "agents_used": [o.agent_id for o in specialist_outputs],
        "latency_ms": elapsed_ms,
        "confidence": swarm_decision.confidence,
        "debate_happened": debate_happened,
        "structured": {
            "decision": swarm_decision.dict(),
            "specialists": [o.dict() for o in specialist_outputs],
            "nexus": nexus_output.dict(),
        },
    }


def run_single_agent_streaming(
    agent_id: str,
    message: str,
    conversation_id: str,
    bus: EventBus,
) -> dict:
    """Single-agent streaming (slash commands)."""
    memory = get_memory(conversation_id)
    memory.store(message, role="user", mem_type="conversation")

    bus.emit("workflow.started", {"workflow": "single_agent", "agents": [agent_id]})
    bus.emit("agent.started", {"agent_id": agent_id}, agent_id=agent_id)

    start = time.time()
    output = run_agent_structured(agent_id, message, conversation_id)
    elapsed_ms = int((time.time() - start) * 1000)

    bus.emit("agent.responded", {
        "agent_id": agent_id,
        "conclusion": output.conclusion,
        "confidence": output.confidence,
        "tier_used": output.tier_used,
    }, agent_id=agent_id)

    memory.store(output.conclusion[:500], role="assistant", mem_type="conversation", importance=0.5)

    bus.emit("decision.reached", {
        "decision": output.conclusion,
        "confidence": output.confidence,
        "agents_consulted": [agent_id],
        "agents_agreed": [agent_id] if output.confidence > 0.5 else [],
        "agents_dissented": [],
        "debate_happened": False,
        "latency_ms": elapsed_ms,
        "next_action": output.recommendations[0].dict() if output.recommendations else None,
    })

    bus.emit("stream.end", {})

    return {
        "agent": agent_id,
        "response": output.summary or output.conclusion,
        "agents_used": [agent_id],
        "latency_ms": elapsed_ms,
        "confidence": output.confidence,
        "structured": {"specialist": output.dict()},
    }
