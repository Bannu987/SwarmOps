export interface Message {
  id?: string
  role: "user" | "assistant" | "system"
  content: string
  agents_used?: string[]
  workflow?: string | null
  latency_ms?: number
  confidence?: number
  artifact_id?: string
  attachments?: FileAttachment[]
  created_at?: string
  timestamp?: number
  clicked_signal?: any
  trace_id?: string
  workflow_version?: string
  prompt_version?: string
  model_name?: string
  last_event?: string
  stream_status?: string
  action_plan_status?: string
  verification_status?: string
  retrieved_memories?: Array<{ id: string; memory_type: string; title: string; source_id?: string }>
}

export interface FileAttachment {
  filename: string
  file_type: string
  file_size: number
  word_count?: number
  summary?: string
}

export interface Conversation {
  id: string
  title: string
  pinned: boolean
  archived: boolean
  message_count: number
  last_message_at: string
  created_at: string
  project_id?: string | null
}

export interface Project {
  id: string
  name: string
  description: string
  website_url: string
  pinned: boolean
  archived: boolean
  brand_data: Record<string, unknown>
}

export interface SlashCommand {
  cmd: string
  desc: string
  icon: string
  category: "agent" | "action"
}

export interface AgentConfig {
  id: string
  name: string
  role: string
  color: string
  icon: string
}
