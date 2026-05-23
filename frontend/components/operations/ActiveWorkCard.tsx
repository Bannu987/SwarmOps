"use client"

import { Loader2, CheckCircle2, AlertCircle } from "lucide-react"
import { getAgentConfig } from "@/lib/constants/agents"

interface ActiveWorkItem {
  id: string
  agentId: string
  task: string
  status: "thinking" | "complete" | "waiting"
  durationSec?: number
  progress?: number
}

interface Props {
  item: ActiveWorkItem
  onClick?: () => void
}

export function ActiveWorkCard({ item, onClick }: Props) {
  const cfg = getAgentConfig(item.agentId)

  const statusConfig = {
    thinking: { dot: "#22D3EE", icon: <Loader2 className="w-3 h-3 animate-spin" />, label: cfg.name },
    complete:  { dot: "#22C55E", icon: <CheckCircle2 className="w-3 h-3" />, label: "Ready" },
    waiting:   { dot: "#FB923C", icon: <AlertCircle className="w-3 h-3" />, label: "Awaiting input" },
  }

  const sc = statusConfig[item.status]

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-card border border-border rounded-lg p-3 hover:border-primary/30 transition"
    >
      <div className="flex items-center gap-2 mb-2">
        <div
          className={`w-1.5 h-1.5 rounded-full ${item.status === "thinking" ? "animate-pulse" : ""}`}
          style={{ background: sc.dot }}
        />
        <span className="text-[11px] font-medium" style={{ color: sc.dot }}>
          {sc.label}
        </span>
        {item.durationSec !== undefined && (
          <span className="text-[10px] font-mono text-muted-foreground ml-auto">
            {item.durationSec}s
          </span>
        )}
      </div>

      <div className="text-[12px] text-foreground/85 leading-snug mb-2 tracking-tight">
        {item.task}
      </div>

      {item.progress !== undefined && item.status === "thinking" && (
        <div className="h-0.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full transition-all duration-300"
            style={{ width: `${item.progress}%`, background: sc.dot }}
          />
        </div>
      )}
    </button>
  )
}

export type { ActiveWorkItem }
