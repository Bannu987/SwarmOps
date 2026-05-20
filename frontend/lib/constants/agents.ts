import type { AgentConfig } from "@/types"

export const AGENTS: Record<string, AgentConfig> = {
  nexus: {
    id: "nexus",
    name: "Nexus",
    role: "CMO Orchestrator",
    color: "#6366f1",
    icon: "◉",
  },
  seo: {
    id: "seo",
    name: "SEO",
    role: "Search Optimization",
    color: "#22d3ee",
    icon: "◎",
  },
  content: {
    id: "content",
    name: "Content",
    role: "Content Strategy",
    color: "#a855f7",
    icon: "✦",
  },
  analytics: {
    id: "analytics",
    name: "Analytics",
    role: "Data & Metrics",
    color: "#10b981",
    icon: "▣",
  },
  cro: {
    id: "cro",
    name: "CRO",
    role: "Conversion Optimization",
    color: "#22c55e",
    icon: "◑",
  },
  aeo: {
    id: "aeo",
    name: "AEO",
    role: "AI Search Optimization",
    color: "#fbbf24",
    icon: "◯",
  },
}

export function getAgentConfig(id: string): AgentConfig {
  return AGENTS[id.toLowerCase()] || AGENTS.nexus
}
