"use client"

import { useEffect, useState, useCallback } from "react"
import { CheckSquare, ArrowRight, Sparkles, Check, X, RefreshCw, Loader2, Award, Zap, Calendar, TrendingUp } from "lucide-react"
import { listOpportunities, updateOpportunity } from "@/lib/api"
import type { Opportunity } from "@/lib/api"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { WelcomeOnboarding } from "@/components/shared/WelcomeOnboarding"
import { getAgentConfig } from "@/lib/constants/agents"
import Link from "next/link"

export default function ApprovalPage() {
  const {
    projects,
    activeProject,
    loading: projectsLoading,
  } = useActiveProject()

  const [opportunities, setOpportunities] = useState<Opportunity[]>([])
  const [dataLoading, setDataLoading] = useState(true)
  const [actioningId, setActioningId] = useState<string | null>(null)
  const [feedbackMsg, setFeedbackMsg] = useState<{ id: string; type: "success" | "dismissed"; text: string } | null>(null)

  const loadOpportunities = useCallback(async () => {
    if (!activeProject) {
      setOpportunities([])
      setDataLoading(false)
      return
    }
    setDataLoading(true)
    try {
      const res = await listOpportunities("active", activeProject.id)
      setOpportunities(res.opportunities || [])
    } catch (e) {
      console.error("Failed to load approvals:", e)
    } finally {
      setDataLoading(false)
    }
  }, [activeProject])

  useEffect(() => {
    loadOpportunities()
  }, [loadOpportunities])

  const handleApprove = async (id: string, name: string) => {
    setActioningId(id)
    try {
      await updateOpportunity(id, { status: "completed" })
      setFeedbackMsg({ id, type: "success", text: `Approved campaign action: "${name}"` })
      setTimeout(() => {
        setFeedbackMsg(null)
        loadOpportunities()
      }, 5000)
    } catch (e) {
      console.error("Failed to approve opportunity:", e)
    } finally {
      setActioningId(null)
    }
  }

  const handleDismiss = async (id: string, name: string) => {
    setActioningId(id)
    try {
      await updateOpportunity(id, { status: "dismissed" })
      setFeedbackMsg({ id, type: "dismissed", text: `Dismissed recommendation: "${name}"` })
      setTimeout(() => {
        setFeedbackMsg(null)
        loadOpportunities()
      }, 2000)
    } catch (e) {
      console.error("Failed to dismiss opportunity:", e)
    } finally {
      setActioningId(null)
    }
  }

  const loading = projectsLoading || dataLoading

  if (loading) {
    return (
      <div className="flex-grow flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-5 h-5 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground">Loading approvals queue...</div>
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
    <div className="flex-grow overflow-y-auto px-8 py-8 bg-background text-foreground">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8 flex items-center justify-between border-b border-border pb-5">
          <div>
            <h1 className="text-2xl font-semibold mb-1 text-foreground flex items-center gap-2">
              <CheckSquare className="w-6 h-6 text-primary" /> Approvals Board
            </h1>
            <p className="text-xs text-muted-foreground max-w-xl">
              Verify, edit, or approve AI-generated campaign actions. Approved actions are queued for channel execution.
            </p>
          </div>
          <button
            onClick={loadOpportunities}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-card hover:bg-muted border border-border rounded-lg text-xs text-foreground font-medium transition"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh
          </button>
        </div>

        {opportunities.length === 0 ? (
          <div className="bg-card border border-border rounded-2xl p-8 max-w-lg mx-auto text-center mt-12 shadow-lg">
            <div className="w-12 h-12 mx-auto rounded-xl bg-primary/10 flex items-center justify-center mb-4">
              <CheckSquare className="w-5 h-5 text-primary animate-pulse" />
            </div>
            <h3 className="text-base font-semibold text-foreground mb-2">No pending approvals</h3>
            <p className="text-xs text-muted-foreground mb-6 leading-relaxed">
              Specialist agents generate strategic opportunities during site scans or in the Brief Room.
              Add a URL to run a scan or coordinate a brief with Nexus to populate this queue.
            </p>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition shadow-md"
            >
              Brief the Swarm <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {opportunities.map((opp) => {
              const proposingAgent = getAgentConfig(opp.proposed_by)
              const isActioning = actioningId === opp.id
              const isFeedback = feedbackMsg && feedbackMsg.id === opp.id

              if (isFeedback) {
                return (
                  <div
                    key={opp.id}
                    className={`border rounded-xl p-6 text-center animate-fade-in transition-all flex flex-col items-center justify-center gap-3 ${
                      feedbackMsg.type === "success"
                        ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400"
                        : "bg-amber-500/10 border-amber-500/30 text-amber-400"
                    }`}
                  >
                    <div className="w-8 h-8 rounded-full bg-current/10 flex items-center justify-center">
                      {feedbackMsg.type === "success" ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <X className="w-4 h-4" />
                      )}
                    </div>
                    <p className="text-xs font-semibold">{feedbackMsg.text}</p>
                    {feedbackMsg.type === "success" && (
                      <Link
                        href="/action-plans"
                        className="px-3.5 py-1.5 bg-emerald-400 hover:bg-emerald-350 text-black text-[10px] font-bold rounded-lg transition shadow-md flex items-center gap-1"
                      >
                        <span>View Execution Action Plan</span>
                        <ArrowRight className="w-3 h-3" />
                      </Link>
                    )}
                  </div>
                )
              }

              return (
                <div
                  key={opp.id}
                  className="bg-card border border-border rounded-xl p-5 hover:border-primary/20 transition flex flex-col justify-between shadow-sm relative group"
                >
                  {/* Top Header */}
                  <div className="flex items-center justify-between mb-3 border-b border-border/40 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-primary/10 text-primary text-[10px] font-semibold rounded uppercase tracking-wider">
                        {opp.category}
                      </span>
                      <span className="text-[10px] text-muted-foreground/60">·</span>
                      <div className="flex items-center gap-1">
                        <div
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ backgroundColor: proposingAgent.color }}
                        />
                        <span className="text-[10px] text-muted-foreground">
                          Proposed by <span className="font-semibold text-foreground">{proposingAgent.name}</span>
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 text-emerald-400 font-semibold bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded text-[10px] tracking-wider">
                      <TrendingUp className="w-3 h-3" />
                      RICE {opp.rice_score.toFixed(2)}
                    </div>
                  </div>

                  {/* Title & Desc */}
                  <div className="mb-4">
                    <h3 className="font-bold text-sm mb-1.5 text-foreground leading-snug">
                      {opp.title}
                    </h3>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {opp.description}
                    </p>
                  </div>

                  {/* Badges and Metrics */}
                  <div className="flex flex-wrap items-center gap-2 mb-4 bg-muted/40 p-2.5 rounded-lg border border-border/30">
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground font-medium">
                      <Zap className="w-3 h-3 text-amber-500" />
                      Impact: <span className="text-foreground capitalize">{opp.expected_impact}</span>
                    </div>
                    <span className="text-muted-foreground/40 text-[10px] font-mono">·</span>
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground font-medium">
                      <Award className="w-3 h-3 text-sky-500" />
                      Effort: <span className="text-foreground capitalize">{opp.effort}</span>
                    </div>
                    <span className="text-muted-foreground/40 text-[10px] font-mono">·</span>
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground font-medium">
                      <Calendar className="w-3 h-3 text-purple-500" />
                      Timeframe: <span className="text-foreground">{opp.timeframe}</span>
                    </div>
                    <span className="text-muted-foreground/40 text-[10px] font-mono">·</span>
                    <div className="flex items-center gap-1 text-[10px] text-muted-foreground font-medium">
                      Confidence: <span className="text-foreground font-semibold">{(opp.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  {/* Action Bar */}
                  <div className="flex flex-col sm:flex-row gap-2 mt-2 pt-3 border-t border-border/40 justify-between items-stretch sm:items-center">
                    <div className="text-[10px] text-muted-foreground italic mb-2 sm:mb-0">
                      Endorsed by {opp.endorsed_by.join(", ").toUpperCase()}
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleDismiss(opp.id, opp.title)}
                        disabled={isActioning}
                        className="px-3 py-1.5 border border-border hover:bg-muted text-muted-foreground hover:text-foreground text-xs font-semibold rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-1"
                      >
                        <X className="w-3.5 h-3.5" /> Dismiss
                      </button>
                      <Link
                        href={`/chat?opportunity=${opp.id}`}
                        className="px-3 py-1.5 border border-primary/20 hover:border-primary/40 text-primary text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1 bg-primary/5 hover:bg-primary/10"
                      >
                        Brief Swarm <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                      <button
                        onClick={() => handleApprove(opp.id, opp.title)}
                        disabled={isActioning}
                        className="px-4 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-1 shadow-md"
                      >
                        {isActioning ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Check className="w-3.5 h-3.5" />
                        )}
                        {isActioning ? "Approving..." : "Approve Action"}
                      </button>
                    </div>
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
