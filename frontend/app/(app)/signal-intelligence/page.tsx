"use client"

import React, { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { listSignals, triggerScan } from "@/lib/api"
import type { Signal } from "@/lib/api"
import { 
  Radio, 
  RefreshCw, 
  TrendingUp, 
  AlertTriangle, 
  ShieldAlert, 
  HelpCircle, 
  Eye, 
  Sparkles,
  ArrowRight,
  ChevronRight,
  ShieldCheck,
  Search,
  CheckCircle2,
  FileText,
  X
} from "lucide-react"
import { cn } from "@/lib/utils"
import { WelcomeOnboarding } from "@/components/shared/WelcomeOnboarding"

export default function SignalIntelligencePage() {
  const router = useRouter()
  const { projects, activeProject, loading: projectsLoading } = useActiveProject()
  
  const [signals, setSignals] = useState<Signal[]>([])
  const [dataLoading, setDataLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [activeTab, setActiveTab] = useState<"all" | "seo" | "aeo" | "analytics" | "cro">("all")
  
  // Drawer states
  const [selectedSignal, setSelectedSignal] = useState<Signal | null>(null)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const projectId = activeProject?.id

  const loadSignals = useCallback(async () => {
    if (!projectId) {
      setSignals([])
      setDataLoading(false)
      return
    }
    setDataLoading(true)
    try {
      const res = await listSignals("active", projectId)
      setSignals(res.signals || [])
    } catch (e) {
      console.error("Failed to load signals:", e)
    } finally {
      setDataLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadSignals()
  }, [loadSignals])

  const handleScan = useCallback(async () => {
    if (!projectId) return
    setScanning(true)
    try {
      await triggerScan(projectId)
      await loadSignals()
    } catch (e) {
      console.error("Scan trigger failed:", e)
    } finally {
      setScanning(false)
    }
  }, [projectId, loadSignals])

  const loading = projectsLoading || dataLoading

  const filteredSignals = signals.filter(s => {
    if (activeTab === "all") return true
    if (activeTab === "seo") return s.category.toLowerCase() === "seo"
    if (activeTab === "aeo") return s.category.toLowerCase() === "aeo"
    if (activeTab === "analytics") return s.category.toLowerCase() === "analytics"
    if (activeTab === "cro") return s.category.toLowerCase() === "cro"
    return true
  })

  // Group signals by priority
  const criticalSignals = signals.filter(s => s.severity.toLowerCase() === "critical")
  const highSignals = signals.filter(s => s.severity.toLowerCase() === "high")
  const mediumSignals = signals.filter(s => s.severity.toLowerCase() === "medium" || s.severity.toLowerCase() === "medium_low")
  const lowSignals = signals.filter(s => s.severity.toLowerCase() === "low")

  if (loading && signals.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-5 h-5 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Demodulating signal logs...</div>
        </div>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="flex-grow flex items-center justify-center bg-background">
        <WelcomeOnboarding />
      </div>
    )
  }

  return (
    <div className="flex-grow flex h-full overflow-hidden bg-background text-foreground animate-fade-in relative">
      
      {/* Left panel: Signal Grid */}
      <div className="flex-grow overflow-y-auto px-8 py-6 flex flex-col h-full bg-background relative z-10">
        
        {/* Page Header */}
        <div className="mb-6 flex items-center justify-between border-b border-border/60 pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Radio className="w-5 h-5 text-primary" />
              <h1 className="text-2xl md:text-3xl font-serif font-normal tracking-tight text-foreground">
                Signal Intelligence
              </h1>
            </div>
            <p className="text-xs text-muted-foreground max-w-xl">
              Real-time vulnerability mapping, search index readiness tracker, and optimization opportunities.
            </p>
          </div>
          
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition-all duration-300 disabled:opacity-50 shadow-md border border-primary/20"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", scanning && "animate-spin")} />
            <span>{scanning ? "Scanning Core..." : "Scan Workspace"}</span>
          </button>
        </div>

        {/* Workspace Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="glass-panel rounded-xl p-4.5 flex flex-col justify-between shadow-md">
            <span className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest">Active Signals</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-2xl font-serif font-semibold text-foreground">{signals.length}</span>
              <span className="text-[10px] font-mono text-primary bg-primary/10 border border-primary/20 px-2 py-0.5 rounded">MONITORED</span>
            </div>
          </div>
          <div className="glass-panel rounded-xl p-4.5 flex flex-col justify-between shadow-md">
            <span className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest">Critical Alert Vector</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-2xl font-serif font-semibold text-destructive">{criticalSignals.length}</span>
              <span className="text-[10px] font-mono text-destructive bg-destructive/10 border border-destructive/20 px-2 py-0.5 rounded">VULNERABLE</span>
            </div>
          </div>
          <div className="glass-panel rounded-xl p-4.5 flex flex-col justify-between shadow-md">
            <span className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest">High Severity Alerts</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-2xl font-serif font-semibold text-amber-500">{highSignals.length}</span>
              <span className="text-[10px] font-mono text-amber-500 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded">RESOLVE_NOW</span>
            </div>
          </div>
          <div className="glass-panel rounded-xl p-4.5 flex flex-col justify-between shadow-md">
            <span className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest">Telemetry Scans Run</span>
            <div className="flex items-baseline justify-between mt-2">
              <span className="text-2xl font-serif font-semibold text-emerald-400">12</span>
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded">SECURE</span>
            </div>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex border-b border-border/60 mb-5 text-xs font-mono uppercase tracking-wider gap-6">
          {(["all", "seo", "aeo", "analytics", "cro"] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={cn(
                "pb-2 border-b-2 transition duration-200 relative",
                activeTab === tab 
                  ? "border-primary text-foreground font-bold" 
                  : "border-transparent text-muted-foreground hover:text-foreground"
              )}
            >
              {tab === "all" ? "All Vectors" : tab}
              {activeTab === tab && (
                <span className="absolute bottom-0 left-0 right-0 h-[2px] bg-primary shadow-[0_0_10px_#3b82f6]" />
              )}
            </button>
          ))}
        </div>

        {/* Signal Cards Grid */}
        {filteredSignals.length === 0 ? (
          <div className="glass-panel rounded-xl p-10 text-center max-w-md mx-auto mt-6 shadow-md">
            <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto mb-4 animate-pulse" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground mb-1">System Vector Secure</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              No active signals detected in this category. Run a fresh scan to audit website telemetry indicators.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredSignals.map(s => {
              const isCritical = s.severity.toLowerCase() === "critical"
              const isHigh = s.severity.toLowerCase() === "high"
              
              return (
                <div
                  key={s.id}
                  onClick={() => {
                    setSelectedSignal(s)
                    setDrawerOpen(true)
                  }}
                  className="glass-panel glass-panel-hover rounded-xl p-5 cursor-pointer flex flex-col justify-between"
                >
                  <div>
                    {/* Header: Category and Severity badge */}
                    <div className="flex items-center justify-between mb-3 border-b border-border/40 pb-2.5">
                      <span className="px-2 py-0.5 bg-primary/10 border border-primary/20 text-primary text-[8px] font-mono uppercase tracking-widest rounded">
                        {s.category}
                      </span>
                      <span className={cn(
                        "text-[8px] font-mono px-2 py-0.5 rounded border uppercase tracking-wider",
                        isCritical 
                          ? "bg-destructive/10 border-destructive/20 text-destructive glow-destructive"
                          : isHigh
                            ? "bg-amber-500/10 border-amber-500/20 text-amber-500"
                            : "bg-muted border-border/80 text-muted-foreground"
                      )}>
                        {s.severity.replace("_", " ")}
                      </span>
                    </div>

                    <h3 className="text-sm font-semibold text-foreground mb-1.5 leading-snug group-hover:text-primary transition duration-300">
                      {s.title}
                    </h3>
                    <p className="text-xs text-muted-foreground/80 leading-relaxed truncate max-w-full">
                      {s.description}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-[9px] font-mono uppercase tracking-wider text-muted-foreground/50 border-t border-border/30 pt-3.5 mt-4">
                    <span>DETECTOR: {s.source_agent || "seo"}</span>
                    <span className="flex items-center gap-1 text-primary">
                      <span>Investigate</span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Right panel: Radar and Signal Map */}
      <div className="w-[340px] border-l border-border/80 bg-background/25 flex flex-col h-full flex-shrink-0 z-10 relative overflow-hidden select-none">
        
        {/* Grid Background Effect */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.005)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.005)_1px,transparent_1px)] bg-[size:16px_16px] pointer-events-none opacity-50 animate-grid-glow" />
        
        <div className="p-4 border-b border-border/60 z-10">
          <h2 className="font-mono text-[10px] text-primary/80 uppercase tracking-widest flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            Signal Radar Scope
          </h2>
        </div>

        {/* Animated Signal Radar Graphic */}
        <div className="flex-grow flex items-center justify-center p-6 relative">
          <div className="w-60 h-60 rounded-full border border-border/40 relative flex items-center justify-center shadow-lg">
            {/* Concentric rings */}
            <div className="absolute w-44 h-44 rounded-full border border-border/30" />
            <div className="absolute w-28 h-28 rounded-full border border-border/20" />
            <div className="absolute w-12 h-12 rounded-full border border-border/10" />
            
            {/* Crosshairs */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="h-full w-[1px] bg-border/20" />
              <div className="w-full h-[1px] bg-border/20" />
            </div>

            {/* Radar Sweeper */}
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-primary/0 via-primary/5 to-primary/25 origin-center animate-radar-sweep pointer-events-none" />

            {/* Mock signal nodes mapped dynamically on radar */}
            {signals.map((sig, idx) => {
              const angles = [35, 110, 215, 290, 160, 340, 75, 250]
              const radius = [40, 75, 100, 60, 90, 115, 80, 50]
              const angle = angles[idx % angles.length]
              const rad = radius[idx % radius.length]
              
              const x = 120 + rad * Math.cos(angle * Math.PI / 180)
              const y = 120 + rad * Math.sin(angle * Math.PI / 180)

              return (
                <div 
                  key={sig.id}
                  className={cn(
                    "absolute w-2.5 h-2.5 rounded-full border-2 border-background cursor-pointer hover:scale-125 transition duration-300",
                    sig.severity.toLowerCase() === "critical"
                      ? "bg-destructive glow-destructive"
                      : sig.severity.toLowerCase() === "high"
                        ? "bg-amber-500"
                        : "bg-primary glow-blue"
                  )}
                  style={{
                    left: `${x - 5}px`,
                    top: `${y - 5}px`,
                  }}
                  title={sig.title}
                  onClick={() => {
                    setSelectedSignal(sig)
                    setDrawerOpen(true)
                  }}
                />
              )
            })}
          </div>
        </div>

        {/* Radar Map Details Legend */}
        <div className="p-4.5 border-t border-border/60 bg-[#08080f]/40 font-mono text-[9px] text-muted-foreground/60 space-y-2.5">
          <div className="flex items-center justify-between">
            <span>TOTAL VECTORS MONITOR</span>
            <span className="text-foreground font-bold">{signals.length}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-destructive" />
              CRITICAL VECTORS
            </span>
            <span className="text-destructive font-bold">{criticalSignals.length}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-500" />
              HIGH ALERT VECTORS
            </span>
            <span className="text-amber-500 font-bold">{highSignals.length}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-primary" />
              MEDIUM/LOW VECTORS
            </span>
            <span className="text-primary font-bold">{mediumSignals.length + lowSignals.length}</span>
          </div>
        </div>

      </div>

      {/* 5. Slide-out Evidence / Detail Drawer */}
      {drawerOpen && selectedSignal && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-[2px]">
          <div className="absolute inset-0" onClick={() => setDrawerOpen(false)} />
          <div className="glass-panel border-l border-primary/20 w-[460px] h-full flex flex-col relative z-10 shadow-2xl animate-slide-up">
            
            {/* Drawer Header */}
            <div className="p-5 border-b border-border/80 flex items-center justify-between bg-primary/5">
              <div className="flex items-center gap-2">
                <Radio className="w-4.5 h-4.5 text-primary" />
                <span className="text-xs font-semibold tracking-wide text-foreground uppercase">Signal Diagnostics</span>
              </div>
              <button 
                onClick={() => setDrawerOpen(false)}
                className="p-1 text-muted-foreground hover:text-foreground hover:bg-muted/40 rounded transition"
              >
                <X className="w-4.5 h-4.5" />
              </button>
            </div>

            {/* Drawer Content Scroll */}
            <div className="flex-grow overflow-y-auto p-6 space-y-6">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="px-2 py-0.5 bg-primary/10 border border-primary/20 text-primary text-[8px] font-mono uppercase tracking-widest rounded">
                    {selectedSignal.category}
                  </span>
                  <span className="text-[10px] font-mono text-muted-foreground/60">CONFIDENCE: 95%</span>
                </div>
                
                <h2 className="text-xl font-serif text-foreground leading-snug font-normal">
                  {selectedSignal.title}
                </h2>
                
                <p className="text-xs text-muted-foreground/80 mt-2.5 leading-relaxed font-sans">
                  {selectedSignal.description}
                </p>
              </div>

              {/* Severity Priority details */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-[#0c0c16]/50 border border-border/60 rounded-lg p-3">
                  <span className="text-[8px] font-mono text-muted-foreground/60 uppercase">SEVERITY TYPE</span>
                  <span className="block text-sm font-semibold text-foreground mt-1 capitalize">{selectedSignal.severity.replace("_", " ")}</span>
                </div>
                <div className="bg-[#0c0c16]/50 border border-border/60 rounded-lg p-3">
                  <span className="text-[8px] font-mono text-muted-foreground/60 uppercase">DETECTION SOURCE</span>
                  <span className="block text-sm font-semibold text-primary mt-1 uppercase font-mono">{selectedSignal.source_agent || "seo"} specialist</span>
                </div>
              </div>

              {/* Why It Matters */}
              <div className="space-y-2">
                <h3 className="font-mono text-[9px] uppercase tracking-widest text-primary">Why It Matters</h3>
                <p className="text-xs text-muted-foreground/85 leading-relaxed font-sans">
                  {selectedSignal.category.toLowerCase() === "seo" 
                    ? "Resolving crawl blockers or missing descriptors helps ensure index readability and avoids resource budget limits on standard web crawlers."
                    : "Entity metadata helps ensure search index bots and machine algorithms accurately synthesize your brand's structure and author identity."}
                </p>
              </div>

              {/* Evidence list details */}
              {selectedSignal.evidence && selectedSignal.evidence.length > 0 && (
                <div className="space-y-2.5">
                  <h3 className="font-mono text-[9px] uppercase tracking-widest text-primary">Evidence Telemetry</h3>
                  <div className="bg-[#040409]/60 border border-border/60 rounded-lg p-4 font-mono text-[10px] text-accent space-y-1 shadow-inner">
                    {Array.isArray(selectedSignal.evidence) ? (
                      (selectedSignal.evidence as any[]).map((item, idx) => {
                        const displayText = typeof item === "object" && item !== null
                          ? `${item.claim || ""} [Source: ${item.source || "inferred"}]`
                          : String(item);
                        return (
                          <div key={idx} className="leading-relaxed">
                            {displayText}
                          </div>
                        )
                      })
                    ) : (
                      <div className="leading-relaxed">{String(selectedSignal.evidence)}</div>
                    )}
                  </div>
                </div>
              )}

              {/* Recommended Action */}
              <div className="space-y-2">
                <h3 className="font-mono text-[9px] uppercase tracking-widest text-primary">Recommended Action</h3>
                <div className="bg-primary/5 border border-primary/20 rounded-lg p-4 text-xs leading-relaxed text-foreground/90 font-sans flex items-start gap-3.5">
                  <Sparkles className="w-4.5 h-4.5 text-primary flex-shrink-0 mt-0.5" />
                  <p>{selectedSignal.category.toLowerCase() === "seo" 
                    ? "Establish strict configuration protocols. Define user-agent rules and index pathways using structured tags." 
                    : "Add explicit JSON-LD schema parameters in page templates to support crawl semantic processing."}</p>
                </div>
              </div>
            </div>

            {/* Bottom Actions CTA */}
            <div className="p-4 border-t border-border/80 bg-[#08080f]/40 flex gap-2.5 justify-end">
              <button 
                onClick={() => setDrawerOpen(false)}
                className="px-4 py-2 border border-border rounded-lg text-xs hover:bg-muted/30 transition text-muted-foreground hover:text-foreground"
              >
                Close View
              </button>
              <button 
                onClick={() => {
                  setDrawerOpen(false)
                  router.push(`/chat?signal=${selectedSignal.id}`)
                }}
                className="px-4.5 py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition-all duration-300 shadow-md border border-primary/20 flex items-center gap-1.5"
              >
                <span>Initiate Swarm Boardroom</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>

          </div>
        </div>
      )}

    </div>
  )
}
