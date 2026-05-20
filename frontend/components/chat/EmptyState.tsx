"use client"

import { Sparkles } from "lucide-react"
import { AGENTS } from "@/lib/constants/agents"

interface Props {
  onQuickAction: (text: string) => void
}

const QUICK_ACTIONS = [
  "Run a marketing audit on my site",
  "Create a content strategy for Q1 2026",
  "Find SEO keyword opportunities",
  "Analyze my conversion funnel",
]

export function EmptyState({ onQuickAction }: Props) {
  return (
    <div className="max-w-2xl mx-auto pt-12 px-4 text-center">
      <div className="w-14 h-14 mx-auto rounded-2xl bg-gradient-to-br from-primary to-swarm-cyan flex items-center justify-center text-white mb-5">
        <Sparkles className="w-6 h-6" />
      </div>

      <h2 className="text-2xl font-semibold mb-2">
        How can your AI marketing team help?
      </h2>
      <p className="text-sm text-muted-foreground mb-8">
        6 specialist agents · 6 workflows · Ready to execute
      </p>

      <div className="grid grid-cols-2 gap-2 mb-8">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action}
            onClick={() => onQuickAction(action)}
            className="text-left px-4 py-3 bg-card hover:bg-muted border border-border rounded-lg text-sm text-muted-foreground hover:text-foreground transition"
          >
            {action}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-3 gap-2 mb-8">
        {Object.values(AGENTS).map((agent) => (
          <div
            key={agent.id}
            className="px-3 py-2 bg-card border border-border rounded-lg text-left"
          >
            <div className="flex items-center gap-2">
              <div
                className="w-1.5 h-1.5 rounded-full"
                style={{ background: agent.color }}
              />
              <span className="text-xs font-medium">{agent.name}</span>
            </div>
            <div className="text-[10px] text-muted-foreground mt-0.5 truncate">
              {agent.role}
            </div>
          </div>
        ))}
      </div>

      <p className="text-xs text-muted-foreground">
        Type{" "}
        <kbd className="px-1.5 py-0.5 bg-muted border border-border rounded text-[10px]">/</kbd>{" "}
        for commands · Click 📎 to upload files (any type)
      </p>
    </div>
  )
}
