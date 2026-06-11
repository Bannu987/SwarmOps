"use client"

import { AGENTS } from "@/lib/constants/agents"
import { Bot, Sparkles, Cpu, Clock, Zap } from "lucide-react"
import Link from "next/link"

const AGENT_DESCRIPTIONS: Record<string, string> = {
  nexus: "Orchestrates the swarm debate, consolidates findings, guarantees brand alignment, and serves as the strategic chief marketing officer.",
  seo: "Audits search visibility, identifies organic keyword gaps, tracks competitors' search footprints, and monitors technical crawl and index issues.",
  content: "Maps content strategies, identifies content decay in articles, outlines search-optimized briefs, and drafts high-converting copy.",
  analytics: "Detects traffic anomalies, visualizes conversion funnels, and aggregates cross-platform audience attribution trends.",
  cro: "Pinpoints leaks in signups and checkouts, maps layout friction audits, and outlines A/B testing ideas to lift conversions.",
  aeo: "Optimizes brand mentions for Answer Engine Optimization (Perplexity, ChatGPT, Gemini) to secure visibility in AI-generated answers."
}

const AGENT_TECHNICAL_META: Record<string, { model: string, capabilities: string[], stance: string, latency: string }> = {
  nexus: {
    model: "Nexus-v2.5 (Supervisor Core)",
    capabilities: ["Consensus Arbitration", "Strategic Routing", "Brand Tone Compliance"],
    stance: "Consensus Arbiter",
    latency: "1.8s avg"
  },
  seo: {
    model: "SEO-Crawler-v1.8",
    capabilities: ["Indexability Scanning", "Keyword Auditing", "Sitemap Verification"],
    stance: "Strict Search Guarded",
    latency: "1.1s avg"
  },
  content: {
    model: "Copy-Synthesis-v1.9",
    capabilities: ["Brief Optimization", "Keyword Density", "CTR Copywriting"],
    stance: "Creative & Audience-Centric",
    latency: "1.4s avg"
  },
  analytics: {
    model: "Analytics-Deep-v2.0",
    capabilities: ["Funnel Tracking", "Anomaly Detection", "Attribution Modeling"],
    stance: "Purely Quantitative",
    latency: "0.8s avg"
  },
  cro: {
    model: "CRO-Friction-v1.6",
    capabilities: ["Friction Mapping", "CTA Efficiency Audit", "A/B Test Ideation"],
    stance: "Conversion-Focused",
    latency: "1.2s avg"
  },
  aeo: {
    model: "Entity-AEO-v1.4",
    capabilities: ["LLM Retrieval Scan", "Entity Citation Prep", "Perplexity Visibility"],
    stance: "Semantic Optimizing",
    latency: "1.3s avg"
  }
}

export default function AgentsPage() {
  return (
    <div className="flex-grow overflow-y-auto px-8 py-8 bg-transparent animate-fade-in text-white">
      <div className="max-w-6xl mx-auto">
        
        {/* Header */}
        <div className="mb-8 border-b border-white/5 pb-5">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl md:text-2xl font-serif font-normal tracking-tight text-white">
              Agent Network
            </h1>
            <span className="text-[9px] font-mono text-primary bg-primary/10 border border-primary/25 px-2 py-0.5 rounded-full uppercase tracking-wider">
              Coordinated Swarm
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1 max-w-2xl leading-relaxed">
            Specialist machine intelligence cores collaborate under the Nexus supervisor to audit marketing telemetry, generate campaign checklists, and execute strategies.
          </p>
        </div>

        {/* Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {Object.values(AGENTS).map((agent) => {
            const desc = AGENT_DESCRIPTIONS[agent.id.toLowerCase()] || "Specialist AI marketing assistant ready to execute campaigns."
            const meta = AGENT_TECHNICAL_META[agent.id.toLowerCase()] || {
              model: "Specialist-v1.0",
              capabilities: ["Context Sync", "Strategy Audit"],
              stance: "Data-Driven",
              latency: "1.0s avg"
            }

            return (
              <div
                key={agent.id}
                className="glass-panel border border-white/5 rounded-xl p-5 hover:border-white/10 hover:bg-white/[0.02] transition-all duration-300 flex flex-col justify-between shadow-lg relative group"
                style={{
                  borderTop: `2px solid ${agent.color}40`
                }}
              >
                <div>
                  {/* Top Bar */}
                  <div className="flex items-center justify-between mb-4 border-b border-white/5 pb-3">
                    <div className="flex items-center gap-2">
                      <div
                        className="w-6 h-6 rounded flex items-center justify-center text-black text-xs font-bold transition-transform group-hover:scale-105 shadow-sm"
                        style={{
                          background: `linear-gradient(135deg, ${agent.color}, ${agent.color}dd)`,
                        }}
                      >
                        <span className="text-[10px]">{agent.icon}</span>
                      </div>
                      <h3 className="font-sans font-semibold text-xs text-white">{agent.name} specialist</h3>
                    </div>
                    
                    <span className="flex items-center gap-1 text-[8px] font-mono uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                      <span className="w-1 h-1 bg-emerald-400 rounded-full animate-pulse" />
                      ACTIVE
                    </span>
                  </div>

                  {/* Stance and Description */}
                  <div className="space-y-3 mb-5">
                    <div className="text-[9px] font-mono text-primary uppercase tracking-widest">{agent.role}</div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{desc}</p>
                  </div>

                  {/* Technical Parameters */}
                  <div className="bg-white/[0.01] border border-white/5 rounded-lg p-3 space-y-2 mb-5 font-mono text-[9px] text-muted-foreground">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground/60 flex items-center gap-1"><Cpu className="w-3 h-3 text-muted-foreground/40" /> MODEL</span>
                      <span className="text-white/95 font-medium">{meta.model}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground/60 flex items-center gap-1"><Clock className="w-3 h-3 text-muted-foreground/40" /> LATENCY</span>
                      <span className="text-white/95 font-medium">{meta.latency}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground/60 flex items-center gap-1"><Zap className="w-3 h-3 text-muted-foreground/40" /> DEBATE STANCE</span>
                      <span className="text-white/95 font-medium">{meta.stance}</span>
                    </div>
                    <div className="border-t border-white/5 pt-2 mt-1 space-y-1">
                      <div className="text-muted-foreground/40 text-[8px] uppercase tracking-wider">CORE CAPABILITIES</div>
                      <ul className="list-disc list-inside space-y-0.5 pl-1 text-[9px] text-white/80">
                        {meta.capabilities.map((cap, idx) => (
                          <li key={idx} className="truncate">{cap}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>

                {/* Footer Link */}
                <div className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground border-t border-white/5 pt-3.5 flex items-center justify-between">
                  <span className="flex items-center gap-1">
                    <span>PORTAL AP_x0{agent.id.toUpperCase()}</span>
                  </span>
                  <Link
                    href={`/chat?agent=${agent.id.toLowerCase()}`}
                    className="px-3 py-1 border border-white/10 hover:border-white/25 hover:bg-white/5 text-white rounded-lg transition-all duration-300 font-mono text-[9px] uppercase tracking-wider flex items-center gap-1"
                  >
                    <span>Initialize</span>
                    <Sparkles className="w-2.5 h-2.5 text-primary animate-pulse" />
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
