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
      <div className="max-w-5xl mx-auto animate-fade-in">
        <div className="mb-8 flex items-center justify-between border-b border-border/60 pb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <CheckSquare className="w-5 h-5 text-primary" />
              <h1 className="text-2xl font-serif font-normal tracking-tight text-foreground">
                Approvals Board
              </h1>
            </div>
            <p className="text-xs text-muted-foreground max-w-xl">
              Verify, edit, or approve AI-generated campaign actions. Approved actions are queued for channel execution.
            </p>
          </div>
          <button
            onClick={loadOpportunities}
            className="flex items-center gap-1.5 px-3 py-1.5 bg-card/85 hover:bg-card border border-border/80 hover:border-primary/45 rounded text-xs text-foreground font-medium transition duration-300"
          >
            <RefreshCw className="w-3.5 h-3.5 text-primary/90" />
            <span className="font-sans text-[11px] font-medium">Sync Queue</span>
          </button>
        </div>

        {opportunities.length === 0 ? (
          <div className="bg-card/65 border border-border/40 rounded-xl p-8 max-w-lg mx-auto text-center mt-12 shadow-sm">
            <div className="w-12 h-12 mx-auto rounded-lg bg-primary/10 flex items-center justify-center mb-4">
              <CheckSquare className="w-5 h-5 text-primary animate-pulse" />
            </div>
            <h3 className="text-lg font-serif text-foreground mb-2">No pending approvals</h3>
            <p className="text-xs text-muted-foreground mb-6 leading-relaxed">
              Specialist agents generate strategic opportunities during site scans or in the Brief Room.
              Add a URL to run a scan or coordinate a brief with Nexus to populate this queue.
            </p>
            <Link
              href="/chat"
              className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary/95 text-primary-foreground text-[10px] font-mono uppercase tracking-wider rounded transition shadow-md"
            >
              <span>Brief the Swarm</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-5">
            {opportunities.map((opp) => {
              const proposingAgent = getAgentConfig(opp.proposed_by)
              const isActioning = actioningId === opp.id
              const isFeedback = feedbackMsg && feedbackMsg.id === opp.id

              if (isFeedback) {
                return (
                  <div
                    key={opp.id}
                    className={`border rounded-xl p-6 text-center animate-fade-in transition-all flex flex-col items-center justify-center gap-3 shadow-inner ${
                      feedbackMsg.type === "success"
                        ? "bg-[#a3b899]/10 border-[#a3b899]/30 text-[#a3b899]"
                        : "bg-[#d76f57]/10 border-[#d76f57]/30 text-[#d76f57]"
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
                        className="px-4 py-2 bg-[#a3b899] hover:bg-[#a3b899]/90 text-black text-[10px] font-mono uppercase tracking-wider rounded transition shadow-md flex items-center gap-1.5"
                      >
                        <span>View Action Plan</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    )}
                  </div>
                )
              }

              return (
                <div
                  key={opp.id}
                  className="bg-card/65 border border-border/40 rounded-xl p-6 hover:border-primary/35 transition-all duration-300 flex flex-col justify-between shadow-sm relative group"
                >
                  {/* Top Header */}
                  <div className="flex items-center justify-between mb-3 border-b border-border/30 pb-3">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 bg-primary/10 border border-primary/20 text-primary text-[9px] font-mono uppercase tracking-wider rounded">
                        {opp.category}
                      </span>
                      <span className="text-[10px] text-muted-foreground/40">·</span>
                      <div className="flex items-center gap-1.5">
                        <div
                          className="w-1.5 h-1.5 rounded-full"
                          style={{ backgroundColor: proposingAgent.color }}
                        />
                        <span className="text-[10px] font-mono text-muted-foreground">
                          PROPOSED BY <span className="font-semibold text-foreground" style={{ color: proposingAgent.color }}>{proposingAgent.name.toUpperCase()}</span>
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1.5 text-primary bg-primary/5 border border-primary/20 px-2 py-0.5 rounded text-[10px] font-mono tracking-wider">
                      <TrendingUp className="w-3 h-3 text-primary/80" />
                      RICE {opp.rice_score.toFixed(2)}
                    </div>
                  </div>

                  {/* Title & Desc */}
                  <div className="mb-4">
                    <h3 className="font-serif font-normal text-lg mb-1.5 text-foreground leading-snug">
                      {opp.title}
                    </h3>
                    <p className="text-xs text-muted-foreground/90 leading-relaxed max-w-3xl">
                      {opp.description}
                    </p>
                  </div>

                  {/* Badges and Metrics */}
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2 mb-4 bg-card/45 p-3 rounded-lg border border-border/35 text-[10px] font-mono uppercase tracking-wider text-muted-foreground/80">
                    <div className="flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-primary/95" />
                      <span>IMPACT:</span>
                      <span className="text-foreground font-semibold">{opp.expected_impact}</span>
                    </div>
                    <span className="text-muted-foreground/30 font-mono">·</span>
                    <div className="flex items-center gap-1.5">
                      <Award className="w-3.5 h-3.5 text-primary/80" />
                      <span>EFFORT:</span>
                      <span className="text-foreground font-semibold">{opp.effort}</span>
                    </div>
                    <span className="text-muted-foreground/30 font-mono">·</span>
                    <div className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-primary/80" />
                      <span>TIMEFRAME:</span>
                      <span className="text-foreground font-semibold">{opp.timeframe}</span>
                    </div>
                    <span className="text-muted-foreground/30 font-mono">·</span>
                    <div className="flex items-center gap-1.5">
                      <span>CONFIDENCE:</span>
                      <span className="text-foreground font-semibold">{(opp.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>

                  {/* Action Bar */}
                  <div className="flex flex-col sm:flex-row gap-4 mt-2 pt-4 border-t border-border/30 justify-between items-stretch sm:items-center">
                    <div className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground/75">
                      ENDORSED BY: <span className="text-foreground/90">{opp.endorsed_by.join(", ").toUpperCase()}</span>
                    </div>
                    
                    <div className="flex gap-2.5">
                      <button
                        onClick={() => handleDismiss(opp.id, opp.title)}
                        disabled={isActioning}
                        className="px-3.5 py-1.5 border border-border/80 hover:bg-card hover:text-foreground text-muted-foreground font-mono text-[10px] uppercase tracking-wider rounded transition duration-300 disabled:opacity-50 flex items-center justify-center gap-1"
                      >
                        <X className="w-3.5 h-3.5" />
                        <span>Dismiss</span>
                      </button>
                      <Link
                        href={`/chat?opportunity=${opp.id}`}
                        className="px-3.5 py-1.5 border border-primary/25 hover:border-primary/50 text-primary bg-primary/5 hover:bg-primary/10 font-mono text-[10px] uppercase tracking-wider rounded transition duration-300 flex items-center justify-center gap-1"
                      >
                        <span>Brief Swarm</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                      <button
                        onClick={() => handleApprove(opp.id, opp.title)}
                        disabled={isActioning}
                        className="px-4.5 py-1.5 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded transition-all duration-300 disabled:opacity-50 flex items-center justify-center gap-1.5 shadow-md hover:scale-[1.01] active:scale-100"
                      >
                        {isActioning ? (
                          <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        ) : (
                          <Check className="w-3.5 h-3.5" />
                        )}
                        <span>{isActioning ? "Approving..." : "Approve Action"}</span>
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
