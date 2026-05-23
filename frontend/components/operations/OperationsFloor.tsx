"use client"

import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { listSignals, listOpportunities, listProjects, triggerScan } from "@/lib/api"
import type { Signal, Opportunity, Project } from "@/lib/api"
import { Column } from "./Column"
import { OpportunityCard } from "./OpportunityCard"
import { SignalCard } from "./SignalCard"
import { ActiveWorkCard, type ActiveWorkItem } from "./ActiveWorkCard"
import { PulseBar } from "./PulseBar"
import { EmptyOperationsState } from "./EmptyOperationsState"
import { RefreshCw, MessageSquarePlus } from "lucide-react"
import Link from "next/link"

export function OperationsFloor() {
  const router = useRouter()

  const [signals, setSignals] = useState<Signal[]>([])
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [activeWork, setActiveWork] = useState<ActiveWorkItem[]>([])
  const [loading, setLoading] = useState(true)
  const [scanning, setScanning] = useState(false)

  const loadData = useCallback(async () => {
    try {
      const [projectsRes, signalsRes, oppsRes] = await Promise.all([
        listProjects(),
        listSignals("active"),
        listOpportunities("active"),
      ])
      setProjects(projectsRes.projects || [])
      setSignals(signalsRes.signals || [])
      setOpportunities(oppsRes.opportunities || [])
    } catch (e) {
      console.error("Failed to load operations data:", e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 60000)
    return () => clearInterval(interval)
  }, [loadData])

  const handleScan = async () => {
    setScanning(true)
    const firstProject = projects[0]

    setActiveWork([
      { id: "scan-1", agentId: "seo", task: "Scanning site for issues", status: "thinking", progress: 30 },
    ])

    try {
      await triggerScan(firstProject?.id)
      await loadData()
    } catch (e) {
      console.error("Scan failed:", e)
    } finally {
      setScanning(false)
      setActiveWork([])
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-sm text-muted-foreground">Loading operations floor...</div>
      </div>
    )
  }

  if (projects.length === 0) {
    return <EmptyOperationsState hasProject={false} />
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
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-3 border-b border-border flex items-center justify-between">
        <div>
          <h1 className="text-base font-medium tracking-tight">Operations Floor</h1>
          <p className="text-[11px] text-muted-foreground">
            {projects[0]?.name} · {projects[0]?.website_url || "no URL"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleScan}
            disabled={scanning}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-card hover:bg-muted border border-border rounded-md text-xs text-foreground transition disabled:opacity-50"
            title="Trigger immediate scan"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${scanning ? "animate-spin" : ""}`} />
            {scanning ? "Scanning..." : "Refresh"}
          </button>
          <Link
            href="/chat"
            className="flex items-center gap-1.5 px-3 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground rounded-md text-xs font-medium transition"
          >
            <MessageSquarePlus className="w-3.5 h-3.5" />
            Brief the swarm
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
          status={activeWork.length > 0 ? { dot: "#22C55E", label: "Live" } : undefined}
        >
          {activeWork.length === 0 ? (
            <div className="text-center py-8 text-[11px] text-muted-foreground">
              <div className="mb-2 text-muted-foreground/50">No active scans</div>
              <button
                onClick={handleScan}
                disabled={scanning}
                className="text-primary hover:underline disabled:opacity-50"
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
          badgeColor={unseen > 0 ? "#22D3EE" : undefined}
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
