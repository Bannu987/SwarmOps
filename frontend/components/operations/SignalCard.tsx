"use client"

import { formatRelativeTime } from "@/lib/utils"
import { SEVERITY_CONFIG, CATEGORY_CONFIG } from "@/lib/constants/severity"
import type { Signal } from "@/lib/api"

interface Props {
  signal: Signal
  onClick?: () => void
}

export function SignalCard({ signal, onClick }: Props) {
  const severity = SEVERITY_CONFIG[signal.severity] || SEVERITY_CONFIG.medium
  const category = CATEGORY_CONFIG[signal.category as keyof typeof CATEGORY_CONFIG] || CATEGORY_CONFIG.market

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-card border border-border rounded-lg p-3 hover:border-primary/30 transition group"
      style={{ borderLeftWidth: "2px", borderLeftColor: severity.color }}
    >
      <div className="flex items-center justify-between mb-1.5">
        <div className="flex items-center gap-2">
          <span className="text-[10px]" style={{ color: category.color }}>
            {category.icon}
          </span>
          <span className="text-[9px] font-mono font-semibold tracking-wider" style={{ color: severity.color }}>
            {severity.label}
          </span>
        </div>
        <span className="text-[10px] text-muted-foreground">{formatRelativeTime(signal.detected_at)}</span>
      </div>

      <div className="text-[13px] text-foreground/90 leading-snug mb-1 tracking-tight">
        {signal.title}
      </div>

      {signal.description && (
        <div className="text-[11px] text-muted-foreground line-clamp-2 leading-relaxed">
          {signal.description}
        </div>
      )}

      <div className="mt-2 flex items-center gap-1.5 text-[10px] text-muted-foreground">
        <span>by</span>
        <span className="font-medium" style={{ color: category.color }}>
          {signal.source_agent}
        </span>
        {!signal.seen && (
          <span className="ml-auto w-1.5 h-1.5 rounded-full bg-primary animate-pulse" title="Unseen" />
        )}
      </div>
    </button>
  )
}
