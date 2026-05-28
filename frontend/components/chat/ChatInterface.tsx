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

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [pendingAttachments, setPendingAttachments] = useState<FileAttachment[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)
  
  const searchParams = useSearchParams()
  const [initiated, setInitiated] = useState(false)

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
          handleSend(`Analyze and address this signal: "${sig.title}"\nDescription: ${sig.description}\nDetected by: ${sig.source_agent}`)
        }
      })
    }
  }, [searchParams, initiated])

  const handleSend = async (text: string) => {
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

    try {
      await streamChat(text, "default", (event) => {
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
          accumulatedContent = event.rationale || event.decision
          
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: accumulatedContent,
                    confidence: confidence,
                    latency_ms: latencyMs,
                    agents_used: event.agents_consulted || msg.agents_used,
                  }
                : msg
            )
          )
        }
      })
    } catch {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMsgId
            ? {
                ...msg,
                content:
                  "Connection error. The backend may be waking up (free tier sleeps after 15 min). Try again in 30 seconds.",
              }
            : msg
        )
      )
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

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-3 border-b border-border flex items-center justify-between">
        <div>
          <h1 className="font-semibold">Command Center</h1>
          <p className="text-xs text-muted-foreground">Orchestrated by Nexus CMO</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Online
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <EmptyState onQuickAction={handleSend} />
        ) : (
          <div className="max-w-3xl mx-auto space-y-5">
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
    </div>
  )
}
