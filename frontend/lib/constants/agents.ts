import type { AgentConfig } from "@/types"

export const AGENTS: Record<string, AgentConfig> = {
  nexus: {
    id: "nexus",
    name: "Nexus",
    role: "CMO Orchestrator",
    color: "#c5a880",
    icon: "◉",
  },
  seo: {
    id: "seo",
    name: "SEO",
    role: "Search Optimization",
    color: "#dfdacf",
    icon: "◎",
  },
  content: {
    id: "content",
    name: "Content",
    role: "Content Strategy",
    color: "#8e2b32",
    icon: "✦",
  },
  analytics: {
    id: "analytics",
    name: "Analytics",
    role: "Data & Metrics",
    color: "#8a857b",
    icon: "▣",
  },
  cro: {
    id: "cro",
    name: "CRO",
    role: "Conversion Optimization",
    color: "#a3b899",
    icon: "◑",
  },
  aeo: {
    id: "aeo",
    name: "AEO",
    role: "AI Search Optimization",
    color: "#e8927d",
    icon: "◯",
  },
}

export function getAgentConfig(id: string): AgentConfig {
  return AGENTS[id.toLowerCase()] || AGENTS.nexus
}
