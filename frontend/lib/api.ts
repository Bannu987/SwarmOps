import { createClient } from "@/lib/supabase/client"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://swarmops.onrender.com"

async function authHeaders(): Promise<Record<string, string>> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {}
}

export async function sendChat(message: string, conversationId?: string, projectId?: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({ message, conversation_id: conversationId, project_id: projectId }),
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
  projectId?: string
) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({ message, conversation_id: conversationId, project_id: projectId }),
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
    const lines = buffer.split("\n\n")
    buffer = lines.pop() || ""

    for (const line of lines) {
      const trimmed = line.trim()
      if (!trimmed) continue

      if (trimmed.startsWith("data: ")) {
        try {
          const rawJson = trimmed.substring(6)
          const data = JSON.parse(rawJson)
          onEvent(data)
        } catch (e) {
          console.error("Failed to parse SSE line:", trimmed, e)
        }
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
  status: "pending" | "in_progress" | "completed" | "blocked" | "dismissed"
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

