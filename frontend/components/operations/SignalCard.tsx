"use client"

import { formatRelativeTime } from "@/lib/utils"
import { SEVERITY_CONFIG, CATEGORY_CONFIG } from "@/lib/constants/severity"
import type { Signal } from "@/lib/api"

interface Props {
  signal: Signal
  onClick?: () => void
}

export function SignalCard({ signal, onClick }: Props) {
  const isHigh = signal.severity.toLowerCase() === "high" || signal.severity.toLowerCase() === "critical"
  const isMedium = signal.severity.toLowerCase() === "medium" || signal.severity.toLowerCase() === "warning"
  
  // Custom refined editorial color palette
  const severityColor = isHigh 
    ? "hsl(11, 63%, 59%)"   // terracotta clay/coral for critical
    : isMedium 
      ? "hsl(35, 38%, 64%)" // antique brass for medium/warning
      : "hsl(43, 12% , 65%)" // sand/gray for info

  const category = CATEGORY_CONFIG[signal.category as keyof typeof CATEGORY_CONFIG] || CATEGORY_CONFIG.market

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-card/40 border border-border/40 hover:border-primary/40 rounded-xl p-3.5 transition-all duration-300 hover:-translate-y-0.5 hover:bg-card/75 group shadow-sm flex flex-col gap-2.5 relative overflow-hidden"
    >
      {/* Editorial side accent border */}
      <span className="absolute left-0 top-0 bottom-0 w-0.75" style={{ backgroundColor: severityColor }} />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="text-[10px]" style={{ color: severityColor }}>
            {category.icon}
          </span>
          <span className="text-[8px] font-mono font-bold tracking-widest uppercase" style={{ color: severityColor }}>
            {signal.severity}
          </span>
        </div>
        <span className="text-[9px] font-mono text-muted-foreground/60 tabular-nums">
          {formatRelativeTime(signal.detected_at)}
        </span>
      </div>

      <div>
        <div className="text-[12px] font-medium leading-snug tracking-tight text-parchment group-hover:text-foreground transition-colors">
          {signal.title}
        </div>
        {signal.description && (
          <div className="text-[10px] text-muted-foreground/80 line-clamp-2 leading-relaxed mt-1">
            {signal.description}
          </div>
        )}
      </div>

      <div className="flex items-center gap-1.5 text-[9px] font-mono text-muted-foreground/50 border-t border-border/20 pt-2 mt-0.5 w-full">
        <span>telemetry</span>
        <span className="text-muted-foreground/30">·</span>
        <span className="font-semibold uppercase tracking-wider text-muted-foreground/80" style={{ color: severityColor }}>
          {signal.source_agent}
        </span>
        {!signal.seen && (
          <span className="ml-auto w-1.25 h-1.25 rounded-full bg-primary animate-pulse" title="Unseen" />
        )}
      </div>
    </button>
  )
}

