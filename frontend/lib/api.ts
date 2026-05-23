import { createClient } from "@/lib/supabase/client"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://marketingos2-0.onrender.com"

async function authHeaders(): Promise<Record<string, string>> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()
  return session?.access_token
    ? { Authorization: `Bearer ${session.access_token}` }
    : {}
}

export async function sendChat(message: string, conversationId?: string) {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify({ message, conversation_id: conversationId }),
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

export async function listSignals(status: string = "active") {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/signals?status=${status}&limit=50`, { headers })
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

export async function listOpportunities(status: string = "active") {
  const headers = await authHeaders()
  const res = await fetch(`${API_URL}/api/opportunities?status=${status}&limit=50`, { headers })
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
