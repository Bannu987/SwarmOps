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

  return (
    <div className="flex flex-col h-full bg-background text-foreground">
      {/* Header */}
      <div className="px-6 py-4 border-b border-border/60 bg-card/15 flex items-center justify-between">
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
        <div className="flex items-center gap-2">
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-card/85 hover:bg-card border border-border/80 hover:border-primary/45 rounded-md text-xs text-foreground transition duration-300 disabled:opacity-50 font-sans shadow-sm"
            title="Trigger immediate scan"
          >
            <RefreshCw className={`w-3.5 h-3.5 text-primary/95 ${scanning ? "animate-spin" : ""}`} />
            <span className="font-medium">{scanning ? "Scanning..." : "Scan Workspace"}</span>
          </button>
          <Link
            href="/chat"
            className="flex items-center gap-1.5 px-3.5 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-md text-xs transition duration-300 shadow-md border border-primary/20 hover:scale-[1.01] active:scale-100"
          >
            <MessageSquarePlus className="w-3.5 h-3.5 text-primary-foreground/90" />
            <span>Brief the Swarm</span>
          </Link>
        </div>
      </div>

      {/* Pulse bar */}
      <PulseBar activities={pulseActivities} signalsCount={signals.length} />

      {/* Three columns */}
      <div className="flex-1 grid grid-cols-3 overflow-hidden divide-x divide-border">
        {/* Column 1: Opportunities */}
        <Column
          title="Opportunities"
          badge={`${opportunities.length} ranked`}
        >
          {opportunities.length === 0 ? (
            <div className="text-center py-8 text-[11px] text-muted-foreground">
              No opportunities yet — run a scan to generate them
            </div>
          ) : (
            opportunities.map((opp, i) => (
              <OpportunityCard
                key={opp.id}
                opportunity={opp}
                rank={i}
                onClick={() => router.push(`/chat?opportunity=${opp.id}`)}
              />
            ))
          )}
        </Column>

        {/* Column 2: Active Work */}
        <Column
          title="Active Work"
          status={activeWork.length > 0 ? { dot: "#a3b899", label: "Live" } : undefined}
        >
          {activeWork.length === 0 ? (
            <div className="text-center py-8 text-[11px] text-muted-foreground">
              <div className="mb-2 text-muted-foreground/50">No active scans</div>
              <button
                onClick={handleScan}
                disabled={scanning}
                className="text-primary hover:underline font-mono text-[10px] uppercase tracking-wider disabled:opacity-50"
              >
                Trigger a scan
              </button>
            </div>
          ) : (
            activeWork.map((item) => (
              <ActiveWorkCard key={item.id} item={item} />
            ))
          )}
        </Column>

        {/* Column 3: Signals */}
        <Column
          title="Signals"
          badge={unseen > 0 ? `${unseen} new` : `${signals.length} total`}
          badgeColor={unseen > 0 ? "#c5a880" : undefined}
        >
          {signals.length === 0 ? (
            <div className="text-center py-8 text-[11px] text-muted-foreground">
              No signals detected
            </div>
          ) : (
            signals.map((signal) => (
              <SignalCard
                key={signal.id}
                signal={signal}
                onClick={() => router.push(`/chat?signal=${signal.id}`)}
              />
            ))
          )}
        </Column>
      </div>
    </div>
  )
}
