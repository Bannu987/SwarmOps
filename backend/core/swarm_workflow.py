import time
import logging
import json
import uuid
import datetime
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .model_router import call_model
from .prompts import get_prompt
from .events import EventBus
from .memory import get_memory
from .context import get_context
from .supabase_client import get_admin_client
from .signals.registry import CANONICAL_REGISTRY
from .signals.scoring import calculate_priority_score, get_priority_bucket, map_signal_to_registry_key, recalculate_project_health
from .agent_runner import _safe_parse_json

logger = logging.getLogger(__name__)


def run_swarm_signal_workflow(
    clicked_signal: dict,
    message: str,
    conversation_id: str,
    bus: Optional[EventBus] = None
) -> dict:
    """
    LangGraph-inspired supervisor workflow:
    clicked_signal
    → context_builder
    → specialist_router
    → specialist_review_nodes (parallel execution with JSON contracts & repair)
    → boardroom_decision (nexus synthesis with JSON contract & repair)
    → action_plan_generation (write to Supabase action_plans/action_items)
    → save_agent_run (log audit trail in agent_runs)
    → return result / SSE stream
    """
    ctx = get_context(conversation_id)
    memory = get_memory(conversation_id)
    memory.store(message, role="user", mem_type="conversation")

    start_time = time.time()

    # ============================================
    # STEP 1: context_builder
    # ============================================
    if bus:
        bus.emit("workflow.started", {"workflow": "signal_analysis", "agents": []})
        bus.emit("phase.started", {"phase": "context_builder"})

    signal_id = clicked_signal.get("signal_id")
    title = clicked_signal.get("title", "")
    description = clicked_signal.get("description", "")
    category = clicked_signal.get("category", "")
    detector = clicked_signal.get("detector", "seo")
    severity = clicked_signal.get("severity", "medium")
    url = clicked_signal.get("url", "")
    evidence = clicked_signal.get("evidence", [])
    project_id = clicked_signal.get("project_id") or ctx.project_id
    user_id = getattr(ctx, "user_id", None)

    # Lookup registry key
    reg_key = clicked_signal.get("signal_type") or map_signal_to_registry_key(title, category)
    registry_entry = CANONICAL_REGISTRY.get(reg_key) if reg_key else None

    # Construct compiled context details
    signal_context = {
        "signal_id": signal_id,
        "title": title,
        "description": description,
        "category": category,
        "detector": detector,
        "severity": severity,
        "url": url,
        "evidence": str(evidence),
        "project_id": project_id,
        "workspace_id": project_id,
        "what_issue_means": registry_entry.what_issue_means if registry_entry else "Standard technical opportunity detected.",
        "why_it_matters": registry_entry.why_it_matters if registry_entry else "Resolving this improves crawler access and site quality.",
        "business_impact": registry_entry.business_impact if registry_entry else "Aesthetic or structure improvements.",
        "seo_aeo_impact": registry_entry.seo_aeo_impact if registry_entry else "Crawler readability improvements.",
        "default_impact_score": registry_entry.default_impact_score if registry_entry else 5.0,
        "default_effort_score": registry_entry.default_effort_score if registry_entry else 3.0,
        "default_urgency_score": registry_entry.default_urgency_score if registry_entry else 5.0,
        "default_confidence_score": registry_entry.default_confidence_score if registry_entry else 9.0,
        "business_relevance_score": registry_entry.business_relevance_score if registry_entry else 5.0,
        "exact_fix": registry_entry.exact_fix if registry_entry else "Implement configuration fix.",
        "implementation_example": registry_entry.implementation_example if registry_entry else "",
        "verification_method": registry_entry.verification_method if registry_entry else "Re-scan the website.",
        "resolved_when": registry_entry.resolved_when if registry_entry else "No longer flagged by scanner.",
        "evidence_safe_wording": registry_entry.evidence_safe_wording if registry_entry else "Address site configuration.",
        "avoid_claims": registry_entry.avoid_claims if registry_entry else [],
    }

    if bus:
        bus.emit("phase.completed", {"phase": "context_builder"})

    # ============================================
    # STEP 2: specialist_router
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "specialist_router"})

    # Determine specialists based on signal category/title
    specialist_ids = []
    cat_lower = category.lower() if category else ""
    title_lower = title.lower()

    if cat_lower == "seo" or any(k in title_lower for k in ["robots.txt", "sitemap", "canonical", "title", "meta description"]):
        specialist_ids = ["seo", "aeo"]
    elif cat_lower == "aeo" or any(k in title_lower for k in ["json-ld", "schema", "person", "organization"]):
        specialist_ids = ["aeo", "seo", "cro"]
    elif cat_lower == "analytics" or any(k in title_lower for k in ["analytics", "ga4", "gtm"]):
        specialist_ids = ["analytics", "cro"]
    elif cat_lower == "cro" or any(k in title_lower for k in ["cta", "lead capture", "form", "trust"]):
        specialist_ids = ["cro", "analytics"]
    else:
        specialist_ids = ["seo", "cro"]

    # Deduplicate and limit
    specialist_ids = list(dict.fromkeys(specialist_ids))

    if bus:
        bus.emit("phase.completed", {"phase": "specialist_router", "selected_agents": specialist_ids})

    # ============================================
    # STEP 3: specialist_review_nodes (Parallel)
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "specialist_review", "agents": specialist_ids})

    specialist_reviews = []

    def run_one_specialist(agent_id: str) -> dict:
        if bus:
            bus.emit("agent.started", {"agent_id": agent_id}, agent_id=agent_id)
        
        system_prompt = get_prompt(agent_id)
        
        # Injects strict constraints: no rate limit/fallback talk, accurate SEO/Schema assertions
        instructions = f"""
You are the {agent_id.upper()} Specialist reviewing a specific website signal in the boardroom.
Your final output MUST be a JSON object ONLY matching this schema:
{{
  "agent": "{agent_id}",
  "assessment": "Detailed assessment of this signal",
  "impact_view": "Your perspective on the SEO, AEO, tracking, or conversion impact of this signal",
  "evidence_used": ["List of evidence metrics/strings evaluated"],
  "recommended_action": "Specific remediation fix",
  "risk_or_caution": "Detailed considerations or warnings",
  "confidence": 1.0
}}

STRICT WORDING CONSTRAINTS:
1. Do NOT show or mention upstream rate limits, fallback providers, offline modes, or system failures.
2. robots.txt controls crawler access, not indexing.
3. A clear meta description may improve snippet quality and click appeal when search engines choose to display it (never claim CTR improves by 30%).
4. Structured data gives search engines explicit clues about the meaning of a page and can support machine understanding (never claim schema is critical for citations).

SIGNAL DETAILS:
- Title: {signal_context['title']}
- Description: {signal_context['description']}
- URL: {signal_context['url']}
- Evidence: {signal_context['evidence']}

Respond ONLY with the JSON object. Do not include markdown code fences or other prose.
"""

        # Call model
        raw = call_model(
            prompt=instructions,
            agent_id=agent_id,
            system=system_prompt + "\n\nALWAYS return JSON only. No markdown fences.",
            temperature=0.3,
            json_mode=True
        )

        parsed = _safe_parse_json(raw)
        
        # If parse failed, try once to repair
        if not parsed:
            repair_prompt = f"""
The following text could not be parsed as valid JSON. Please rewrite it so that it is valid JSON matching this schema:
{{
  "agent": "{agent_id}",
  "assessment": "Assessment string",
  "impact_view": "Impact view string",
  "evidence_used": ["evidence list"],
  "recommended_action": "Recommended action string",
  "risk_or_caution": "Risk string",
  "confidence": 0.9
}}

TEXT TO REPAIR:
{raw}
"""
            raw_repaired = call_model(
                prompt=repair_prompt,
                agent_id=agent_id,
                system="Return ONLY valid JSON.",
                temperature=0.1,
                json_mode=True
            )
            parsed = _safe_parse_json(raw_repaired)

        if not parsed:
            # Fallback to registry default
            parsed = {
                "agent": agent_id,
                "assessment": f"Evaluated the {signal_context['title']} alert.",
                "impact_view": signal_context["why_it_matters"],
                "evidence_used": [signal_context["title"]],
                "recommended_action": signal_context["exact_fix"],
                "risk_or_caution": signal_context["evidence_safe_wording"],
                "confidence": 0.8
            }

        if bus:
            bus.emit("agent.responded", {
                "agent_id": agent_id,
                "conclusion": parsed.get("assessment", "")[:200],
                "confidence": parsed.get("confidence", 0.9)
            }, agent_id=agent_id)

        return parsed

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=len(specialist_ids)) as executor:
        futures = {executor.submit(run_one_specialist, a): a for a in specialist_ids}
        for future in as_completed(futures):
            try:
                specialist_reviews.append(future.result())
            except Exception as e:
                logger.error(f"Specialist node failed: {e}")

    if bus:
        bus.emit("phase.completed", {"phase": "specialist_review"})

    # ============================================
    # STEP 4: boardroom_decision
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "boardroom_decision", "agent_id": "nexus"})
        bus.emit("agent.started", {"agent_id": "nexus", "role": "synthesizer"}, agent_id="nexus")

    specialist_reviews_str = json.dumps(specialist_reviews, indent=2)

    boardroom_prompt = f"""
You are Nexus, the Chief Boardroom Decision Agent. Synthesize the boardroom specialist reviews and reach a final consensus on the clicked signal.

STRICT WORDING CONSTRAINTS:
1. Do NOT mention upstream rate limits, fallback providers, offline modes, or system failures.
2. robots.txt controls crawler access, not indexing.
3. A clear meta description may improve snippet quality and click appeal when search engines choose to display it (never claim CTR improves by 30%).
4. Structured data gives search engines explicit clues about the meaning of a page and can support machine understanding (never claim schema is critical for citations).

SIGNAL CONTEXT:
- Title: {signal_context['title']}
- Description: {signal_context['description']}
- URL: {signal_context['url']}
- Default Impact: {signal_context['default_impact_score']}
- Default Effort: {signal_context['default_effort_score']}
- Default Urgency: {signal_context['default_urgency_score']}
- Default Confidence: {signal_context['default_confidence_score']}
- Business Relevance: {signal_context['business_relevance_score']}

SPECIALIST REVIEWS:
{specialist_reviews_str}

Your output MUST be a JSON object matching this schema:
{{
  "executive_summary": "1-2 sentence top-line synthesis of the findings",
  "final_priority_bucket": "Critical | High | Medium | Low",
  "final_impact": 1.0_to_10.0,
  "final_effort": 1.0_to_10.0,
  "final_urgency": 1.0_to_10.0,
  "final_confidence": 1.0_to_10.0,
  "final_decision": "Consensus reached in the boardroom regarding what we must do.",
  "action_title": "Action Plan Title",
  "action_description": "Clear remediation plan description",
  "checklist": ["Remediation action item 1", "Remediation action item 2", "Verification check step"],
  "verification_method": "Visit /robots.txt or inspect HTML head or check headers...",
  "resolved_when": "The specific state required to resolve this alert"
}}

Respond ONLY with the JSON object. Do not include markdown code fences or other prose.
"""

    raw_boardroom = call_model(
        prompt=boardroom_prompt,
        agent_id="nexus",
        system=get_prompt("nexus") + "\n\nALWAYS return JSON only.",
        temperature=0.3,
        json_mode=True
    )

    boardroom_json = _safe_parse_json(raw_boardroom)

    # Repair once
    if not boardroom_json:
        repair_boardroom_prompt = f"The previous output was not valid JSON. Fix it and return valid JSON matching the schema:\n\n{raw_boardroom}"
        raw_repaired_br = call_model(
            prompt=repair_boardroom_prompt,
            agent_id="nexus",
            system="Return ONLY valid JSON.",
            temperature=0.1,
            json_mode=True
        )
        boardroom_json = _safe_parse_json(raw_repaired_br)

    if not boardroom_json:
        # Fallback boardroom JSON
        boardroom_json = {
            "executive_summary": f"Consensus reached to resolve the '{signal_context['title']}' alert.",
            "final_priority_bucket": get_priority_bucket(
                calculate_priority_score(
                    signal_context["default_impact_score"],
                    signal_context["default_urgency_score"],
                    signal_context["default_confidence_score"],
                    signal_context["business_relevance_score"],
                    signal_context["default_effort_score"]
                )
            ),
            "final_impact": signal_context["default_impact_score"],
            "final_effort": signal_context["default_effort_score"],
            "final_urgency": signal_context["default_urgency_score"],
            "final_confidence": signal_context["default_confidence_score"],
            "final_decision": f"Address the '{signal_context['title']}' issue immediately following standard procedures.",
            "action_title": f"Resolve: {signal_context['title']}",
            "action_description": signal_context["description"],
            "checklist": [signal_context["exact_fix"], f"Verify: {signal_context['verification_method']}"],
            "verification_method": signal_context["verification_method"],
            "resolved_when": signal_context["resolved_when"]
        }

    # Calculate final priority score
    priority_score = calculate_priority_score(
        boardroom_json.get("final_impact", 5.0),
        boardroom_json.get("final_urgency", 5.0),
        boardroom_json.get("final_confidence", 9.0),
        signal_context["business_relevance_score"],
        boardroom_json.get("final_effort", 3.0)
    )
    priority_bucket = get_priority_bucket(priority_score)
    boardroom_json["priority_score"] = priority_score
    boardroom_json["final_priority_bucket"] = priority_bucket

    if bus:
        bus.emit("agent.responded", {
            "agent_id": "nexus",
            "conclusion": boardroom_json.get("executive_summary", "")[:200],
            "confidence": boardroom_json.get("final_confidence", 9.0) / 10.0
        }, agent_id="nexus")
        bus.emit("phase.completed", {"phase": "boardroom_decision"})

    # ============================================
    # STEP 5: action_plan_generation
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "action_plan_generation"})

    action_plan_id = None
    admin = get_admin_client()
    if admin and project_id and user_id:
        try:
            # Map boardroom effort/impact to text limits (low, medium, high)
            def map_to_text(val: float) -> str:
                if val >= 7.0:
                    return "high"
                elif val >= 4.0:
                    return "medium"
                else:
                    return "low"

            est_effort = map_to_text(boardroom_json.get("final_effort", 3.0))
            exp_impact = map_to_text(boardroom_json.get("final_impact", 5.0))

            plan_insert = admin.table("action_plans").insert({
                "user_id": user_id,
                "project_id": project_id,
                "source_type": "swarm_decision",
                "source_id": signal_id,
                "title": boardroom_json.get("action_title", f"Resolve: {title}"),
                "objective": boardroom_json.get("action_description", description),
                "plan_type": "seo_growth" if category.lower() == "seo" else "general_strategy",
                "priority": priority_bucket.lower(),
                "status": "pending",
                "estimated_effort": est_effort,
                "expected_impact": exp_impact,
                "confidence": boardroom_json.get("final_confidence", 9.0) / 10.0,
                "tasks": boardroom_json.get("checklist", []),
                "kpis": [{"kpi": "Signal Cleared", "target": "Resolved"}],
            }).execute()

            if plan_insert.data:
                action_plan_id = plan_insert.data[0]["id"]
                # Insert checklist items into action_items
                checklist_items = boardroom_json.get("checklist", [])
                for idx, item in enumerate(checklist_items):
                    try:
                        admin.table("action_items").insert({
                            "plan_id": action_plan_id,
                            "title": item,
                            "status": "pending",
                            "assigned_to": "nexus" if idx == 0 else "user"
                        }).execute()
                    except Exception as item_err:
                        logger.debug(f"action_items insert failed (table might be missing): {item_err}")
        except Exception as plan_err:
            logger.warning(f"Could not save action plan to Supabase (migration might be pending): {plan_err}")

    if bus:
        bus.emit("phase.completed", {"phase": "action_plan_generation", "action_plan_id": action_plan_id})

    # ============================================
    # STEP 6: save_agent_run
    # ============================================
    if bus:
        bus.emit("phase.started", {"phase": "save_agent_run"})

    if admin and project_id and user_id:
        try:
            admin.table("agent_runs").insert({
                "user_id": user_id,
                "project_id": project_id,
                "signal_id": signal_id,
                "agent_id": "nexus",
                "workflow_name": "signal_analysis",
                "inputs": clicked_signal,
                "outputs": boardroom_json,
                "status": "completed",
                "latency_ms": int((time.time() - start_time) * 1000)
            }).execute()
        except Exception as run_err:
            logger.warning(f"Could not save agent run to Supabase: {run_err}")

    if bus:
        bus.emit("phase.completed", {"phase": "save_agent_run"})

    # ============================================
    # STEP 7: Format Response Markdown
    # ============================================
    # Prepare specialist reviews text
    reviews_md = ""
    for r in specialist_reviews:
        agent_name = "SEO Specialist" if r.get("agent") == "seo" else \
                     "AEO/GEO Specialist" if r.get("agent") == "aeo" else \
                     "Growth Strategist" if r.get("agent") == "cro" else \
                     "Analytics Specialist" if r.get("agent") == "analytics" else \
                     "Content Specialist" if r.get("agent") == "content" else \
                     r.get("agent", "").upper()
        reviews_md += f"\n- **{agent_name}**: {r.get('assessment', '')} "
        if r.get("recommended_action"):
            reviews_md += f"Recommendation: *{r.get('recommended_action')}* "
        if r.get("risk_or_caution"):
            reviews_md += f"(Note: {r.get('risk_or_caution')})"

    # Handle robots.txt default implementation block requirement
    impl_example = boardroom_json.get("implementation_example", signal_context.get("implementation_example", ""))
    if "robots.txt" in title.lower() or "robots.txt" in description.lower():
        impl_example = """```
User-agent: *
Allow: /

Sitemap: https://shravanpayyavula.me/sitemap.xml
```"""
    elif impl_example and not impl_example.startswith("```"):
        impl_example = f"```\n{impl_example}\n```"

    checklist_md = "\n".join(f"- [ ] {item}" for item in boardroom_json.get("checklist", []))

    final_markdown = f"""# SwarmOps Boardroom Analysis: {title}

### Signal Summary
{boardroom_json.get("executive_summary", "")}

### Evidence Found
- **URL**: {url or "Homepage"}
- **Detector**: {detector}
- **Telemetry Indicators**: {evidence or "Missing tag detected in page DOM."}

### What This Means
{signal_context['what_issue_means']}

### Why It Matters
{signal_context['why_it_matters']}

### Priority
- **Score**: {priority_score} / 10.0
- **Bucket**: **{priority_bucket}**
- **Metrics**: Impact: {boardroom_json.get("final_impact", 5.0)}/10 | Effort: {boardroom_json.get("final_effort", 3.0)}/10 | Urgency: {boardroom_json.get("final_urgency", 5.0)}/10 | Confidence: {boardroom_json.get("final_confidence", 9.0)}/10

### Specialist Review
{reviews_md}

### Recommended Fix
{boardroom_json.get("action_description", signal_context.get("exact_fix"))}

### Implementation Example
{impl_example}

### Verification Steps
{boardroom_json.get("verification_method", signal_context.get("verification_method"))}

### Final Boardroom Decision
{boardroom_json.get("final_decision", "")}

### Action Checklist
{checklist_md}
"""

    total_latency = int((time.time() - start_time) * 1000)

    decision_val = final_markdown
    rationale_val = boardroom_json.get("executive_summary", "")
    logger.info(
        f"[DIAGNOSTIC] Emitting decision.reached: "
        f"event_type=decision.reached, "
        f"workflow=signal_analysis, "
        f"decision_exists={bool(decision_val)}, "
        f"decision_len={len(decision_val) if decision_val else 0}, "
        f"rationale_exists={bool(rationale_val)}, "
        f"rationale_len={len(rationale_val) if rationale_val else 0}, "
        f"payload_keys={['decision', 'rationale', 'confidence', 'agents_consulted', 'agents_agreed', 'agents_dissented', 'debate_happened', 'latency_ms', 'workflow', 'next_action']}"
    )

    # If streaming, output decision and close out bus
    if bus:
        bus.emit("decision.reached", {
            "rationale": boardroom_json.get("executive_summary", ""),
            "confidence": boardroom_json.get("final_confidence", 9.0) / 10.0,
            "agents_consulted": specialist_ids,
            "agents_agreed": specialist_ids,
            "agents_dissented": [],
            "debate_happened": False,
            "latency_ms": total_latency,
            "workflow": "signal_analysis",
            "next_action": {
                "action": boardroom_json.get("action_title", f"Resolve: {title}"),
                "rationale": boardroom_json.get("action_description", description),
                "expected_impact": map_to_text(boardroom_json.get("final_impact", 5.0)),
                "effort": map_to_text(boardroom_json.get("final_effort", 3.0)),
                "timeframe": "this week"
            }
        })
        bus.emit("final.answer", {
            "workflow": "signal_analysis",
            "decision_id": str(uuid.uuid4())[:8],
            "message_id": str(uuid.uuid4())[:8],
            "answer": final_markdown,
            "answer_len": len(final_markdown)
        })
        bus.emit("stream.end", {})

    # Store in memory for conversation context
    memory.store(final_markdown[:1000], role="assistant", mem_type="conversation", importance=0.8)

    return {
        "workflow": "signal_analysis",
        "response": final_markdown,
        "agents_used": ["nexus"] + specialist_ids,
        "latency_ms": total_latency,
        "confidence": boardroom_json.get("final_confidence", 9.0) / 10.0,
        "structured": {
            "decision": boardroom_json,
            "specialists": specialist_reviews,
            "nexus": boardroom_json,
        }
    }
