"use client"

import { getAgentConfig } from "@/lib/constants/agents"

interface AgentAvatarProps {
  agentId: string
  size?: "xs" | "sm" | "md"
  showRing?: boolean
}

export function AgentAvatar({ agentId, size = "sm", showRing = false }: AgentAvatarProps) {
  const cfg = getAgentConfig(agentId)

  const sizeClasses = {
    xs: "w-4 h-4 text-[8px]",
    sm: "w-6 h-6 text-[10px]",
    md: "w-8 h-8 text-xs",
  }

  return (
    <div
      className={`${sizeClasses[size]} rounded-full flex items-center justify-center text-white font-bold flex-shrink-0 ${showRing ? "ring-2 ring-background" : ""}`}
      style={{ background: cfg.color }}
      title={cfg.name}
    >
      {cfg.name.charAt(0)}
    </div>
  )
}

export function AgentAvatarStack({
  agentIds,
  max = 3,
  size = "sm",
}: {
  agentIds: string[]
  max?: number
  size?: "xs" | "sm" | "md"
}) {
  const shown = agentIds.slice(0, max)
  const remaining = Math.max(0, agentIds.length - max)

  const sizeClass = size === "xs" ? "w-4 h-4 text-[8px]" : size === "sm" ? "w-6 h-6 text-[10px]" : "w-8 h-8 text-xs"

  return (
    <div className="flex items-center -space-x-1">
      {shown.map((id) => (
        <AgentAvatar key={id} agentId={id} size={size} showRing />
      ))}
      {remaining > 0 && (
        <div
          className={`${sizeClass} rounded-full bg-muted text-muted-foreground flex items-center justify-center font-medium ring-2 ring-background`}
        >
          +{remaining}
        </div>
      )}
    </div>
  )
}
