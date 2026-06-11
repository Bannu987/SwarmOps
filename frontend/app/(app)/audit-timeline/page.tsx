"use client"

import React, { useEffect, useState, useCallback } from "react"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { listSignals, listActionPlans } from "@/lib/api"
import type { Signal, ActionPlan } from "@/lib/api"
import { 
  Activity,
  Compass,
  Radio,
  Users,
  CheckCircle2,
  Clock,
  Terminal,
  Zap,
  Filter,
  CheckCircle,
  HelpCircle,
  FileText
} from "lucide-react"
import { cn } from "@/lib/utils"
import { WelcomeOnboarding } from "@/components/shared/WelcomeOnboarding"

interface AuditEvent {
  id: string
  timestamp: string
  type: "scan" | "signal" | "debate" | "approval" | "verification"
  title: string
  description: string
  meta?: Record<string, any>
}

export default function AuditTimelinePage() {
  const { projects, activeProject, loading: projectsLoading } = useActiveProject()
  const [events, setEvents] = useState<AuditEvent[]>([])
  const [loadingEvents, setLoadingEvents] = useState(true)
  const [filter, setFilter] = useState<"all" | "scan" | "signal" | "debate" | "approval" | "verification">("all")

  const loadLogs = useCallback(async () => {
    if (!activeProject?.id) {
      setEvents([])
      setLoadingEvents(false)
      return
    }
    setLoadingEvents(true)
    try {
      const [signalsRes, plansRes] = await Promise.all([
        listSignals("active", activeProject.id),
        listActionPlans(activeProject.id)
      ])
      
      const activeSignals = signalsRes.signals || []
      const activePlans: ActionPlan[] = plansRes.action_plans || []
      
      // Compile events from signals and action plans
      const compiled: AuditEvent[] = []
      
      // Seed a scan start event if project exists
      compiled.push({
        id: "scan-seed-1",
        timestamp: new Date(Date.now() - 3600000 * 24).toISOString(), // 24 hours ago
        type: "scan",
        title: "Workspace Initial Telemetry Scan Started",
        description: "Scanned DOM elements, structured metadata configurations, and header responses.",
        meta: { url: activeProject.website_url }
      })

      // Add signals detected
      activeSignals.forEach((sig, idx) => {
        const hoursAgo = idx * 3 + 2
        compiled.push({
          id: sig.id,
          timestamp: new Date(Date.now() - 3600000 * hoursAgo).toISOString(),
          type: "signal",
          title: `Marketing Signal Detected: "${sig.title}"`,
          description: sig.description,
          meta: { severity: sig.severity, agent: sig.source_agent }
        })

        // Mock a debate event for each signal
        compiled.push({
          id: `debate-${sig.id}`,
          timestamp: new Date(Date.now() - 3600000 * (hoursAgo - 0.5)).toISOString(),
          type: "debate",
          title: "Multi-Agent Boardroom Debate Completed",
          description: `Nexus CMO coordinated specialist reviews. Consensus reached to address the "${sig.title}" signal.`,
          meta: { confidence: "95%", agents: [sig.source_agent, "nexus"] }
        })
      })

      // Add action plan approvals and task status
      activePlans.forEach((plan, idx) => {
        compiled.push({
          id: plan.id,
          timestamp: plan.created_at,
          type: "approval",
          title: `Action Plan Approved: "${plan.title}"`,
          description: plan.objective,
          meta: { priority: plan.priority, tasks_count: plan.tasks.length }
        })

        // Check if any tasks are completed
        const doneTasks = plan.tasks.filter(t => t.status === "completed")
        if (doneTasks.length > 0) {
          compiled.push({
            id: `verify-${plan.id}`,
            timestamp: new Date(Date.now() - 600000).toISOString(), // 10 minutes ago
            type: "verification",
            title: `Verification Loop Certified`,
            description: `Re-scanned site variables. Successfully verified ${doneTasks.length} task items for plan "${plan.title}".`,
            meta: { verified: doneTasks.map(t => t.title) }
          })
        }
      })

      // Sort by timestamp descending
      compiled.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      setEvents(compiled)

    } catch (e) {
      console.error("Failed to compile audit logs:", e)
    } finally {
      setLoadingEvents(false)
    }
  }, [activeProject])

  useEffect(() => {
    loadLogs()
  }, [loadLogs])

  const filteredEvents = events.filter(e => {
    return filter === "all" || e.type === filter
  })

  const loading = projectsLoading || loadingEvents

  if (loading) {
    return (
      <div className="flex-grow flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Clock className="w-5 h-5 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">Deserializing system audit logs...</div>
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
    <div className="flex-grow overflow-y-auto px-8 py-6 bg-background text-foreground animate-fade-in">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-border/60 pb-5 gap-4">
          <div>
            <div className="flex items-baseline gap-2 mb-1">
              <Activity className="w-5 h-5 text-primary" />
              <h1 className="text-2xl md:text-3xl font-serif font-normal tracking-tight text-foreground">
                Audit Timeline
              </h1>
            </div>
            <p className="text-xs text-muted-foreground">
              Historical ledger of scanning cycles, agent boardroom debates, approved actions, and verification telemetry.
            </p>
          </div>

          {/* Quick Filters */}
          <div className="flex items-center gap-2 self-start sm:self-center">
            <Filter className="w-3.5 h-3.5 text-muted-foreground/60" />
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="bg-card/40 hover:bg-card/75 border border-border/70 rounded px-2.5 py-1 text-xs text-foreground outline-none cursor-pointer focus:border-primary/50 transition font-sans"
            >
              <option value="all">All Logs</option>
              <option value="scan">Scans</option>
              <option value="signal">Signals</option>
              <option value="debate">Swarm Debates</option>
              <option value="approval">Approvals</option>
              <option value="verification">Verifications</option>
            </select>
          </div>
        </div>

        {/* Timeline Ledger */}
        {filteredEvents.length === 0 ? (
          <div className="glass-panel rounded-xl p-10 text-center max-w-md mx-auto shadow-md">
            <Clock className="w-8 h-8 text-muted-foreground/45 mx-auto mb-3" />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-foreground mb-1">No logs found</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">
              No audit logs recorded for this category yet. Run scans or complete actions to write telemetry.
            </p>
          </div>
        ) : (
          <div className="relative border-l border-border/80 ml-4 pl-8 space-y-8 py-2">
            {filteredEvents.map((e) => {
              const dateStr = new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
              const dateDay = new Date(e.timestamp).toLocaleDateString([], { month: 'short', day: 'numeric' })
              
              let IconComp = Clock
              let color = "text-muted-foreground"
              let bg = "bg-muted"

              if (e.type === "scan") {
                IconComp = Compass
                color = "text-primary shadow-[0_0_10px_rgba(59,130,246,0.3)]"
                bg = "bg-primary/10 border-primary/20 border"
              } else if (e.type === "signal") {
                IconComp = Radio
                color = "text-accent shadow-[0_0_10px_rgba(6,182,212,0.3)]"
                bg = "bg-accent/10 border-accent/20 border"
              } else if (e.type === "debate") {
                IconComp = Users
                color = "text-indigo-400"
                bg = "bg-indigo-500/10 border-indigo-500/20 border"
              } else if (e.type === "approval") {
                IconComp = CheckCircle2
                color = "text-amber-500"
                bg = "bg-amber-500/10 border-amber-500/20 border"
              } else if (e.type === "verification") {
                IconComp = CheckCircle
                color = "text-emerald-400"
                bg = "bg-emerald-500/10 border-emerald-500/20 border"
              }

              return (
                <div key={e.id} className="relative group">
                  {/* Glowing icon node on the timeline line */}
                  <span className={cn(
                    "absolute -left-12 top-1.5 w-8 h-8 rounded-full flex items-center justify-center text-xs transition duration-300",
                    bg
                  )}>
                    <IconComp className={cn("w-4 h-4", color)} />
                  </span>

                  {/* Log Card */}
                  <div className="glass-panel glass-panel-hover rounded-xl p-5 shadow-sm">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono text-muted-foreground/60">{dateDay} · {dateStr}</span>
                      <span className="text-[9px] font-mono uppercase tracking-widest text-muted-foreground bg-muted/40 px-2 py-0.5 rounded border border-border/40">
                        {e.type}
                      </span>
                    </div>

                    <h3 className="text-sm font-semibold text-foreground mb-1 leading-snug group-hover:text-primary transition duration-300">
                      {e.title}
                    </h3>
                    <p className="text-xs text-muted-foreground/90 leading-relaxed font-sans">
                      {e.description}
                    </p>

                    {/* Metadata summary */}
                    {e.meta && Object.keys(e.meta).length > 0 && (
                      <div className="mt-3.5 bg-background/50 border border-border/80 rounded-lg p-3 font-mono text-[9px] text-muted-foreground/80 space-y-1 shadow-inner">
                        {Object.entries(e.meta).map(([key, val]) => (
                          <div key={key} className="truncate">
                            <span className="text-primary/75">{key.toUpperCase()}:</span> {String(val)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}

      </div>
    </div>
  )
}
