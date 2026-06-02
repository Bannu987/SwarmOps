"use client"

import { ArrowRight } from "lucide-react"
import { AgentAvatarStack } from "@/components/shared/AgentAvatar"
import { IMPACT_CONFIG, CATEGORY_CONFIG } from "@/lib/constants/severity"
import type { Opportunity } from "@/lib/api"

interface Props {
  opportunity: Opportunity
  onClick?: () => void
  rank?: number
}

export function OpportunityCard({ opportunity: opp, onClick, rank }: Props) {
  const impact = IMPACT_CONFIG[opp.expected_impact] || IMPACT_CONFIG.medium
  const category = CATEGORY_CONFIG[opp.category as keyof typeof CATEGORY_CONFIG] || CATEGORY_CONFIG.market
  const isTopRank = rank === 0

  const allAgents = [opp.proposed_by, ...opp.endorsed_by.filter((a) => a !== opp.proposed_by)]

  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-card/65 border border-border/50 rounded-lg p-3.5 transition-all duration-300 hover:border-primary/35 hover:bg-card/90 hover:-translate-y-0.5 shadow-sm group"
      style={
        isTopRank
          ? { borderColor: "rgba(197, 168, 128, 0.3)", borderLeftWidth: "3px", borderLeftColor: "var(--primary)" }
          : {}
      }
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[9px] font-mono font-semibold tracking-wider" style={{ color: impact.color }}>
            {impact.label}
          </span>
          <span className="text-[9px] font-mono text-muted-foreground">
            {category.label.toUpperCase()}
          </span>
        </div>
        <span className="text-[10px] font-mono text-muted-foreground tabular-nums">
          {(opp.confidence * 100).toFixed(0)}%
        </span>
      </div>

      {/* Title */}
      <div
        className={`text-[13px] leading-snug mb-2 tracking-tight ${
          isTopRank ? "text-foreground font-medium" : "text-foreground/90"
        }`}
      >
        {opp.title}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <AgentAvatarStack agentIds={allAgents} size="xs" />
          <span className="text-[10px] text-muted-foreground">
            {allAgents.length === 1 ? `${allAgents[0]} proposes` : `${allAgents.length} agents agree`}
          </span>
        </div>
        <div className="flex items-center gap-1.5 text-muted-foreground group-hover:text-primary transition">
          <span className="text-[10px] font-mono">RICE {opp.rice_score.toFixed(2)}</span>
          <ArrowRight className="w-3 h-3" />
        </div>
      </div>
    </button>
  )
}
