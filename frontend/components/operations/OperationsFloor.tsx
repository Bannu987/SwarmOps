"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { listSignals, listOpportunities, triggerScan } from "@/lib/api"
import type { Signal, Opportunity } from "@/lib/api"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { Column } from "./Column"
import { OpportunityCard } from "./OpportunityCard"
import { SignalCard } from "./SignalCard"
import { ActiveWorkCard, type ActiveWorkItem } from "./ActiveWorkCard"
import { PulseBar } from "./PulseBar"
import { EmptyOperationsState } from "./EmptyOperationsState"
import { RefreshCw, MessageSquarePlus } from "lucide-react"
import Link from "next/link"
import { WelcomeOnboarding } from "@/components/shared/WelcomeOnboarding"
import { AnimatedTabs, RevealPanel, ScanlineSkeleton } from "@/components/shared/MotionPrimitives"


export function OperationsFloor() {
  const router = useRouter()

  const {
    projects,
    activeProject,
    loading: projectsLoading,
    selectProject,
  } = useActiveProject()

  const [signals, setSignals] = useState<Signal[]>([])
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [activeWork, setActiveWork] = useState<ActiveWorkItem[]>([])
  const [dataLoading, setDataLoading] = useState(true)
  const [scanning, setScanning] = useState(false)

  const loadData = useCallback(async () => {
    if (!activeProject) {
      setSignals([])
      setOpportunities([])
      setDataLoading(false)
      return
    }
    try {
      const [signalsRes, oppsRes] = await Promise.all([
        listSignals("active", activeProject.id),
        listOpportunities("active", activeProject.id),
      ])
      setSignals(signalsRes.signals || [])
      setOpportunities(oppsRes.opportunities || [])
    } catch (e) {
      console.error("Failed to load operations data:", e)
    } finally {
      setDataLoading(false)
    }
  }, [activeProject])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 60000)
    return () => clearInterval(interval)
  }, [loadData])

  const handleScan = async () => {
    if (!activeProject) return
    setScanning(true)

    setActiveWork([
      { id: "scan-1", agentId: "seo", task: "Scanning site for issues", status: "thinking", progress: 30 },
    ])

    try {
      await triggerScan(activeProject.id)
      await loadData()
    } catch (e) {
      console.error("Scan failed:", e)
    } finally {
      setScanning(false)
      setActiveWork([])
    }
  }

  const loading = projectsLoading || dataLoading

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-5 h-5 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground">Loading operations floor...</div>
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

  if (signals.length === 0 && opportunities.length === 0 && activeWork.length === 0) {
    return <EmptyOperationsState hasProject={true} onTriggerScan={handleScan} scanning={scanning} />
  }

  const pulseActivities = signals.slice(0, 4).map((s) => ({
    agent: s.source_agent,
    action: `detected ${s.title.toLowerCase().substring(0, 40)}`,
  }))

  const unseen = signals.filter((s) => !s.seen).length

  const [activeTab, setActiveTab] = useState("overview")
  const [selectedItem, setSelectedItem] = useState<{ type: "opportunity" | "signal"; data: any } | null>(null)

  const tabs = [
    { id: "overview", label: "[ALL_DECK]" },
    { id: "opportunities", label: "[OPPORTUNITIES]" },
    { id: "signals", label: "[SIGNALS]" },
    { id: "active", label: "[ACTIVE_LOGS]" },
  ]


  return (
    <div className="flex flex-col h-full bg-background text-foreground animate-fade-in relative z-10">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border/60 bg-card/15 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-baseline gap-2">
            <h1 className="text-xl font-serif font-normal tracking-tight text-foreground">
              Command Center
            </h1>
            <span className="text-[10px] font-mono text-primary/70 uppercase tracking-widest">
              [OPS_DECK_V2]
            </span>
          </div>
          <p className="text-[10px] text-muted-foreground mt-1 leading-snug">
            Live marketing signals, opportunities, and next actions for your active workspace.
          </p>
          <div className="flex items-center gap-2 mt-1.5">
            {projects.length > 1 ? (
              <select
                value={activeProject?.id || ""}
                onChange={(e) => selectProject(e.target.value)}
                className="bg-card/85 hover:bg-card border border-border/80 rounded px-2 py-0.5 text-[11px] text-foreground font-medium outline-none cursor-pointer focus:border-primary/80 transition font-sans"
              >
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            ) : (
              <p className="text-sm font-serif text-primary italic leading-none">
                {activeProject?.name}
              </p>
            )}
            <span className="text-[11px] text-muted-foreground/40">·</span>
            <p className="text-[10px] font-mono text-muted-foreground/80 bg-muted/30 px-1.5 py-0.5 rounded border border-border/30">
              {activeProject?.website_url || "no URL"}
            </p>
          </div>
        </div>

        {/* Tab Controls and Actions */}
        <div className="flex flex-wrap items-center gap-3">
          <AnimatedTabs tabs={tabs} activeTab={activeTab} onChange={(id: string) => {
            setActiveTab(id)
            setSelectedItem(null)
          }} />

          <div className="flex items-center gap-2">
            <button
              onClick={handleScan}
              disabled={scanning}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-card/85 hover:bg-card border border-border/80 hover:border-primary/45 rounded text-xs text-foreground transition duration-300 disabled:opacity-50 font-sans shadow-sm"
              title="Trigger immediate scan"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-primary/95 ${scanning ? "animate-spin" : ""}`} />
              <span className="font-medium">{scanning ? "Scanning..." : "Scan Workspace"}</span>
            </button>
            <Link
              href="/chat"
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded text-xs transition duration-300 shadow-md border border-primary/20 hover:scale-[1.01] active:scale-100"
            >
              <MessageSquarePlus className="w-3.5 h-3.5 text-primary-foreground/90" />
              <span>Brief Swarm</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Pulse bar */}
      <PulseBar activities={pulseActivities} signalsCount={signals.length} />

      {/* Core Deck Grid Floor */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Main List Column Pane */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          
          {scanning && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 border border-border/40 p-4.5 bg-primary/5 rounded-xl">
              <div className="col-span-full text-xs font-mono uppercase tracking-wider text-primary flex items-center gap-2 mb-2 animate-pulse">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Specialist swarming running technical marketing scan...</span>
              </div>
              <ScanlineSkeleton />
              <ScanlineSkeleton />
              <ScanlineSkeleton />
            </div>
          )}

          {/* Tab content 1: Overview */}
          {activeTab === "overview" && !scanning && (
            <div className={`grid gap-4 ${selectedItem ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"}`}>
              {/* Opportunities Column */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono tracking-widest uppercase text-primary/80 border-b border-border/30 pb-1.5 block">
                  Opportunities ({opportunities.length})
                </span>
                {opportunities.slice(0, 3).map((opp, i) => (
                  <OpportunityCard
                    key={opp.id}
                    opportunity={opp}
                    rank={i}
                    onClick={() => setSelectedItem({ type: "opportunity", data: opp })}
                  />
                ))}
              </div>

              {/* Signals Column */}
              <div className="space-y-3">
                <span className="text-[10px] font-mono tracking-widest uppercase text-primary/80 border-b border-border/30 pb-1.5 block">
                  Signals Log ({signals.length})
                </span>
                {signals.slice(0, 4).map((sig) => (
                  <SignalCard
                    key={sig.id}
                    signal={sig}
                    onClick={() => setSelectedItem({ type: "signal", data: sig })}
                  />
                ))}
              </div>

              {/* Active Logs Column */}
              {!selectedItem && (
                <div className="space-y-3">
                  <span className="text-[10px] font-mono tracking-widest uppercase text-[#a3b899] border-b border-[#a3b899]/20 pb-1.5 block">
                    Active Logs ({activeWork.length})
                  </span>
                  {activeWork.length === 0 ? (
                    <div className="bg-card/45 border border-border/40 p-5 rounded-lg text-center text-[10px] font-mono text-muted-foreground/60 uppercase">
                      NO_ACTIVE_SCANS
                    </div>
                  ) : (
                    activeWork.map((item) => (
                      <ActiveWorkCard key={item.id} item={item} />
                    ))
                  )}
                </div>
              )}
            </div>
          )}

          {/* Tab content 2: Opportunities */}
          {activeTab === "opportunities" && !scanning && (
            <div className={`grid gap-4 ${selectedItem ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"}`}>
              {opportunities.length === 0 ? (
                <div className="text-center py-16 text-[10px] font-mono text-muted-foreground uppercase">
                  NO_OPPORTUNITIES_DETECTED
                </div>
              ) : (
                opportunities.map((opp, i) => (
                  <OpportunityCard
                    key={opp.id}
                    opportunity={opp}
                    rank={i}
                    onClick={() => setSelectedItem({ type: "opportunity", data: opp })}
                  />
                ))
              )}
            </div>
          )}

          {/* Tab content 3: Signals */}
          {activeTab === "signals" && !scanning && (
            <div className={`grid gap-4 ${selectedItem ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"}`}>
              {signals.length === 0 ? (
                <div className="text-center py-16 text-[10px] font-mono text-muted-foreground uppercase">
                  NO_TELEMETRY_SIGNALS
                </div>
              ) : (
                signals.map((sig) => (
                  <SignalCard
                    key={sig.id}
                    signal={sig}
                    onClick={() => setSelectedItem({ type: "signal", data: sig })}
                  />
                ))
              )}
            </div>
          )}

          {/* Tab content 4: Active logs */}
          {activeTab === "active" && !scanning && (
            <div className="max-w-2xl mx-auto space-y-3">
              {activeWork.length === 0 ? (
                <div className="bg-card/65 border border-border/40 rounded-xl p-8 text-center text-[11px] text-muted-foreground">
                  <div className="mb-2 font-mono uppercase tracking-widest text-muted-foreground/50">Core Engine Idle</div>
                  <button
                    onClick={handleScan}
                    disabled={scanning}
                    className="text-primary font-mono text-[9px] uppercase tracking-widest hover:underline disabled:opacity-50"
                  >
                    TRIGGER_SCAN
                  </button>
                </div>
              ) : (
                activeWork.map((item) => (
                  <ActiveWorkCard key={item.id} item={item} />
                ))
              )}
            </div>
          )}

        </div>

        {/* Right-Side Progressive Detail Rail */}
        <RevealPanel
          isOpen={selectedItem !== null}
          onClose={() => setSelectedItem(null)}
          title={selectedItem?.type === "opportunity" ? "Opportunity Briefing" : "Signal Telemetry"}
          widthClass="w-96"
        >
          {selectedItem?.type === "opportunity" && (
            <div className="space-y-4 font-sans text-xs">
              <div>
                <span className="text-[9px] font-mono uppercase tracking-wider bg-primary/10 border border-primary/20 text-primary px-2 py-0.5 rounded">
                  {selectedItem.data.category}
                </span>
                <h4 className="font-serif font-normal text-base text-foreground mt-3 leading-snug">
                  {selectedItem.data.title}
                </h4>
              </div>
              <div className="border-t border-border/30 pt-3">
                <span className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest block mb-1">Impact Description</span>
                <p className="text-muted-foreground leading-relaxed text-xs">
                  {selectedItem.data.description}
                </p>
              </div>
              
              <div className="bg-card/45 border border-border/40 p-3 rounded-lg space-y-2.5 font-mono text-[10px] uppercase">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">RICE RATING</span>
                  <span className="text-primary font-bold">{selectedItem.data.rice_score.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">ALIGN CONFIDENCE</span>
                  <span className="text-foreground">{(selectedItem.data.confidence * 100).toFixed(0)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">PROPOSED BY</span>
                  <span className="text-primary">{selectedItem.data.proposed_by}</span>
                </div>
              </div>

              <div className="border-t border-border/30 pt-4 flex flex-col gap-2">
                <button
                  onClick={() => {
                    setSelectedItem(null)
                    router.push(`/chat?opportunity=${selectedItem.data.id}`)
                  }}
                  className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded transition-all duration-300 shadow-md border border-primary/20 text-center"
                >
                  Brief Swarm on Opportunity
                </button>
                <button
                  onClick={() => {
                    setSelectedItem(null)
                    router.push("/approval")
                  }}
                  className="w-full py-2 bg-card border border-border/80 hover:bg-muted text-muted-foreground hover:text-foreground font-mono text-[10px] uppercase tracking-wider rounded transition duration-300 text-center"
                >
                  Manage on Approvals Board
                </button>
              </div>
            </div>
          )}

          {selectedItem?.type === "signal" && (
            <div className="space-y-4 font-sans text-xs">
              <div>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded border border-primary/20 bg-primary/5 text-[9px] font-mono uppercase tracking-widest text-primary">
                  {selectedItem.data.signal_type || "TELEMETRY"}
                </span>
                <h4 className="font-serif font-normal text-base text-foreground mt-3 leading-snug">
                  {selectedItem.data.title}
                </h4>
              </div>
              <div className="border-t border-border/30 pt-3">
                <span className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest block mb-1">Signal telemetric read</span>
                <p className="text-muted-foreground leading-relaxed text-xs">
                  {selectedItem.data.description}
                </p>
              </div>

              <div className="bg-card/45 border border-border/40 p-3 rounded-lg space-y-2.5 font-mono text-[10px] uppercase">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">SEVERITY</span>
                  <span className="text-primary font-bold">{selectedItem.data.severity || "MEDIUM"}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">DETECTED BY</span>
                  <span className="text-foreground">{selectedItem.data.source_agent}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">TIMESTAMP</span>
                  <span className="text-foreground">{new Date(selectedItem.data.created_at).toLocaleTimeString()}</span>
                </div>
              </div>

              <div className="border-t border-border/30 pt-4">
                <button
                  onClick={() => {
                    setSelectedItem(null)
                    router.push(`/chat?signal=${selectedItem.data.id}`)
                  }}
                  className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded transition-all duration-300 shadow-md border border-primary/20 text-center"
                >
                  Deploy Swarm on Signal
                </button>
              </div>
            </div>
          )}
        </RevealPanel>
      </div>
    </div>
  )
}
