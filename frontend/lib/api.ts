import { createClient } from "@/lib/supabase/client"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://swarmops.onrender.com"

async function authHeaders(): Promise<Record<string, string>> {
  try {
    const supabase = createClient()
    let { data: { session } } = await supabase.auth.getSession()
    
    if (session) {
      // Check if session token is expired or close to expiry (e.g. less than 2 minutes left)
      const expiresAt = session.expires_at // unix timestamp
      const now = Math.floor(Date.now() / 1000)
      if (expiresAt && expiresAt - now < 120) {
        console.info("[AUTH CLIENT] Session is close to expiring. Attempting proactive token refresh...")
        const { data: { session: refreshed }, error } = await supabase.auth.refreshSession()
        if (refreshed) {
          session = refreshed
          console.info("[AUTH CLIENT] Proactive token refresh succeeded.")
        } else if (error) {
          console.warn("[AUTH CLIENT] Proactive session refresh failed:", error)
        }
      }
    } else {
      // No active session found via getSession. Let's check getUser() which is more authoritative
      // and can restore sessions from cookies or local storage.
      console.info("[AUTH CLIENT] No session found via getSession(). Checking getUser() fallback...")
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
        console.info("[AUTH CLIENT] User found via getUser(). Re-fetching refreshed session...")
        const fresh = await supabase.auth.getSession()
        session = fresh.data.session
      }
    }
    
    return session?.access_token
      ? { Authorization: `Bearer ${session.access_token}` }
      : {}
  } catch (err) {
    console.error("[AUTH CLIENT] Failed to construct authorization headers:", err)
    return {}
  }
}


export async function sendChat(message: string, conversationId?: string, projectId?: string, clickedSignal?: any, traceId?: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({ 
      message, 
      conversation_id: conversationId, 
      project_id: projectId,
      clicked_signal: clickedSignal,
      trace_id: traceId
    }),
  })
  return res.json()
}


export async function uploadFile(file: File) {
  const headers = await authHeaders()
  const formData = new FormData()
  formData.append("file", file)
  const res = await fetch(`${API_URL}/api/upload`, {
    method: "POST",
    headers,
    body: formData,
  })
  return res.json()
}

export async function listConversations() {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/conversations`, { headers })
  return res.json()
}

export async function createConversation() {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/conversations`, {
    method: "POST",
    headers,
  })
  return res.json()
}

export async function getMessages(conversationId: string) {
  const headers = await authHeaders()
  const res = await fetch(
    `${API_URL}/api/conversations/${conversationId}/messages`,
    { headers }
  )
  return res.json()
}

export async function listProjects() {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/projects`, { headers })
  return res.json()
}

export async function createProject(data: {
  name: string
  description?: string
  website_url?: string
}) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function connectService(
  service: string,
  credentials: Record<string, unknown>
) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/credentials`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({ service, credentials }),
  })
  return res.json()
}

export async function listConnectedServices() {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/credentials`, { headers })
  return res.json()
}

// ============================================================
// TYPES
// ============================================================

export interface Project {
  id: string
  user_id: string
  name: string
  description: string
  website_url: string
  brand_data: Record<string, unknown>
  pinned: boolean
  archived: boolean
  created_at: string
  updated_at: string
}

export interface Signal {
  id: string
  user_id: string
  project_id: string | null
  signal_type: "risk_alert" | "opportunity_window" | "competitor_move" | "traffic_anomaly" | "ranking_change" | "content_decay"
  severity: "critical" | "high" | "medium" | "low"
  category: "risk" | "opportunity" | "market" | "content" | "seo" | "analytics"
  title: string
  description: string
  source_agent: string
  source_detail: string | null
  evidence: Array<{ claim: string; source: string; value?: string }>
  raw_data: Record<string, unknown>
  status: "active" | "addressed" | "dismissed" | "expired"
  seen: boolean
  detected_at: string
  expires_at: string | null
}

export interface Opportunity {
  id: string
  user_id: string
  project_id: string | null
  title: string
  description: string
  category: "seo" | "content" | "cro" | "aeo" | "analytics" | "market"
  signal_ids: string[]
  recommended_action: string
  expected_impact: "high" | "medium" | "low"
  effort: "low" | "medium" | "high"
  timeframe: string
  rice_score: number
  confidence: number
  proposed_by: string
  endorsed_by: string[]
  status: "active" | "in_progress" | "completed" | "dismissed"
  created_at: string
}

// ============================================================
// SIGNALS
// ============================================================

export async function listSignals(status: string = "active", projectId?: string) {
  const headers = await authHeaders()
  const url = `${API_URL}/api/signals?status=${status}&limit=50` + (projectId ? `&project_id=${projectId}` : "")
  const res = await fetch(url, { headers })
  return res.json() as Promise<{ signals: Signal[] }>
}

export async function updateSignal(id: string, updates: { seen?: boolean; status?: string }) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/signals/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(updates),
  })
  return res.json()
}

// ============================================================
// OPPORTUNITIES
// ============================================================

export async function listOpportunities(status: string = "active", projectId?: string) {
  const headers = await authHeaders()
  const url = `${API_URL}/api/opportunities?status=${status}&limit=50` + (projectId ? `&project_id=${projectId}` : "")
  const res = await fetch(url, { headers })
  return res.json() as Promise<{ opportunities: Opportunity[] }>
}

export async function updateOpportunity(id: string, updates: { status?: string; user_action?: string }) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/opportunities/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(updates),
  })
  return res.json()
}

// ============================================================
// SCAN
// ============================================================

export async function triggerScan(projectId?: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/scan`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(projectId ? { project_id: projectId } : {}),
  })
  return res.json()
}

// ============================================================
// CHAT STREAMING (SSE)
// ============================================================

export async function streamChat(
  message: string,
  conversationId: string,
  onEvent: (event: any) => void,
  projectId?: string,
  clickedSignal?: any,
  traceId?: string
) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({ 
      message, 
      conversation_id: conversationId, 
      project_id: projectId,
      clicked_signal: clickedSignal,
      trace_id: traceId
    }),
  })


  if (!res.ok) {
    throw new Error(`HTTP error ${res.status}`)
  }

  const reader = res.body?.getReader()
  if (!reader) {
    throw new Error("No readable stream in response")
  }

  const decoder = new TextDecoder("utf-8")
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const normalized = buffer.replace(/\r\n/g, "\n")
    const blocks = normalized.split("\n\n")
    buffer = blocks.pop() || ""

    for (const block of blocks) {
      const trimmedBlock = block.trim()
      if (!trimmedBlock) continue

      try {
        let eventName = ""
        let dataBuffer = ""
        const blockLines = trimmedBlock.split("\n")
        
        for (const blockLine of blockLines) {
          const lineTrimmed = blockLine.trim()
          if (lineTrimmed.startsWith("event: ")) {
            eventName = lineTrimmed.substring(7).trim()
          } else if (lineTrimmed.startsWith("data: ")) {
            dataBuffer += lineTrimmed.substring(6).trim()
          } else if (lineTrimmed.startsWith("data:")) {
            dataBuffer += lineTrimmed.substring(5).trim()
          }
        }

        let parsedData = null
        if (dataBuffer) {
          parsedData = JSON.parse(dataBuffer)
        } else {
          // Format C legacy fallback: try to parse the entire block as raw JSON
          try {
            parsedData = JSON.parse(trimmedBlock)
          } catch (jsonErr) {
            // Not a raw JSON block
          }
        }

        if (parsedData) {
          if (eventName) {
            parsedData.type = eventName
          }
          onEvent(parsedData)
        }
      } catch (e) {
        console.error("Failed to parse SSE block:", trimmedBlock, e)
      }
    }
  }
}

// ============================================================
// MEMORIES & BRIEFS
// ============================================================

export interface ProjectMemory {
  id: string
  user_id: string
  project_id: string
  memory_type: "brand_voice" | "icp" | "competitor" | "campaign_goal" | "channel_strategy" | "previous_decision" | "approved_action" | "rejected_action" | "data_gap" | "experiment" | "report_insight"
  title: string
  summary: string
  source: "user" | "swarm_decision" | "file_upload" | "scanner"
  confidence: number
  tags: string[]
  created_at: string
}

export interface StrategyBrief {
  id: string
  user_id: string
  project_id: string | null
  conversation_id: string | null
  artifact_type: string
  title: string
  content: {
    markdown: string
    user_directive?: string
  }
  status: "pending" | "approved" | "rejected" | "deployed"
  created_at: string
}

export async function listProjectMemories(projectId: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/projects/${projectId}/memories`, { headers })
  return res.json() as Promise<{ memories: ProjectMemory[] }>
}

export async function createProjectMemory(projectId: string, data: {
  memory_type: string
  title: string
  summary: string
  source?: string
  tags?: string[]
}) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/projects/${projectId}/memories`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(data),
  })
  return res.json() as Promise<ProjectMemory>
}

export async function deleteProjectMemory(memoryId: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/memories/${memoryId}`, {
    method: "DELETE",
    headers,
  })
  return res.json() as Promise<{ success: boolean }>
}

export async function generateStrategyBrief(projectId: string, userDirective?: string, template?: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/projects/${projectId}/briefs`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({ 
      user_directive: userDirective || "",
      template: template || "general_strategy"
    }),
  })
  return res.json() as Promise<StrategyBrief>
}

export async function listStrategyBriefs(projectId: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/projects/${projectId}/briefs`, { headers })
  return res.json() as Promise<{ briefs: StrategyBrief[] }>
}

export async function getStrategyBrief(briefId: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/briefs/${briefId}`, { headers })
  return res.json() as Promise<StrategyBrief>
}

// ============================================================
// ACTION PLANS
// ============================================================

export interface ActionPlanTask {
  id: string
  title: string
  status: "pending" | "in_progress" | "completed" | "blocked" | "dismissed"
  owner: string
}

export interface ActionPlanKPI {
  metric: string
  target: string
  timeframe: string
}

export interface ActionPlanRisk {
  risk: string
  mitigation: string
}

export interface ActionPlan {
  id: string
  user_id: string
  project_id: string
  opportunity_id: string | null
  source_type: "opportunity" | "swarm_decision" | "strategy_brief" | "user"
  source_id: string | null
  title: string
  objective: string
  plan_type: "seo_growth" | "paid_ads" | "lead_generation" | "content_calendar" | "crm_lifecycle" | "product_launch" | "competitor_attack" | "conversion_rate_optimization" | "general_strategy"
  priority: "high" | "medium" | "low"
  status: "pending" | "approved" | "in_progress" | "verified" | "rejected" | "completed" | "blocked" | "dismissed"
  owner_label: string
  due_date: string | null
  estimated_effort: "low" | "medium" | "high"
  expected_impact: "low" | "medium" | "high"
  confidence: number
  tasks: ActionPlanTask[]
  kpis: ActionPlanKPI[]
  dependencies: string[]
  risks: ActionPlanRisk[]
  created_at: string
  signal_id?: string
  signal_key?: string
  priority_score?: number
  recommended_fix?: string
  evidence?: any
  implementation_steps?: string
  verification_steps?: string
}

export async function listActionPlans(projectId: string, status: string = "all") {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/projects/${projectId}/action-plans?status=${status}`, { headers })
  return res.json() as Promise<{ action_plans: ActionPlan[] }>
}

export async function createActionPlan(projectId: string, data: Partial<ActionPlan>) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/projects/${projectId}/action-plans`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(data),
  })
  return res.json() as Promise<ActionPlan>
}

export async function updateActionPlan(planId: string, updates: Partial<ActionPlan>) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/action-plans/${planId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(updates),
  })
  return res.json() as Promise<ActionPlan>
}

export async function deleteActionPlan(planId: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/action-plans/${planId}`, {
    method: "DELETE",
    headers,
  })
  return res.json() as Promise<{ success: boolean }>
}

export async function createActionPlanFromBoardroom(data: {
  project_id: string
  signal_id: string
  signal_key: string
  title: string
  priority_bucket: string
  priority_score: number
  owner: string
  recommended_fix: string
  evidence: any
  implementation_steps: string
  verification_steps: string
  checklist_items: string[]
  expected_impact: string
  effort: string
}) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/action-plans/from-boardroom`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(data),
  })
  if (res.status === 409) {
    return { duplicate: true }
  }
  if (!res.ok) {
    throw new Error(`HTTP error ${res.status}`)
  }
  return res.json() as Promise<ActionPlan>
}

export async function verifyActionPlanCompletion(planId: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/action-plans/${planId}/verify`, {
    method: "POST",
    headers,
  })
  return res.json() as Promise<{ success: boolean; message: string; status?: string }>
}

// ============================================================
// RUN TRACE RECOVERY (Phase 2.6)
// ============================================================

export interface RunTraceResponse {
  trace_id: string
  status: "running" | "completed" | "failed" | "error"
  run_type: string
  started_at: string
  ended_at: string | null
  workflow_version: string
  prompt_version: string
  model_name: string
  provider: string | null
  latency_ms: number | null
  replay_snapshot?: {
    // Raw structured output
    final_structured_output?: Record<string, any>
    scoring_inputs?: Record<string, any>
    // Normalized convenience fields
    final_answer_available?: boolean
    confidence?: number
    agents_consulted?: string[]
    action_plan_created?: boolean
    latency_ms?: number
    // Key decision fields (mapped from LLM output)
    title?: string
    priority_score?: number
    priority_bucket?: string
    action_description?: string
    executive_summary?: string
    checklist?: string[]
    verification_method?: string
    final_decision?: string
  }
}

export async function getRunTrace(traceId: string): Promise<RunTraceResponse | null> {
  const headers = await authHeaders()
  try {
    const res = await fetch(`${API_URL}/api/runs/${traceId}`, { headers })
    if (!res.ok) {
      console.warn(`[RECOVERY] getRunTrace returned ${res.status}`)
      return null
    }
    return res.json() as Promise<RunTraceResponse>
  } catch (err) {
    console.warn("[RECOVERY] getRunTrace network error:", err)
    return null
  }
}
