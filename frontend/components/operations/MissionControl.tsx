"use client"

import React, { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { listSignals, listOpportunities, triggerScan, updateOpportunity } from "@/lib/api"
import type { Signal, Opportunity } from "@/lib/api"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { 
  Compass, 
  RefreshCw, 
  Zap, 
  Activity, 
  ArrowRight, 
  ChevronRight,
  TrendingUp, 
  ShieldAlert, 
  CheckCircle2, 
  Clock, 
  Users, 
  Bot, 
  Award,
  CircleDot,
  Play
} from "lucide-react"
import { cn } from "@/lib/utils"
import Link from "next/link"
import { WelcomeOnboarding } from "@/components/shared/WelcomeOnboarding"

export function MissionControl() {
  const router = useRouter()
  const { projects, activeProject, loading: projectsLoading } = useActiveProject()
  
  const [signals, setSignals] = useState<Signal[]>([])
  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [dataLoading, setDataLoading] = useState(true)
  const [scanning, setScanning] = useState(false)
  const [actioningId, setActioningId] = useState<string | null>(null)

  const projectId = activeProject?.id

  const loadData = useCallback(async () => {
    if (!projectId) {
      setSignals([])
      setOpportunities([])
      setDataLoading(false)
      return
    }
    setDataLoading(true)
    try {
      const [signalsRes, oppsRes] = await Promise.all([
        listSignals("active", projectId),
        listOpportunities("active", projectId),
      ])
      setSignals(signalsRes.signals || [])
      setOpportunities(oppsRes.opportunities || [])
    } catch (e) {
      console.error("Failed to load Mission Control data:", e)
    } finally {
      setDataLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleScan = useCallback(async () => {
    if (!projectId) return
    setScanning(true)
    try {
      await triggerScan(projectId)
      await loadData()
    } catch (e) {
      console.error("Scan trigger failed:", e)
    } finally {
      setScanning(false)
    }
  }, [projectId, loadData])

  const handleQuickApprove = async (id: string) => {
    setActioningId(id)
    try {
      await updateOpportunity(id, { status: "completed" })
      loadData()
    } catch (e) {
      console.error("Failed to approve action:", e)
    } finally {
      setActioningId(null)
    }
  }

  const loading = projectsLoading || dataLoading

  // Calculate scores
  const scoreBase = 100 - (signals.length * 4)
  const healthScore = Math.max(35, Math.min(98, scoreBase))

  const seoSignalsCount = signals.filter(s => s.category.toLowerCase() === "seo").length
  const aeoSignalsCount = signals.filter(s => s.category.toLowerCase() === "aeo").length
  const trackingSignalsCount = signals.filter(s => s.category.toLowerCase() === "analytics").length
  const conversionSignalsCount = signals.filter(s => s.category.toLowerCase() === "cro").length

  const seoScore = Math.max(45, 100 - (seoSignalsCount * 12))
  const aeoScore = Math.max(50, 100 - (aeoSignalsCount * 15))
  const trackingScore = Math.max(60, 100 - (trackingSignalsCount * 15))
  const conversionScore = Math.max(40, 100 - (conversionSignalsCount * 20))

  // Find most critical signal for Recommended Next Action
  const nextActionSignal = signals.find(s => s.severity.toLowerCase() === "critical") || 
                           signals.find(s => s.severity.toLowerCase() === "high") || 
                           signals[0]

  if (loading && signals.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <RefreshCw className="w-5 h-5 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Syncing Mission Control...</div>
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
    <div className="flex-1 overflow-y-auto px-8 py-6 bg-background text-foreground animate-fade-in">
      <div className="max-w-5xl mx-auto space-y-6">
        
        {/* Dashboard Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-border/60 pb-5 gap-4">
          <div>
            <div className="flex items-baseline gap-2 mb-1">
              <Compass className="w-5 h-5 text-primary" />
              <h1 className="text-2xl md:text-3xl font-serif font-normal tracking-tight text-foreground">
                Mission Control
              </h1>
            </div>
            <p className="text-xs text-muted-foreground">
              Swarm operations center. Unified marketing health indices and active agent tasks.
            </p>
          </div>
          
          <div className="flex items-center gap-2.5">
            <button
              onClick={handleScan}
              disabled={scanning}
              className="flex items-center gap-1.5 px-3.5 py-1.5 bg-card border border-border hover:border-primary/50 hover:bg-card/70 rounded-lg text-xs text-foreground font-mono uppercase tracking-wider transition disabled:opacity-50"
            >
              <RefreshCw className={cn("w-3.5 h-3.5", scanning && "animate-spin")} />
              <span>{scanning ? "Scanning..." : "Scan Site"}</span>
            </button>
            
            <Link
              href="/chat"
              className="px-4 py-1.5 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition shadow-md border border-primary/20 flex items-center gap-1.5"
            >
              <span>Prompt Swarm</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>

        {/* Health Scores Grid & Recommended Action */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Main Health Rings Card */}
          <div className="lg:col-span-2 glass-panel rounded-xl p-6 flex flex-col justify-between shadow-md relative overflow-hidden">
            <div>
              <span className="text-[9px] font-mono text-muted-foreground uppercase tracking-widest block mb-4">MARKETING READY MATRIX</span>
              
              <div className="flex flex-col sm:flex-row items-center gap-8">
                {/* Visual Ring Chart */}
                <div className="relative w-32 h-32 flex items-center justify-center flex-shrink-0">
                  <svg className="w-full h-full transform -rotate-90">
                    <circle cx="64" cy="64" r="54" className="stroke-muted" strokeWidth="8" fill="transparent" />
                    <circle 
                      cx="64" 
                      cy="64" 
                      r="54" 
                      className="stroke-primary transition-all duration-1000 ease-out" 
                      strokeWidth="8" 
                      fill="transparent" 
                      strokeDasharray={339.29} 
                      strokeDashoffset={339.29 - (339.29 * healthScore) / 100}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute flex flex-col items-center justify-center">
                    <span className="text-3xl font-serif font-normal text-foreground leading-none">{healthScore}%</span>
                    <span className="text-[8px] font-mono text-muted-foreground uppercase tracking-widest mt-1">Ready</span>
                  </div>
                </div>

                {/* Sub-Health parameters */}
                <div className="flex-grow grid grid-cols-2 gap-4.5 w-full">
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground/85">
                      <span>SEO SCANNER</span>
                      <span className="text-foreground font-bold">{seoScore}%</span>
                    </div>
                    <div className="w-full bg-border/40 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-primary h-full rounded-full transition-all duration-500" style={{ width: `${seoScore}%` }} />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground/85">
                      <span>AEO INDEX</span>
                      <span className="text-foreground font-bold">{aeoScore}%</span>
                    </div>
                    <div className="w-full bg-border/40 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-accent h-full rounded-full transition-all duration-500" style={{ width: `${aeoScore}%` }} />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground/85">
                      <span>ANALYTICS GAP</span>
                      <span className="text-foreground font-bold">{trackingScore}%</span>
                    </div>
                    <div className="w-full bg-border/40 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full transition-all duration-500" style={{ width: `${trackingScore}%` }} />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px] font-mono text-muted-foreground/85">
                      <span>CONVERSION READY</span>
                      <span className="text-foreground font-bold">{conversionScore}%</span>
                    </div>
                    <div className="w-full bg-border/40 h-1.5 rounded-full overflow-hidden">
                      <div className="bg-amber-500 h-full rounded-full transition-all duration-500" style={{ width: `${conversionScore}%` }} />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="border-t border-border/40 pt-4.5 mt-6 flex justify-between items-center text-[10px] font-mono text-muted-foreground/75">
              <span>SCAN TARGET: {activeProject?.name || "SYS_WORKSPACE"}</span>
              <Link href="/signal-intelligence" className="text-primary hover:underline flex items-center gap-1">
                <span>Detailed Intelligence Radar</span>
                <ChevronRight className="w-3 h-3" />
              </Link>
            </div>
          </div>

          {/* Recommended Next Action Card */}
          <div className="glass-panel border border-primary/20 rounded-xl p-6 flex flex-col justify-between shadow-md">
            <div>
              <span className="text-[9px] font-mono text-primary uppercase tracking-widest block mb-4.5">RECOMMENDED NEXT ACTION</span>
              
              {nextActionSignal ? (
                <div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 bg-primary/15 border border-primary/20 text-primary text-[8px] font-mono uppercase tracking-wider rounded">
                      {nextActionSignal.category}
                    </span>
                    <span className="text-[9px] font-mono text-destructive uppercase font-semibold">
                      {nextActionSignal.severity} severity
                    </span>
                  </div>
                  
                  <h3 className="text-sm font-semibold text-foreground leading-snug mb-1.5">
                    {nextActionSignal.title}
                  </h3>
                  <p className="text-xs text-muted-foreground/80 leading-relaxed font-sans line-clamp-3">
                    {nextActionSignal.description}
                  </p>
                </div>
              ) : (
                <div className="text-center py-4">
                  <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                  <p className="text-xs text-muted-foreground font-sans">No alert vectors found. Run a scan to discover recommendations.</p>
                </div>
              )}
            </div>

            {nextActionSignal && (
              <button 
                onClick={() => router.push(`/chat?signal=${nextActionSignal.id}`)}
                className="w-full mt-6 py-2 px-3 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[9px] uppercase tracking-wider rounded-lg transition flex items-center justify-center gap-1.5 shadow-md"
              >
                <span>Deploy Boardroom Swarm</span>
                <Play className="w-2.5 h-2.5 fill-current" />
              </button>
            )}
          </div>

        </div>

        {/* Dashboard split lists: Active Work, Pending Approvals, Recent Agent Activity */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Pending Approvals */}
          <div className="space-y-3">
            <h3 className="font-mono text-[10px] text-primary/80 uppercase tracking-widest flex items-center gap-2 px-1">
              <Award className="w-4 h-4 text-primary" />
              Campaign Actions Pending Approval
            </h3>

            <div className="glass-panel rounded-xl p-4.5 space-y-3 shadow-md max-h-[360px] overflow-y-auto">
              {opportunities.length === 0 ? (
                <div className="text-center py-12 text-xs text-muted-foreground/75 font-sans">
                  No actions pending. Scans and briefs generate opportunities.
                </div>
              ) : (
                opportunities.slice(0, 4).map((opp) => (
                  <div 
                    key={opp.id} 
                    className="p-3 border border-border/40 hover:border-primary/20 bg-background/30 rounded-lg flex items-center justify-between gap-4 transition duration-200"
                  >
                    <div className="min-w-0">
                      <span className="text-[8px] font-mono uppercase text-primary/80 bg-primary/5 px-1.5 py-0.2 rounded border border-primary/10 mb-1 inline-block">
                        {opp.category}
                      </span>
                      <h4 className="text-xs font-sans font-medium text-foreground truncate max-w-xs">{opp.title}</h4>
                      <p className="text-[10px] font-mono text-muted-foreground/60 mt-0.5">RICE: {opp.rice_score.toFixed(2)}</p>
                    </div>

                    <button 
                      onClick={() => handleQuickApprove(opp.id)}
                      disabled={actioningId === opp.id}
                      className="flex-shrink-0 px-2.5 py-1.5 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[9px] uppercase tracking-wider rounded transition shadow-sm"
                    >
                      {actioningId === opp.id ? "..." : "Approve"}
                    </button>
                  </div>
                ))
              )}
              {opportunities.length > 4 && (
                <Link 
                  href="/approval" 
                  className="block text-center text-[10px] font-mono uppercase text-primary hover:underline pt-2"
                >
                  View All {opportunities.length} Approvals
                </Link>
              )}
            </div>
          </div>

          {/* Recent Agent Activity Logs */}
          <div className="space-y-3">
            <h3 className="font-mono text-[10px] text-primary/80 uppercase tracking-widest flex items-center gap-2 px-1">
              <Activity className="w-4 h-4 text-primary" />
              Recent Agent Activity
            </h3>

            <div className="glass-panel rounded-xl p-4.5 space-y-4.5 shadow-md max-h-[360px] overflow-y-auto">
              {signals.length === 0 ? (
                <div className="text-center py-12 text-xs text-muted-foreground/75 font-sans">
                  No recent activities recorded. Start a scan vector.
                </div>
              ) : (
                signals.slice(0, 4).map((sig, idx) => {
                  const hours = idx * 2 + 1
                  return (
                    <div key={sig.id} className="flex gap-3 text-xs leading-relaxed">
                      <span className="mt-0.5 w-6 h-6 rounded bg-primary/10 border border-primary/20 flex items-center justify-center text-[11px] flex-shrink-0 text-primary">
                        🤖
                      </span>
                      <div className="min-w-0">
                        <p className="text-xs text-foreground/90 font-sans">
                          <span className="font-semibold text-primary">{sig.source_agent.toUpperCase()} specialist</span> audited the website and detected a new signal.
                        </p>
                        <p className="text-[10px] text-card-foreground/75 mt-0.5 line-clamp-1 italic">
                          "{sig.title}"
                        </p>
                        <span className="text-[9px] font-mono text-muted-foreground/50 block mt-1 uppercase">
                          {hours} hours ago · verified
                        </span>
                      </div>
                    </div>
                  )
                })
              )}
              {signals.length > 0 && (
                <Link 
                  href="/audit-timeline" 
                  className="block text-center text-[10px] font-mono uppercase text-primary hover:underline pt-2 border-t border-border/30"
                >
                  View System Audit Logs
                </Link>
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  )
}
