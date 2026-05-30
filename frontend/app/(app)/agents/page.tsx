"use client"

import { AGENTS } from "@/lib/constants/agents"
import { Bot, Sparkles, Network } from "lucide-react"

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
    <div className="flex-grow overflow-y-auto px-8 py-8 bg-background">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-semibold text-foreground">Agent Network</h1>
          </div>
          <p className="text-sm text-muted-foreground">
            Specialist AI agents collaborate under Nexus CMO to analyze data and recommend strategic campaign actions.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.values(AGENTS).map((agent) => {
            const desc = AGENT_DESCRIPTIONS[agent.id.toLowerCase()] || "Specialist AI marketing assistant ready to execute campaigns."
            return (
              <div
                key={agent.id}
                className="bg-card border border-border rounded-xl p-5 hover:border-primary/40 transition cursor-pointer group flex flex-col justify-between shadow-sm"
                style={{
                  background: `linear-gradient(180deg, ${agent.color}08 0%, transparent 100%)`,
                }}
              >
                <div>
                  <div className="flex items-start justify-between mb-4">
                    <div
                      className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-base font-bold transition-transform group-hover:scale-110 shadow-sm"
                      style={{
                        background: `linear-gradient(135deg, ${agent.color}, ${agent.color}99)`,
                      }}
                    >
                      {agent.icon}
                    </div>
                    <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <span className="w-1 h-1 bg-emerald-400 rounded-full animate-pulse" />
                      Idle · Ready
                    </span>
                  </div>
                  <h3 className="font-semibold text-sm mb-0.5 text-foreground">{agent.name} Specialist</h3>
                  <p className="text-[11px] font-medium text-primary mb-3 uppercase tracking-wider">{agent.role}</p>
                  <p className="text-xs text-muted-foreground leading-relaxed mb-4">{desc}</p>
                </div>

                <div className="text-[10px] text-muted-foreground/60 border-t border-border/50 pt-3 flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <Bot className="w-3.5 h-3.5 text-primary/80" />
                    Model: OpenRouter Claude/GPT
                  </span>
                  <span className="flex items-center gap-1 font-semibold text-primary group-hover:underline">
                    Deploy <Sparkles className="w-2.5 h-2.5" />
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
