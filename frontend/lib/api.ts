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
