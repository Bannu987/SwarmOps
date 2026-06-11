"use client"

import { useState, useRef, useEffect } from "react"
import { sendChat, uploadFile, streamChat, listSignals, listOpportunities } from "@/lib/api"
import { UserMessage } from "./UserMessage"
import { AgentMessageCard } from "./AgentMessageCard"
import { ChatInput } from "./ChatInput"
import { LoadingMessage } from "./LoadingMessage"
import { EmptyState } from "./EmptyState"
import type { Message, FileAttachment } from "@/types"
import { useSearchParams } from "next/navigation"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { WelcomeOnboarding } from "@/components/shared/WelcomeOnboarding"
import { Loader2, Sparkles } from "lucide-react"
import { AGENTS } from "@/lib/constants/agents"
import { StrategyBriefPanel } from "./StrategyBriefPanel"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://swarmops.onrender.com"

export function ChatInterface() {
  const {
    projects,
    activeProject,
    loading: projectsLoading,
  } = useActiveProject()

  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [showBriefs, setShowBriefs] = useState(false)
  const [pendingAttachments, setPendingAttachments] = useState<FileAttachment[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)
  
  const searchParams = useSearchParams()
  const [initiated, setInitiated] = useState(false)
  const [clickedSignalContext, setClickedSignalContext] = useState<any>(null)

  // Backend connection checking states
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "waking" | "offline" | "misconfigured">("checking")
  const [retryCount, setRetryCount] = useState(0)
  const [healthError, setHealthError] = useState<string | null>(null)

  useEffect(() => {
    checkHealth(0)
  }, [])

  const checkHealth = async (attempt = 0) => {
    if (!API_URL || (API_URL.includes("localhost") && typeof window !== "undefined" && !window.location.hostname.includes("localhost"))) {
      if (typeof window !== "undefined" && !window.location.hostname.includes("localhost")) {
        setBackendStatus("misconfigured")
        setHealthError("CORS/Configuration Error: Production client is trying to connect to a localhost API.")
        return
      }
    }
    
    try {
      new URL(API_URL)
    } catch {
      setBackendStatus("misconfigured")
      setHealthError("Configuration Error: Invalid backend API URL.")
      return
    }

    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 6000) // 6 seconds timeout
      
      const res = await fetch(`${API_URL}/health`, {
        signal: controller.signal
      })
      clearTimeout(timeoutId)
      
      if (res.ok) {
        setBackendStatus("online")
        setRetryCount(0)
        setHealthError(null)
      } else {
        if (res.status === 404) {
          throw new Error("404: Backend health endpoint missing or wrong API URL.")
        } else if (res.status === 502 || res.status === 503) {
          throw new Error("502/503: Render backend unavailable or waking.")
        } else {
          throw new Error(`HTTP ${res.status}: Server returned an error status.`)
        }
      }
    } catch (err: any) {
      console.warn("Backend health ping failed:", err)
      let customError = "Backend is waking or overloaded."
      
      if (err.name === "AbortError" || (err.message && err.message.includes("abort"))) {
        customError = "Timeout: Backend is waking or overloaded."
      } else if (err instanceof TypeError || (err.message && err.message.toLowerCase().includes("fetch"))) {
        customError = "CORS/Network error: Browser blocked backend request. Check CORS."
      } else if (err.message) {
        customError = err.message
      }

      setHealthError(customError)
      
      if (attempt < 5) {
        setBackendStatus("waking")
        setRetryCount(attempt + 1)
        setTimeout(() => {
          checkHealth(attempt + 1)
        }, 10000)
      } else {
        setBackendStatus("offline")
      }
    }
  }

  const handleManualRetry = () => {
    setBackendStatus("checking")
    setRetryCount(0)
    checkHealth(0)
  }

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    })
  }, [messages, loading])

  useEffect(() => {
    if (initiated) return
    const oppId = searchParams.get("opportunity")
    const sigId = searchParams.get("signal")
    const agentId = searchParams.get("agent")
    
    if (oppId) {
      setInitiated(true)
      listOpportunities("active").then((res) => {
        const opp = res.opportunities?.find((o) => o.id === oppId)
        if (opp) {
          handleSend(`Apply this opportunity: "${opp.title}"\nCategory: ${opp.category}\nRecommended action: ${opp.recommended_action}`)
        }
      })
    } else if (sigId) {
      setInitiated(true)
      listSignals("active").then((res) => {
        const sig = res.signals?.find((s) => s.id === sigId)
        if (sig) {
          const signalObj = {
            signal_id: sig.id,
            signal_type: sig.signal_type || sig.category,
            title: sig.title,
            description: sig.description,
            detector: sig.source_agent || "seo",
            category: sig.category,
            severity: sig.severity,
            url: sig.source_detail || null,
            evidence: sig.evidence,
            project_id: activeProject?.id,
            workspace_id: activeProject?.id
          }
          setClickedSignalContext(signalObj)
          handleSend(
            `Analyze and address this signal: "${sig.title}"\nDescription: ${sig.description}\nDetected by: ${sig.source_agent}`,
            signalObj
          )
        }
      })
    } else if (agentId) {
      setInitiated(true)
      const agentObj = Object.values(AGENTS).find((a) => a.id.toLowerCase() === agentId.toLowerCase())
      if (agentObj) {
        handleSend(`Hello ${agentObj.name} Specialist. Please deploy your advanced scanning systems and run a custom audit on my project, then output your latest strategic recommendations.`)
      }
    }
  }, [searchParams, initiated])

  const handleSend = async (text: string, signalContextOverride?: any) => {
    const currentSignalContext = signalContextOverride || clickedSignalContext
    setClickedSignalContext(null)
    const assistantMsgId = Math.random().toString(36).substring(7)
    
    const userMsg: Message = {
      role: "user",
      content: text,
      attachments: pendingAttachments.length > 0 ? pendingAttachments : undefined,
      timestamp: Date.now(),
    }
    
    const initialAssistantMsg: Message = {
      id: assistantMsgId,
      role: "assistant",
      content: "SwarmOps is preparing the brief...",
      agents_used: ["nexus"],
      timestamp: Date.now(),
    }
    
    setMessages((prev) => [...prev, userMsg, initialAssistantMsg])
    setPendingAttachments([])
    setLoading(true)

    let accumulatedContent = ""
    let agentsUsed: string[] = ["nexus"]
    let workflowName: string | null = null
    let confidence: number | undefined = undefined
    let latencyMs: number | undefined = undefined

    let eventReceived = false
    const timeoutId = setTimeout(() => {
      if (!eventReceived) {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId && msg.content === "SwarmOps is preparing the brief..."
              ? {
                  ...msg,
                  content: "Signal analysis stream did not return events. Please retry.",
                }
              : msg
          )
        )
        setLoading(false)
      }
    }, 60000)

    try {
      await streamChat(text, "default", (event) => {
        eventReceived = true
        console.log("[FRONTEND SSE EVENT]", {
          type: event.type,
          keys: Object.keys(event),
          answer_len: event.answer?.length,
          decision_len: event.decision?.length,
          rationale_len: event.rationale?.length
        })

        if (event.type === "workflow.started") {
          workflowName = event.workflow
          if (event.agents) {
            agentsUsed = event.agents
          }
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    workflow: workflowName,
                    agents_used: agentsUsed,
                    content: `Swarm initiated: **${(workflowName || "single_agent").replace(/_/g, " ").toUpperCase()}**\n\nCoordinating specialized agents...`,
                  }
                : msg
            )
          )
        } else if (event.type === "agent.started") {
          const agentId = event.agent_id
          if (!agentsUsed.includes(agentId)) {
            agentsUsed = [...agentsUsed, agentId]
          }
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    agents_used: agentsUsed,
                    content: `${msg.content}\n\n🤖 **${agentId.toUpperCase()} specialist** is joining the workspace...`,
                  }
                : msg
            )
          )
        } else if (event.type === "agent.responded") {
          const agentId = event.agent_id
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: `${msg.content}\n\n✓ **${agentId.toUpperCase()} specialist** completed analysis:\n> *${event.conclusion}*`,
                  }
                : msg
            )
          )
        } else if (event.type === "agent.challenged") {
          const agentId = event.agent_id
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: `${msg.content}\n\n⚔️ **${agentId.toUpperCase()} specialist** challenged the consensus! Initiating debate...`,
                  }
                : msg
            )
          )
        } else if (event.type === "confidence.shifted") {
          const agentId = event.agent_id
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: `${msg.content}\n\n⚖️ Confidence alignment shift for **${agentId.toUpperCase()}**: **${(event.from * 100).toFixed(0)}%** → **${(event.to * 100).toFixed(0)}%** (${event.reason})`,
                  }
                : msg
            )
          )
        } else if (event.type === "decision.reached") {
          confidence = event.confidence
          latencyMs = event.latency_ms
          
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: (event.workflow === "signal_analysis" || event.is_signal_analysis)
                      ? msg.content
                      : (event.rationale || event.decision || msg.content),
                    confidence: confidence,
                    latency_ms: latencyMs,
                    agents_used: event.agents_consulted || msg.agents_used,
                  }
                : msg
            )
          )
        } else if (event.type === "final.answer") {
          accumulatedContent = event.answer || event.decision || event.final_answer || event.message || event.content || "";
          
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: accumulatedContent,
                  }
                : msg
            )
          )
        }
      }, activeProject?.id, currentSignalContext)
      clearTimeout(timeoutId)
    } catch (err: any) {
      clearTimeout(timeoutId)

      console.error("SSE stream failed:", err)
      const isOnline = backendStatus === "online"
      const isCORS = err instanceof TypeError || (err.message && (err.message.toLowerCase().includes("fetch") || err.message.toLowerCase().includes("cors") || err.message.toLowerCase().includes("preflight")))
      
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content: isOnline 
                  ? "Backend is online, but streaming failed. Falling back to non-streaming response..."
                  : isCORS
                    ? "Browser blocked the backend request. Check CORS configuration for this frontend domain or verify the backend is active."
                    : "Connection error. The backend may be waking up (free tier sleeps after 15 min). Try again in 30 seconds.",
              }
            : msg
        )
      )

      if (isOnline) {
        // Fallback to standard HTTP POST request
        try {
          const res = await sendChat(text, "default", activeProject?.id, currentSignalContext)
          setMessages((prev) =>

            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: res.response || "No response received.",
                    agents_used: res.agents_used || msg.agents_used,
                    confidence: res.confidence,
                    latency_ms: res.latency_ms,
                  }
                : msg
            )
          )
        } catch (fallbackErr: any) {
          console.error("Fallback also failed:", fallbackErr)
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: "Fallback failed: Backend rejected the request. Check CORS/auth configuration.",
                  }
                : msg
            )
          )
        }
      }
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    setUploading(true)
    try {
      const result = await uploadFile(file)
      if (result.success) {
        const attachment: FileAttachment = {
          filename: result.filename,
          file_type: result.file_type,
          file_size: result.file_size,
          word_count: result.word_count,
          summary: result.summary,
        }
        setPendingAttachments((prev) => [...prev, attachment])

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `📎 **${result.filename}** uploaded (${(result.file_size / 1024).toFixed(1)}KB)\n\n${result.summary}\n\nAsk me anything about this file.`,
            timestamp: Date.now(),
          },
        ])
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Upload failed: ${result.error || "unknown error"}`,
            timestamp: Date.now(),
          },
        ])
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "unknown error"
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Upload failed: ${msg}`,
          timestamp: Date.now(),
        },
      ])
    } finally {
      setUploading(false)
    }
  }

  // Handle Workspace empty states
  if (projectsLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-5 h-5 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground">Loading Brief Room workspace...</div>
        </div>
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="flex-1 overflow-y-auto bg-background flex items-center justify-center">
        <WelcomeOnboarding />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-transparent">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/5 bg-white/[0.02] flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl md:text-2xl font-serif font-normal tracking-tight text-white">Boardroom Briefing</h1>
            <span className="text-[9px] font-mono text-primary bg-primary/10 border border-primary/25 px-2 py-0.5 rounded-full uppercase tracking-wider">Decision Swarm</span>
          </div>
          <p className="text-[10px] text-muted-foreground mt-1 max-w-lg leading-snug">
            Engage Nexus and specialized marketing intelligence agents to analyze campaign telemetry, SEO anomalies, and strategic roadmaps.
          </p>
        </div>

        <div className="flex items-center gap-4 flex-shrink-0">
          {/* Strategy Brief Button */}
          {activeProject && (
            <button
              onClick={() => setShowBriefs(!showBriefs)}
              className="flex items-center gap-1.5 px-3 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-mono text-[10px] uppercase tracking-wider rounded-lg transition-all duration-300 shadow-sm"
            >
              <Sparkles className="w-3 h-3 text-primary animate-pulse" />
              <span>Strategy Briefs</span>
            </button>
          )}

          {/* Dynamic Status Indicator */}
          <div className="font-mono text-[10px]">
            {backendStatus === "checking" && (
              <div className="flex items-center gap-1.5 text-muted-foreground">
                <Loader2 className="w-3 h-3 animate-spin text-primary" />
                <span>SYNCING</span>
              </div>
            )}
            {backendStatus === "online" && (
              <div className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20 uppercase font-semibold">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span>ONLINE</span>
              </div>
            )}
            {backendStatus === "waking" && (
              <div className="flex items-center gap-1.5 text-amber-500 bg-amber-500/10 px-2.5 py-0.5 rounded-full border border-amber-500/20 uppercase font-semibold">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-ping" />
                <span>WAKING ({retryCount}/6)</span>
              </div>
            )}
            {backendStatus === "offline" && (
              <div className="flex items-center gap-1.5 text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded-full border border-rose-500/20 uppercase font-semibold">
                <div className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                <span>OFFLINE</span>
              </div>
            )}
            {backendStatus === "misconfigured" && (
              <div className="flex items-center gap-1.5 text-rose-400 bg-rose-500/10 px-2.5 py-0.5 rounded-full border border-rose-500/20 uppercase font-semibold">
                <div className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                <span>CONFIG ERROR</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Backend Status Warning Banners */}
      {backendStatus === "waking" && (
        <div className="bg-amber-500/10 border-b border-amber-500/30 px-6 py-2.5 flex items-center justify-between text-amber-500 text-[11px] animate-fade-in animate-pulse">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-amber-500 animate-ping flex-shrink-0" />
            <span>{healthError || "Render free tier is waking up. This can take 30–60 seconds. We'll retry automatically."} (Attempt {retryCount}/6)</span>
          </div>
          <button
            onClick={handleManualRetry}
            className="px-2 py-0.5 bg-amber-500 hover:bg-amber-400 text-black font-semibold rounded text-[10px] transition flex-shrink-0"
          >
            Retry now
          </button>
        </div>
      )}

      {backendStatus === "offline" && (
        <div className="bg-destructive/10 border-b border-destructive/30 px-6 py-2.5 flex items-center justify-between text-destructive text-[11px] animate-fade-in">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-destructive flex-shrink-0" />
            <span>{healthError || "Backend is offline or unreachable. Please verify that your backend service is running."}</span>
          </div>
          <button
            onClick={handleManualRetry}
            className="px-2 py-0.5 bg-destructive hover:bg-destructive/90 text-white font-semibold rounded text-[10px] transition flex-shrink-0"
          >
            Retry now
          </button>
        </div>
      )}

      {backendStatus === "misconfigured" && (
        <div className="bg-destructive/10 border-b border-destructive/30 px-6 py-2.5 text-destructive text-[11px] flex items-center gap-2 animate-fade-in">
          <div className="w-2 h-2 rounded-full bg-destructive flex-shrink-0" />
          <span>{healthError || "Production API URL is not configured correctly. Check NEXT_PUBLIC_API_URL in Netlify."}</span>
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-grow overflow-y-auto px-6 py-6 bg-transparent">
        {messages.length === 0 ? (
          <EmptyState onQuickAction={handleSend} />
        ) : (
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.map((msg, i) =>
              msg.role === "user" ? (
                <UserMessage key={i} message={msg} />
              ) : (
                <AgentMessageCard key={i} message={msg} />
              )
            )}
            {loading && <LoadingMessage />}
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        onFileUpload={handleFileUpload}
        loading={loading}
        uploading={uploading}
      />

      {showBriefs && activeProject && (
        <StrategyBriefPanel
          projectId={activeProject.id}
          onClose={() => setShowBriefs(false)}
        />
      )}
    </div>
  )
}
