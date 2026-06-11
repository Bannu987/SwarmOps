"use client"

import React, { useState, useEffect } from "react"
import Link from "next/link"
import { 
  Bot, 
  Compass, 
  Radio, 
  Users, 
  ClipboardList, 
  Activity, 
  ShieldCheck, 
  Sparkles,
  ArrowRight,
  ChevronRight,
  TrendingUp,
  Cpu,
  Globe
} from "lucide-react"
import { cn } from "@/lib/utils"

export default function LandingPage() {
  const [radarNodes, setRadarNodes] = useState<Array<{ x: number; y: number; color: string; size: string }>>([])

  // Generate random radar nodes on mount
  useEffect(() => {
    setRadarNodes([
      { x: 75, y: 80, color: "bg-destructive glow-destructive", size: "w-2.5 h-2.5" },
      { x: 180, y: 110, color: "bg-primary glow-blue", size: "w-2 h-2" },
      { x: 110, y: 200, color: "bg-accent glow-cyan", size: "w-2 h-2" },
      { x: 140, y: 150, color: "bg-amber-500", size: "w-1.5 h-1.5" },
      { x: 220, y: 60, color: "bg-emerald-400 glow-emerald", size: "w-2.5 h-2.5" }
    ])
  }, [])

  const agents = [
    { name: "Nexus", role: "CMO Orchestrator", desc: "Coordinates swarm debates and consolidates strategy.", color: "#6366f1", icon: "🧠" },
    { name: "SEO Specialist", role: "Organic Visibility", desc: "Audits search visibility and technical indexing.", color: "#06b6d4", icon: "🔍" },
    { name: "AEO Specialist", role: "AI Search Indexing", desc: "Secures brand mentions in LLM answer engines.", color: "#fbbf24", icon: "🤖" },
    { name: "Content Specialist", role: "Strategic Copywriter", desc: "Drafts highly-optimized ad briefs and emails.", color: "#a855f7", icon: "✍️" },
    { name: "Analytics Specialist", role: "Conversion Funnels", desc: "Monitors traffic trends and channel attribution.", color: "#10b981", icon: "📊" },
    { name: "CRO Specialist", role: "Friction Auditor", desc: "Resolves signup leaks and designs A/B tests.", color: "#22c55e", icon: "🎯" }
  ]

  return (
    <div className="min-h-screen flex flex-col bg-[#020205] text-foreground selection:bg-primary/30 relative overflow-x-hidden">
      
      {/* Radial lighting glow spots */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[350px] bg-gradient-to-b from-primary/10 to-transparent blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute top-1/3 left-10 w-[400px] h-[400px] bg-accent/5 blur-[100px] rounded-full pointer-events-none" />
      <div className="absolute bottom-10 right-10 w-[500px] h-[500px] bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none" />

      {/* Grid Pattern overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.003)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.003)_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none opacity-40" />

      {/* Top Navbar */}
      <nav className="border-b border-border/40 backdrop-blur-md bg-[#020205]/40 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-6.5 h-6.5 rounded bg-gradient-to-br from-primary to-accent flex items-center justify-center text-primary-foreground text-xs font-black shadow-md glow-blue">
              S
            </div>
            <span className="text-xs font-black tracking-widest uppercase text-foreground">
              Swarm<span className="text-primary font-light">Ops</span>
            </span>
          </div>
          
          <div className="flex items-center gap-5">
            <Link
              href="/login"
              className="text-xs font-mono uppercase tracking-wider text-muted-foreground hover:text-foreground transition"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="px-4 py-2 bg-primary hover:bg-primary/95 text-primary-foreground text-[10px] font-mono uppercase tracking-wider rounded-lg transition shadow-md border border-primary/20"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="flex-grow flex flex-col justify-center px-6 py-16 md:py-24 max-w-6xl mx-auto w-full z-10 space-y-20">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Hero Left: Text */}
          <div className="lg:col-span-7 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 border border-primary/20 rounded-full text-[10px] font-mono uppercase tracking-wider text-primary animate-pulse-slow">
              <Sparkles className="w-3 h-3" />
              Autonomous Swarm Marketing
            </div>

            <h1 className="text-4xl md:text-6xl font-serif font-normal tracking-tight text-foreground leading-[1.08] mb-4">
              Your autonomous 
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-primary via-accent to-indigo-400 font-sans font-black">
                marketing boardroom.
              </span>
            </h1>

            <p className="text-sm md:text-base text-muted-foreground/90 leading-relaxed max-w-xl">
              SwarmOps deploys a specialized swarm of 6 AI marketing agents that crawl telemetry, debate solutions under Nexus CMO, and execute verified actions.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Link
                href="/signup"
                className="px-6 py-3 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition shadow-lg border border-primary/20 flex items-center justify-center gap-1.5"
              >
                <span>Deploy Swarm Cotes</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
              <Link
                href="/login"
                className="px-6 py-3 bg-card border border-border hover:border-primary/30 hover:bg-muted/30 text-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition shadow-sm flex items-center justify-center gap-1.5"
              >
                <span>Access Command Deck</span>
              </Link>
            </div>
          </div>

          {/* Hero Right: Signal Radar Preview */}
          <div className="lg:col-span-5 flex justify-center relative">
            <div className="w-72 h-72 rounded-full border border-border/40 relative flex items-center justify-center shadow-2xl bg-[#04040a]/40 backdrop-blur-sm">
              {/* Concentric rings */}
              <div className="absolute w-52 h-52 rounded-full border border-border/30" />
              <div className="absolute w-32 h-32 rounded-full border border-border/20" />
              
              {/* Crosshairs */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="h-full w-[1px] bg-border/25" />
                <div className="w-full h-[1px] bg-border/25" />
              </div>

              {/* Radar Sweeper */}
              <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-primary/0 via-primary/5 to-primary/25 origin-center animate-radar-sweep pointer-events-none" />

              {/* Radar Nodes */}
              {radarNodes.map((node, idx) => (
                <div 
                  key={idx}
                  className={cn(
                    "absolute rounded-full border border-background animate-pulse-slow",
                    node.color,
                    node.size
                  )}
                  style={{
                    left: `${node.x}px`,
                    top: `${node.y}px`,
                  }}
                />
              ))}

              <div className="absolute bottom-5 flex flex-col items-center">
                <span className="text-[8px] font-mono text-accent tracking-widest uppercase">SCANNING_WORKSPACE</span>
                <span className="text-[10px] font-serif text-foreground mt-0.5">https://yourbrand.com</span>
              </div>
            </div>
          </div>

        </div>

        {/* Operating Boardroom Agent Cards */}
        <div className="space-y-6">
          <div className="text-center max-w-lg mx-auto">
            <span className="text-[9px] font-mono text-primary uppercase tracking-widest block mb-2">BOARDROOM AGENTS</span>
            <h2 className="text-2xl md:text-3xl font-serif font-normal text-foreground tracking-tight">
              Specialized Marketing Minds
            </h2>
            <p className="text-xs text-muted-foreground mt-1.5 leading-relaxed">
              Every agent plays a dedicated strategic role inside the swarm, analyzing telemetry and collaborating to reach consensus.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className="glass-panel glass-panel-hover rounded-xl p-5 flex flex-col justify-between"
                style={{
                  background: `linear-gradient(180deg, ${agent.color}08 0%, transparent 100%)`,
                }}
              >
                <div>
                  <div className="flex items-center justify-between mb-4 border-b border-border/30 pb-3">
                    <span className="w-8 h-8 rounded bg-background border border-border flex items-center justify-center text-sm shadow-inner">
                      {agent.icon}
                    </span>
                    <span className="text-[8px] font-mono uppercase tracking-wider bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded flex items-center gap-1">
                      <span className="w-1.25 h-1.25 bg-emerald-500 rounded-full animate-pulse" />
                      ACTIVE
                    </span>
                  </div>

                  <h3 className="font-sans font-semibold text-sm text-foreground mb-0.5">{agent.name}</h3>
                  <p className="text-[9px] font-mono text-primary uppercase tracking-widest mb-3">{agent.role}</p>
                  <p className="text-xs text-muted-foreground/80 leading-relaxed font-sans">{agent.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Core Product Trust Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 border-t border-border/50 pt-16">
          <div className="space-y-2">
            <Cpu className="w-6 h-6 text-primary" />
            <h4 className="text-sm font-semibold text-foreground uppercase tracking-wider">Multi-Agent Debate</h4>
            <p className="text-xs text-muted-foreground/85 leading-relaxed font-sans">
              Agents review signal telemetry from different perspectives (SEO, AEO, CRO), raising arguments and counter-recommendations.
            </p>
          </div>
          <div className="space-y-2">
            <ShieldCheck className="w-6 h-6 text-primary" />
            <h4 className="text-sm font-semibold text-foreground uppercase tracking-wider">Evidence-Backed Consensus</h4>
            <p className="text-xs text-muted-foreground/85 leading-relaxed font-sans">
              Decisions must meet strict consensus criteria. No recommendation is generated without linked code citations or DOM telemetry.
            </p>
          </div>
          <div className="space-y-2">
            <ClipboardList className="w-6 h-6 text-primary" />
            <h4 className="text-sm font-semibold text-foreground uppercase tracking-wider">Operations & Verification</h4>
            <p className="text-xs text-muted-foreground/85 leading-relaxed font-sans">
              Once approved, strategy compiles into checklist action items. The crawler safety system rechecks the URL to verify resolution.
            </p>
          </div>
        </div>

      </main>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8 bg-[#020205]/60 text-center text-[10px] font-mono text-muted-foreground/60 z-10 flex items-center justify-center gap-2">
        <span>SwarmOps v2.0</span>
        <span>·</span>
        <span>The Boardroom of marketing operations</span>
      </footer>

    </div>
  )
}
