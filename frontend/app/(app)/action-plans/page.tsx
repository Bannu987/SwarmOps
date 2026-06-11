"use client"

import { useEffect, useState, useCallback } from "react"
import { listActionPlans, updateActionPlan, deleteActionPlan } from "@/lib/api"
import type { ActionPlan, ActionPlanTask } from "@/lib/api"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { WelcomeOnboarding } from "@/components/shared/WelcomeOnboarding"
import { 
  ClipboardList, 
  Loader2, 
  Trash2, 
  Download, 
  Copy, 
  Calendar, 
  Sparkles, 
  TrendingUp, 
  AlertTriangle, 
  ShieldAlert, 
  Link2,
  CheckCircle2, 
  Circle,
  Play,
  XCircle,
  Clock,
  ArrowUpRight
} from "lucide-react"

function getOwnerBadge(owner: string) {
  const name = owner.toUpperCase()
  let bg = "bg-white/5"
  let border = "border-white/10"
  let color = "text-white/80"
  
  if (name.includes("SEO")) {
    bg = "bg-[#dfdacf]/5"
    border = "border-[#dfdacf]/20"
    color = "text-[#dfdacf]"
  } else if (name.includes("AEO")) {
    bg = "bg-[#e8927d]/5"
    border = "border-[#e8927d]/20"
    color = "text-[#e8927d]"
  } else if (name.includes("CRO")) {
    bg = "bg-[#a3b899]/5"
    border = "border-[#a3b899]/20"
    color = "text-[#a3b899]"
  } else if (name.includes("CONTENT")) {
    bg = "bg-[#8e2b32]/5"
    border = "border-[#8e2b32]/20"
    color = "text-[#8e2b32]"
  } else if (name.includes("ANALYTICS")) {
    bg = "bg-[#8a857b]/5"
    border = "border-[#8a857b]/20"
    color = "text-[#8a857b]"
  } else if (name.includes("NEXUS")) {
    bg = "bg-[#c5a880]/5"
    border = "border-[#c5a880]/20"
    color = "text-[#c5a880]"
  }
  
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-mono border ${bg} ${border} ${color}`}>
      {name}
    </span>
  )
}

export default function ActionPlansPage() {
  const { projects, activeProject, loading: projectsLoading } = useActiveProject()
  const [plans, setPlans] = useState<ActionPlan[]>([])
  const [loadingPlans, setLoadingPlans] = useState(true)
  const [selectedPlan, setSelectedPlan] = useState<ActionPlan | null>(null)
  
  // Filters
  const [statusFilter, setStatusFilter] = useState("all")
  const [typeFilter, setTypeFilter] = useState("all")
  const [copied, setCopied] = useState(false)
  const [copiedId, setCopiedId] = useState<string | null>(null)

  const projectId = activeProject?.id
  const selectedPlanId = selectedPlan?.id

  const loadPlans = useCallback(async () => {
    if (!projectId) {
      setPlans([])
      setLoadingPlans(false)
      return
    }
    setLoadingPlans(true)
    try {
      const res = await listActionPlans(projectId, statusFilter)
      const list = res.action_plans || []
      setPlans(list)
      
      // Auto-select first or update selected
      if (list.length > 0) {
        if (selectedPlanId) {
          const fresh = list.find((p) => p.id === selectedPlanId)
          setSelectedPlan(fresh || list[0])
        } else {
          setSelectedPlan(list[0])
        }
      } else {
        setSelectedPlan(null)
      }
    } catch (e) {
      console.error("Failed to load action plans:", e)
    } finally {
      setLoadingPlans(false)
    }
  }, [projectId, statusFilter, selectedPlanId])

  useEffect(() => {
    loadPlans()
  }, [projectId, statusFilter]) // Reload on active project or status filter toggle

  const handleTaskToggle = async (plan: ActionPlan, taskId: string) => {
    const updatedTasks = plan.tasks.map((t) => {
      if (t.id === taskId) {
        const nextStatus: ActionPlanTask["status"] = t.status === "completed" ? "pending" : "completed"
        return { ...t, status: nextStatus }
      }
      return t
    })

    // Optimistic update
    const updatedPlan = { ...plan, tasks: updatedTasks }
    setPlans((prev) => prev.map((p) => p.id === plan.id ? updatedPlan : p))
    if (selectedPlan?.id === plan.id) {
      setSelectedPlan(updatedPlan)
    }

    try {
      await updateActionPlan(plan.id, { tasks: updatedTasks })
    } catch (e) {
      console.error("Failed to toggle task:", e)
      // Rollback
      loadPlans()
    }
  }

  const handleTaskStatusChange = async (plan: ActionPlan, taskId: string, newStatus: ActionPlanTask["status"]) => {
    const updatedTasks = plan.tasks.map((t) => {
      if (t.id === taskId) {
        return { ...t, status: newStatus }
      }
      return t
    })

    const updatedPlan = { ...plan, tasks: updatedTasks }
    setPlans((prev) => prev.map((p) => p.id === plan.id ? updatedPlan : p))
    if (selectedPlan?.id === plan.id) {
      setSelectedPlan(updatedPlan)
    }

    try {
      await updateActionPlan(plan.id, { tasks: updatedTasks })
    } catch (e) {
      console.error("Failed to update task status:", e)
      loadPlans()
    }
  }

  const handleDeletePlan = async (id: string) => {
    if (!confirm("Are you sure you want to delete this action plan?")) return
    try {
      const res = await deleteActionPlan(id)
      if (res.success) {
        setPlans((prev) => prev.filter((p) => p.id !== id))
        if (selectedPlan?.id === id) {
          setSelectedPlan(null)
        }
      }
    } catch (e) {
      console.error("Failed to delete plan:", e)
    }
  }

  const handleCopyMarkdown = (plan: ActionPlan) => {
    const tasksMd = plan.tasks.map((t) => `- [${t.status === "completed" ? "x" : " "}] ${t.title} (${t.owner})`).join("\n")
    const kpisMd = plan.kpis.map((k) => `- **${k.metric}**: ${k.target} (${k.timeframe})`).join("\n")
    const risksMd = plan.risks.map((r) => `- **Risk**: ${r.risk} | **Mitigation**: ${r.mitigation}`).join("\n")
    const depsMd = plan.dependencies.map((d) => `- ${d}`).join("\n")

    const markdown = `# ACTION PLAN: ${plan.title}

## Objective
${plan.objective}

## Plan Details
- **Plan Type**: ${plan.plan_type.replace("_", " ").toUpperCase()}
- **Priority**: ${plan.priority.toUpperCase()}
- **Confidence Rating**: ${Math.round(plan.confidence * 100)}%
- **Estimated Effort**: ${plan.estimated_effort.toUpperCase()}
- **Expected Impact**: ${plan.expected_impact.toUpperCase()}

## 📋 Task Checklist
${tasksMd}

## 🎯 KPIs & Target Metrics
${kpisMd}

## ⚠️ Risks & Backups
${risksMd}

## 🔗 Project Dependencies
${depsMd}

_Generated by SwarmOps Action Engine_`

    navigator.clipboard.writeText(markdown)
    setCopiedId(plan.id)
    setCopied(true)
    setTimeout(() => {
      setCopied(false)
      setCopiedId(null)
    }, 2000)
  }

  const handleDownloadMarkdown = (plan: ActionPlan) => {
    const tasksMd = plan.tasks.map((t) => `- [${t.status === "completed" ? "x" : " "}] ${t.title} (${t.owner})`).join("\n")
    const kpisMd = plan.kpis.map((k) => `- **${k.metric}**: ${k.target} (${k.timeframe})`).join("\n")
    const risksMd = plan.risks.map((r) => `- **Risk**: ${r.risk} | **Mitigation**: ${r.mitigation}`).join("\n")
    const depsMd = plan.dependencies.map((d) => `- ${d}`).join("\n")

    const markdown = `# ACTION PLAN: ${plan.title}

## Objective
${plan.objective}

## Plan Details
- **Plan Type**: ${plan.plan_type.replace("_", " ").toUpperCase()}
- **Priority**: ${plan.priority.toUpperCase()}
- **Confidence Rating**: ${Math.round(plan.confidence * 100)}%
- **Estimated Effort**: ${plan.estimated_effort.toUpperCase()}
- **Expected Impact**: ${plan.expected_impact.toUpperCase()}

## 📋 Task Checklist
${tasksMd}

## 🎯 KPIs & Target Metrics
${kpisMd}

## ⚠️ Risks & Backups
${risksMd}

## 🔗 Project Dependencies
${depsMd}

_Generated by SwarmOps Action Engine_`

    const blob = new Blob([markdown], { type: "text/markdown" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `action_plan_${plan.title.toLowerCase().replace(/[^a-z0-9]+/g, "_")}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const loading = projectsLoading || loadingPlans

  if (loading && plans.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-5 h-5 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground">Loading Action Plans Command Center...</div>
        </div>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <WelcomeOnboarding />
      </div>
    )
  }

  if (!activeProject) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background p-6">
        <div className="bg-card border border-white/5 rounded-2xl p-8 max-w-md text-center shadow-lg">
          <ClipboardList className="w-10 h-10 text-primary mx-auto mb-4 animate-bounce" />
          <h3 className="text-base font-semibold text-white mb-1">Select a Workspace</h3>
          <p className="text-xs text-muted-foreground mb-4">
            Select or create a workspace from the dashboard to unlock the Action Plan Engine.
          </p>
        </div>
      </div>
    )
  }

  const filteredPlans = plans.filter((p) => {
    return typeFilter === "all" || p.plan_type === typeFilter
  })

  return (
    <div className="flex-grow flex h-full overflow-hidden bg-transparent text-white animate-fade-in">
      {/* Left List Pane */}
      <div className="w-80 border-r border-white/5 flex flex-col h-full bg-white/[0.01] flex-shrink-0">
        <div className="p-4 border-b border-white/5 space-y-3 bg-white/[0.02]">
          <div className="flex items-center gap-2">
            <ClipboardList className="w-4 h-4 text-primary" />
            <h2 className="font-mono text-[10px] text-primary font-bold uppercase tracking-wider">
              Execution Plans
            </h2>
          </div>
          
          {/* Quick Filters */}
          <div className="grid grid-cols-2 gap-2">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-2.5 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[10px] text-white outline-none cursor-pointer focus:border-primary/50 transition duration-300 font-sans"
            >
              <option value="all" className="bg-[#08080f]">All Statuses</option>
              <option value="pending" className="bg-[#08080f]">Pending</option>
              <option value="in_progress" className="bg-[#08080f]">In Progress</option>
              <option value="completed" className="bg-[#08080f]">Completed</option>
              <option value="blocked" className="bg-[#08080f]">Blocked</option>
            </select>

            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-2.5 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[10px] text-white outline-none cursor-pointer focus:border-primary/50 transition duration-300 font-sans"
            >
              <option value="all" className="bg-[#08080f]">All Types</option>
              <option value="seo_growth" className="bg-[#08080f]">SEO Growth</option>
              <option value="paid_ads" className="bg-[#08080f]">Paid Funnels</option>
              <option value="lead_generation" className="bg-[#08080f]">Lead Gen</option>
              <option value="crm_lifecycle" className="bg-[#08080f]">CRM Drips</option>
              <option value="product_launch" className="bg-[#08080f]">Product Launch</option>
              <option value="competitor_attack" className="bg-[#08080f]">Competitor Attack</option>
              <option value="conversion_rate_optimization" className="bg-[#08080f]">CRO Page</option>
            </select>
          </div>
        </div>

        {/* Plans List Scroll */}
        <div className="flex-grow overflow-y-auto p-3 space-y-2">
          {filteredPlans.length === 0 ? (
            <div className="text-center py-16 px-4">
              <ClipboardList className="w-6 h-6 text-muted-foreground/35 mx-auto mb-2" />
              <p className="text-[10px] font-sans text-muted-foreground/80 leading-relaxed">
                No active execution plans. Approve campaign signals on the timeline to generate dynamic checklists.
              </p>
            </div>
          ) : (
            filteredPlans.map((plan) => {
              const isSelected = selectedPlan?.id === plan.id
              const doneCount = plan.tasks.filter((t) => t.status === "completed").length
              const totalCount = plan.tasks.length
              const percentage = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0

              let priorityColorClass = "text-primary/95 bg-primary/10 border-primary/20"
              if (plan.priority.toLowerCase() === "critical" || plan.priority.toLowerCase() === "high") {
                priorityColorClass = "text-rose-400 bg-rose-500/10 border-rose-500/20"
              }

              return (
                <button
                  key={plan.id}
                  onClick={() => setSelectedPlan(plan)}
                  className={`w-full text-left p-3.5 rounded-xl text-xs transition border flex flex-col gap-3 relative group shadow-sm ${
                    isSelected 
                      ? "bg-white/5 border-white/10 text-white" 
                      : "bg-white/[0.01] border-white/5 hover:bg-white/[0.03] hover:border-white/10 text-muted-foreground hover:text-white"
                  }`}
                >
                  <div className="w-full">
                    {/* Category tag & Priority badge */}
                    <div className="flex items-center justify-between gap-1 mb-2">
                      <span className="inline-flex px-2 py-0.5 rounded-full text-[8px] font-mono uppercase tracking-wider bg-white/5 text-white/80 border border-white/5">
                        {plan.plan_type.replace(/_/g, " ")}
                      </span>
                      <span className={`inline-flex px-1.5 py-0.2 rounded-full text-[8px] font-mono uppercase tracking-wider border ${priorityColorClass}`}>
                        {plan.priority}
                      </span>
                    </div>
                    <h4 className="font-sans font-medium text-xs leading-snug truncate text-white">
                      {plan.title}
                    </h4>
                  </div>

                  {/* Micro Progress Bar */}
                  <div className="space-y-1 w-full">
                    <div className="flex items-center justify-between text-[9px] font-mono text-muted-foreground/60">
                      <span>PROGRESS</span>
                      <span>{percentage}%</span>
                    </div>
                    <div className="w-full bg-white/5 h-1 rounded-full overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-primary to-accent h-full rounded-full transition-all duration-500" 
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>

                  {/* Date details */}
                  <div className="w-full flex items-center justify-between text-[9px] font-mono uppercase tracking-wider text-muted-foreground/60 border-t border-white/5 pt-2 mt-0.5">
                    <span className="flex items-center gap-1">
                      <Clock className="w-2.5 h-2.5 text-muted-foreground/50" />
                      {new Date(plan.created_at).toLocaleDateString()}
                    </span>
                    <span className="text-[8px] opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-0.5">
                      View details <ArrowUpRight className="w-2.5 h-2.5" />
                    </span>
                  </div>
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Right Plan Detail Pane */}
      <div className="flex-1 overflow-y-auto bg-white/[0.01] flex flex-col h-full">
        {selectedPlan ? (
          <div className="flex-grow p-6 space-y-6">
            
            {/* Header Actions */}
            <div className="flex flex-wrap items-start justify-between gap-4 border-b border-white/5 pb-5">
              <div>
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[8px] font-mono uppercase tracking-wider bg-white/5 border border-white/5 text-white/80">
                    {selectedPlan.plan_type.replace(/_/g, " ")}
                  </span>
                  <span className="text-[10px] text-muted-foreground/40">·</span>
                  <span className="text-[10px] font-mono text-muted-foreground">CONFIDENCE: {Math.round(selectedPlan.confidence * 100)}%</span>
                </div>
                <h1 className="text-xl md:text-2xl font-serif font-normal tracking-tight text-white mt-2">
                  {selectedPlan.title}
                </h1>
                <p className="text-xs text-muted-foreground mt-2 leading-relaxed max-w-2xl">
                  {selectedPlan.objective}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={() => handleCopyMarkdown(selectedPlan)}
                  className="px-3 py-1.5 border border-white/10 hover:bg-white/5 rounded-lg text-muted-foreground hover:text-white transition-all duration-300 flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider"
                  title="Copy as Markdown"
                >
                  {copiedId === selectedPlan.id ? (
                    <span className="text-emerald-400 font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      COPIED
                    </span>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5 text-muted-foreground/75" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
                <button
                  onClick={() => handleDownloadMarkdown(selectedPlan)}
                  className="px-3 py-1.5 border border-white/10 hover:bg-white/5 rounded-lg text-muted-foreground hover:text-white transition-all duration-300 flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider"
                  title="Download Markdown File"
                >
                  <Download className="w-3.5 h-3.5 text-muted-foreground/75" />
                  <span>Download</span>
                </button>
                <button
                  onClick={() => handleDeletePlan(selectedPlan.id)}
                  className="p-2 border border-rose-500/10 hover:bg-rose-500/10 text-muted-foreground hover:text-rose-400 rounded-lg transition-all duration-300"
                  title="Delete Execution Plan"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Primary Details Checklist */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Checklist Column */}
              <div className="lg:col-span-2 space-y-4">
                <h3 className="font-mono text-[10px] text-primary font-bold uppercase tracking-wider flex items-center gap-2">
                  <ClipboardList className="w-4 h-4 text-primary" />
                  Campaign Checklist & Sub-Tasks
                </h3>
                
                <div className="glass-panel border border-white/5 rounded-xl p-5 space-y-3 shadow-md">
                  {selectedPlan.tasks.length === 0 ? (
                    <p className="text-xs text-muted-foreground italic">No tasks created for this plan.</p>
                  ) : (
                    selectedPlan.tasks.map((task) => {
                      const isCompleted = task.status === "completed"
                      const isBlocked = task.status === "blocked"
                      const isProgress = task.status === "in_progress"

                      return (
                        <div 
                          key={task.id} 
                          className={`flex items-start gap-3.5 p-3.5 rounded-lg border transition-all duration-300 group ${
                            isCompleted 
                              ? "bg-emerald-500/[0.01] border-emerald-500/10 text-muted-foreground/60" 
                              : isBlocked
                                ? "bg-rose-500/[0.01] border-rose-500/10 text-rose-400/90"
                                : isProgress
                                  ? "bg-primary/[0.01] border-primary/25 text-white"
                                  : "bg-white/[0.01] border-white/5 hover:border-white/10 hover:bg-white/[0.02] text-white/90"
                          }`}
                        >
                          <button
                            onClick={() => handleTaskToggle(selectedPlan, task.id)}
                            className="mt-0.5 flex-shrink-0 transition text-muted-foreground hover:text-white"
                          >
                            {isCompleted ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400 fill-emerald-500/10" />
                            ) : (
                              <Circle className="w-4 h-4 text-muted-foreground/40 hover:text-white" />
                            )}
                          </button>
                          
                          <div className="flex-1 min-w-0">
                            <span className={`text-[12px] font-medium leading-relaxed block ${isCompleted ? "line-through text-muted-foreground/40" : "text-white"}`}>
                              {task.title}
                            </span>
                            
                            {/* Task Metadata */}
                            <div className="flex items-center gap-3 mt-2 text-[9px] font-mono text-muted-foreground/60">
                              <span className="flex items-center gap-1 uppercase">
                                {getOwnerBadge(task.owner)}
                              </span>
                              <span>·</span>
                              <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                                <button 
                                  onClick={() => handleTaskStatusChange(selectedPlan, task.id, "in_progress")}
                                  className={`px-2 py-0.5 border border-white/10 rounded text-[8px] font-mono uppercase tracking-wider transition ${isProgress ? "bg-primary text-white border-primary/20" : "bg-white/5 hover:bg-white/10 hover:text-white"}`}
                                >
                                  In Progress
                                </button>
                                <button 
                                  onClick={() => handleTaskStatusChange(selectedPlan, task.id, "blocked")}
                                  className={`px-2 py-0.5 border border-white/10 rounded text-[8px] font-mono uppercase tracking-wider transition ${isBlocked ? "bg-rose-500/20 text-rose-300 border-rose-500/30" : "bg-white/5 hover:bg-white/10 hover:text-white"}`}
                                >
                                  Block
                                </button>
                                <button 
                                  onClick={() => handleTaskStatusChange(selectedPlan, task.id, "pending")}
                                  className={`px-2 py-0.5 border border-white/10 rounded text-[8px] font-mono uppercase tracking-wider transition ${task.status === "pending" ? "bg-white/10 text-white" : "bg-white/5 hover:bg-white/10 hover:text-white"}`}
                                >
                                  Reset
                                </button>
                              </div>
                            </div>
                          </div>
                        </div>
                      )
                    })
                  )}
                </div>
              </div>

              {/* Side Cards: KPIs, Risks, Dependencies */}
              <div className="space-y-6">
                
                {/* KPIs Target */}
                <div className="space-y-2">
                  <h3 className="font-mono text-[10px] text-primary font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <TrendingUp className="w-4 h-4 text-primary" />
                    Target KPIs
                  </h3>
                  <div className="glass-panel border border-white/5 rounded-xl p-4.5 space-y-3 shadow-md">
                    {selectedPlan.kpis.map((kpi, idx) => (
                      <div key={idx} className="border-b border-white/5 last:border-0 pb-3 last:pb-0">
                        <div className="text-[9px] font-mono text-muted-foreground uppercase tracking-wider">{kpi.metric}</div>
                        <div className="flex items-baseline justify-between mt-1">
                          <span className="text-xs font-semibold text-primary">{kpi.target}</span>
                          <span className="text-[9px] font-mono text-muted-foreground/60">{kpi.timeframe}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Dependencies */}
                <div className="space-y-2">
                  <h3 className="font-mono text-[10px] text-primary font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <Link2 className="w-4 h-4 text-primary" />
                    Dependencies
                  </h3>
                  <div className="glass-panel border border-white/5 rounded-xl p-4.5 space-y-2 shadow-md">
                    {selectedPlan.dependencies.length === 0 ? (
                      <p className="text-[10px] font-sans text-muted-foreground italic">No checklist dependencies declared.</p>
                    ) : (
                      selectedPlan.dependencies.map((dep, idx) => (
                        <div key={idx} className="flex items-start gap-1.5 text-[11px] text-muted-foreground leading-relaxed">
                          <span className="text-primary mt-1 flex-shrink-0">•</span>
                          <span className="font-sans text-xs text-white/95">{dep}</span>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                {/* Risks mitigation */}
                <div className="space-y-2">
                  <h3 className="font-mono text-[10px] text-rose-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldAlert className="w-4 h-4 text-rose-400" />
                    Risks & mitigations
                  </h3>
                  <div className="glass-panel border border-white/5 rounded-xl p-4.5 space-y-3 shadow-md">
                    {selectedPlan.risks.length === 0 ? (
                      <p className="text-[10px] font-sans text-muted-foreground italic">No identified risks.</p>
                    ) : (
                      selectedPlan.risks.map((risk, idx) => (
                        <div key={idx} className="border-b border-white/5 last:border-0 pb-3 last:pb-0 space-y-1">
                          <div className="text-[10px] font-mono uppercase tracking-wider text-rose-300 flex items-center gap-1">
                            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                            <span>{risk.risk}</span>
                          </div>
                          <p className="text-xs text-muted-foreground leading-relaxed pl-4 font-sans">
                            Mitigation: {risk.mitigation}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </div>

              </div>
            </div>
            
          </div>
        ) : (
          <div className="flex-grow flex flex-col items-center justify-center p-6 text-center">
            <ClipboardList className="w-10 h-10 text-muted-foreground/25 mb-4 animate-pulse" />
            <h2 className="font-serif text-base font-normal text-white mb-1">Select an Action Plan</h2>
            <p className="text-xs text-muted-foreground max-w-sm">
              Click a plan from the left list or approve a new marketing signal to compile a dynamic checklist.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
