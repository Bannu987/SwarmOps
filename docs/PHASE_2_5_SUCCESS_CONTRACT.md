# Phase 2.5 Success Contract: End-to-End Live Reliability Spine for SwarmOps

This document defines the pass/fail criteria and verification protocols for the SwarmOps Phase 2.5 production-readiness gate.

## Pass/Fail Criteria Checklist

| ID | Criteria Description | Status | Verification Method |
|----|----------------------|--------|---------------------|
| 1  | 5 Real Production Runs | Pending | Execute 5 runs using public sites and record their details in the E2E matrix. |
| 2  | Trace ID Propagation | Passed | Verify `trace_id` UUID generated at scan / signal detection propagates to boardroom chat, final decision, action plan, and SSE logs. |
| 3  | Boardroom Run Metadata | Passed | Check `run_traces` database logs for presence of prompt, model, and workflow version constants. |
| 4  | Action Plan Linage | Passed | Ensure created `action_plans` records contain `user_id`, `project_id`, `signal_id`, `decision` reference, and `trace_id`. |
| 5  | SSE Stream Events | Passed | Verify SSE emitter yields `stream.started`, `decision.reached`, `final.answer`, and `stream.end` (or `stream.failed` on errors). |
| 6  | Duplicate Approval Gate | Passed | Attempt to approve the same signal twice; confirm backend returns HTTP 409 and logs `action_plan.duplicate_detected`. |
| 7  | Action Plan Persistence | Passed | Refresh the Operations Floor; verify created action plans persist via database fetch. |
| 8  | Verification Feedback | Passed | Run verify on a failed endpoint; verify response message displays clear explanation (e.g., HTTP 404 or connection error). |
| 9  | Verification Success | Passed | Run verify on a correct endpoint; verify status updates to `verified` and checklist tasks update to `completed`. |
| 10 | Browser Console Health | Pending | Check browser logs during runs; verify zero errors. |
| 11 | Render Logs Cleanliness | Pending | Inspect backend log output; verify no unhandled runtime errors. |
| 12 | Clean Repository | Pending | Confirm `git status` shows all files committed and pushed cleanly. |

## Version Constants
- **BOARDROOM_PROMPT_VERSION**: `1.1.0`
- **SIGNAL_RULES_VERSION**: `1.1.0`
- **ACTION_PLAN_SCHEMA_VERSION**: `1.1.0`
- **VERIFICATION_RULES_VERSION**: `1.1.0`
- **WORKFLOW_VERSION**: `1.5.0`

## Feature Flags
- `ENABLE_ACTION_PLAN_CREATION` (Default: `true`)
- `ENABLE_AUTO_VERIFICATION` (Default: `true`)
- `ENABLE_DETERMINISTIC_SIGNAL_RULES` (Default: `true`)
- `ENABLE_STREAMING_BOARDROOM` (Default: `true`)
- `ENABLE_MODEL_FALLBACK` (Default: `true`)
- `ENABLE_TRACE_LOGGING` (Default: `true`)
