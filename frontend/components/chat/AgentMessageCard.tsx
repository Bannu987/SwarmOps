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
      className="bg-card/65 border border-border/40 rounded-lg overflow-hidden shadow-sm animate-slide-up"
      style={{ borderTop: `2px solid ${agentCfg.color}` }}
    >
      {/* Header */}
      <div className="px-5 py-3.5 flex items-center justify-between border-b border-border/40 bg-card/10">
        <div className="flex items-center gap-2.5">
          <div
            className="w-6 h-6 rounded flex items-center justify-center text-black text-xs font-bold shadow-sm"
            style={{
              background: `linear-gradient(135deg, ${agentCfg.color}, ${agentCfg.color}bb)`,
            }}
          >
            <span className="text-[10px] select-none">{agentCfg.icon}</span>
          </div>
          <span className="text-xs font-medium tracking-tight text-foreground/95">{agentCfg.name} Specialist</span>
          {hasMultiple && (
            <span className="text-[10px] font-mono text-muted-foreground bg-muted/40 px-1.5 py-0.5 rounded border border-border/30">
              +{message.agents_used!.length - 1} co-agents
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground/80">
          {message.confidence && (
            <span className="text-primary font-medium">
              ALIGN: {Math.round(message.confidence * 100)}%
            </span>
          )}
          {message.latency_ms !== undefined && message.latency_ms > 0 && (
            <span className="flex items-center gap-1 font-mono">
              <Clock className="w-3 h-3 text-muted-foreground/60" />
              {(message.latency_ms / 1000).toFixed(1)}s
            </span>
          )}
        </div>
      </div>

      {/* Multi-agent chips */}
      {hasMultiple && (
        <div className="px-5 py-2.5 flex flex-wrap gap-2 border-b border-border/40 bg-card/5">
          {message.agents_used?.map((agentId) => {
            const a = getAgentConfig(agentId)
            return (
              <span
                key={agentId}
                className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-muted/40 border border-border/30 rounded text-[10px] font-mono text-muted-foreground transition duration-300 hover:border-primary/20"
                style={{ borderLeft: `2px solid ${a.color}` }}
              >
                <span className="text-primary text-[8px]">●</span>
                {a.name}
              </span>
            )
          })}
        </div>
      )}

      {/* Content */}
      <div className="px-5 py-5 text-sm leading-relaxed">
        <Markdown content={message.content} />
      </div>

      {/* Footer */}
      <div className="px-5 py-2 border-t border-border/40 bg-card/5 flex items-center justify-between">
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-muted-foreground hover:text-primary transition-colors duration-300"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-primary" />
              <span className="text-primary">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3 text-muted-foreground/60" />
              Copy
            </>
          )}
        </button>
        {message.workflow && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-muted-foreground hover:text-primary transition-colors duration-300"
          >
            {showDetails ? <ChevronUp className="w-3 h-3 text-primary/60" /> : <ChevronDown className="w-3 h-3 text-primary/60" />}
            <span>{message.workflow.replace(/_/g, " ")}</span>
          </button>
        )}
      </div>
    </div>
  )
}
