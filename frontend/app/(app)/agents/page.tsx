"use client"

import { AGENTS } from "@/lib/constants/agents"
import { Bot, Sparkles, Network } from "lucide-react"
import Link from "next/link"

const AGENT_DESCRIPTIONS: Record<string, string> = {
  nexus: "Orchestrates the entire swarm debate, consolidates recommendations, guarantees brand context alignment, and serves as the strategic chief marketing officer.",
  seo: "Audits search visibility, identifies organic keyword gaps, tracks competitors' search footprints, and monitors technical crawl and index issues.",
  content: "Maps content strategies, identifies content decay in your existing articles, outlines search-optimized briefs, and drafts high-converting ad and email copy.",
  analytics: "Detects spikes or anomalies in site traffic, visualizes channel conversion funnels, and aggregates cross-platform audience attribution trends.",
  cro: "Pinpoints leaks in signups and checkouts, maps page layout friction audits, and outlines robust A/B testing ideas to lift signups and conversions.",
  aeo: "Optimizes brand mentions for Answer Engine Optimization (like Perplexity, ChatGPT, and Gemini search queries) to secure dominant visibility in AI results."
}

export default function AgentsPage() {
  return (
    <div className="flex-grow overflow-y-auto px-8 py-8 bg-background animate-fade-in">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8 border-b border-border/60 pb-5">
          <div className="flex items-baseline gap-2 mb-1">
            <h1 className="text-2xl md:text-3xl font-serif font-normal tracking-tight text-foreground">
              Agent Network
            </h1>
            <span className="text-[10px] font-mono text-primary/70 uppercase tracking-widest">
              [OPERATING_SWARM_CORES]
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            Specialist machine intelligences collaborate under Nexus CMO to audit marketing telemetry, generate campaign checklists, and execute strategies.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {Object.values(AGENTS).map((agent) => {
            const desc = AGENT_DESCRIPTIONS[agent.id.toLowerCase()] || "Specialist AI marketing assistant ready to execute campaigns."
            return (
              <div
                key={agent.id}
                className="bg-card/65 border border-border/40 rounded-lg p-5 hover:border-primary/45 hover:bg-card/90 transition-all duration-300 group flex flex-col justify-between shadow-sm"
                style={{
                  background: `linear-gradient(180deg, ${agent.color}08 0%, transparent 100%)`,
                }}
              >
                <div>
                  <div className="flex items-start justify-between mb-4 border-b border-border/30 pb-3">
                    <div
                      className="w-8 h-8 rounded flex items-center justify-center text-black text-xs font-bold transition-transform group-hover:scale-105 shadow-sm"
                      style={{
                        background: `linear-gradient(135deg, ${agent.color}, ${agent.color}dd)`,
                      }}
                    >
                      <span className="text-[10px]">{agent.icon}</span>
                    </div>
                    <span className="flex items-center gap-1.5 text-[9px] font-mono uppercase tracking-wider text-[#a3b899] bg-[#a3b899]/5 px-2 py-0.5 rounded border border-[#a3b899]/20">
                      <span className="w-1.5 h-1.5 bg-[#a3b899] rounded-full animate-pulse" />
                      READY
                    </span>
                  </div>
                  <h3 className="font-sans font-semibold text-sm text-foreground mb-0.5">{agent.name} Specialist</h3>
                  <p className="text-[9px] font-mono text-primary uppercase tracking-widest mb-3">{agent.role}</p>
                  <p className="text-xs text-muted-foreground/90 leading-relaxed mb-4">{desc}</p>
                </div>

                <div className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground/70 border-t border-border/30 pt-3.5 flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <Bot className="w-3.5 h-3.5 text-primary/80" />
                    <span>SYS_CORE</span>
                  </span>
                  <Link
                    href={`/chat?agent=${agent.id.toLowerCase()}`}
                    className="px-2.5 py-1 border border-primary/25 hover:border-primary/50 text-primary bg-primary/5 hover:bg-primary hover:text-primary-foreground rounded transition-all duration-300 font-mono text-[9px] uppercase tracking-wider flex items-center gap-1"
                  >
                    <span>Deploy</span>
                    <Sparkles className="w-2.5 h-2.5" />
                  </Link>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
