"use client"

import { useState } from "react"
import { Markdown } from "./Markdown"
import { getAgentConfig } from "@/lib/constants/agents"
import { Copy, Check, ChevronDown, ChevronUp, Clock } from "lucide-react"
import type { Message } from "@/types"

interface Props {
  message: Message
}

export function AgentMessageCard({ message }: Props) {
  const [copied, setCopied] = useState(false)
  const [showDetails, setShowDetails] = useState(false)

  const primaryAgent = message.agents_used?.[0] || "nexus"
  const agentCfg = getAgentConfig(primaryAgent)
  const hasMultiple = (message.agents_used?.length || 0) > 1

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      className="bg-card border border-border rounded-2xl overflow-hidden animate-slide-up"
      style={{ borderTopColor: agentCfg.color, borderTopWidth: 2 }}
    >
      {/* Header */}
      <div className="px-5 py-3 flex items-center justify-between border-b border-border">
        <div className="flex items-center gap-2.5">
          <div
            className="w-6 h-6 rounded-md flex items-center justify-center text-white text-xs font-bold"
            style={{
              background: `linear-gradient(135deg, ${agentCfg.color}, ${agentCfg.color}99)`,
            }}
          >
            {agentCfg.icon}
          </div>
          <span className="text-sm font-medium">{agentCfg.name}</span>
          {hasMultiple && (
            <span className="text-xs text-muted-foreground">
              +{(message.agents_used?.length || 0) - 1} agents
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          {message.confidence && (
            <span className="text-emerald-400">
              {Math.round(message.confidence * 100)}%
            </span>
          )}
          {message.latency_ms !== undefined && message.latency_ms > 0 && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {(message.latency_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>
      </div>

      {/* Multi-agent chips */}
      {hasMultiple && (
        <div className="px-5 py-2 flex flex-wrap gap-1.5 border-b border-border bg-background/30">
          {message.agents_used?.map((agentId) => {
            const a = getAgentConfig(agentId)
            return (
              <span
                key={agentId}
                className="inline-flex items-center gap-1 px-2 py-0.5 bg-muted rounded-full text-[11px]"
                style={{ borderLeft: `2px solid ${a.color}` }}
              >
                <span className="text-emerald-400 text-[9px]">✓</span>
                {a.name}
              </span>
            )
          })}
        </div>
      )}

      {/* Content */}
      <div className="px-5 py-4">
        <Markdown content={message.content} />
      </div>

      {/* Footer */}
      <div className="px-5 py-2 border-t border-border bg-background/30 flex items-center justify-between">
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              Copy
            </>
          )}
        </button>
        {message.workflow && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition"
          >
            {showDetails ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {message.workflow.replace(/_/g, " ")}
          </button>
        )}
      </div>
    </div>
  )
}
