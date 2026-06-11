"use client"

import { Sparkles, Terminal } from "lucide-react"
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
    <div className="max-w-2xl mx-auto pt-16 px-4 text-center select-none animate-fade-in">
      <div className="w-12 h-12 mx-auto rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-primary-foreground mb-6 shadow-lg glow-blue">
        <Sparkles className="w-5 h-5 animate-pulse" />
      </div>

      <h2 className="text-xl md:text-2xl font-serif font-normal tracking-tight text-foreground mb-2">
        How can the boardroom swarm help?
      </h2>
      <p className="text-xs text-muted-foreground mb-8">
        6 specialist intelligence cores · 6 coordinated workflows · Synced and ready to execute
      </p>

      {/* Quick Actions Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
        {QUICK_ACTIONS.map((action) => (
          <button
            key={action}
            onClick={() => onQuickAction(action)}
            className="text-left px-4.5 py-3.5 glass-panel glass-panel-hover rounded-xl text-xs text-muted-foreground hover:text-foreground transition duration-300"
          >
            {action}
          </button>
        ))}
      </div>

      {/* Agents Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 mb-8">
        {Object.values(AGENTS).map((agent) => (
          <div
            key={agent.id}
            className="px-3 py-2.5 glass-panel rounded-lg text-left relative overflow-hidden"
            style={{
              borderTop: `1px solid ${agent.color}30`
            }}
          >
            <div className="flex items-center gap-1.5 mb-1.5">
              <span className="text-xs">{agent.icon}</span>
              <span className="text-[10px] font-semibold text-foreground truncate">{agent.name}</span>
            </div>
            <div className="text-[8px] font-mono text-muted-foreground uppercase tracking-wider truncate">
              {agent.role}
            </div>
          </div>
        ))}
      </div>

      <p className="text-[10px] font-mono text-muted-foreground/60 flex items-center justify-center gap-1.5">
        <Terminal className="w-3.5 h-3.5 text-primary/80" />
        <span>Type <kbd className="px-1.5 py-0.5 bg-card border border-border/80 rounded text-[9px] font-mono">/</kbd> for commands · Drag files to upload</span>
      </p>
    </div>
  )
}
