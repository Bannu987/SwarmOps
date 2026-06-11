"use client"

import { useState } from "react"
import { Markdown } from "./Markdown"
import { getAgentConfig } from "@/lib/constants/agents"
import { Copy, Check, ChevronDown, ChevronUp, Clock, Sparkles, CheckCircle2, AlertTriangle, Scale, Activity } from "lucide-react"
import type { Message } from "@/types"

interface Props {
  message: Message
}

interface TelemetryItem {
  type: "init" | "started" | "joined" | "responded" | "challenged" | "shifted" | "unknown"
  agentId?: string
  title: string
  details?: string
}

function detectAgent(text: string): string | null {
  const t = text.toLowerCase()
  if (t.includes("seo")) return "seo"
  if (t.includes("aeo")) return "aeo"
  if (t.includes("cro")) return "cro"
  if (t.includes("analytics")) return "analytics"
  if (t.includes("content")) return "content"
  if (t.includes("nexus")) return "nexus"
  return null
}

function parseTelemetry(content: string): TelemetryItem[] {
  const blocks = content.split("\n\n").filter(Boolean)
  const items: TelemetryItem[] = []

  for (const block of blocks) {
    const trimmed = block.trim()
    if (trimmed === "Coordinating specialized agents...") {
      continue
    }
    if (trimmed.startsWith("SwarmOps is preparing the brief...")) {
      items.push({
        type: "init",
        title: "Preparing Boardroom Swarm Briefing...",
        details: "Nexus supervisor is compiling context parameters and website diagnostics."
      })
    } else if (trimmed.includes("Swarm initiated:")) {
      const match = trimmed.match(/Swarm initiated:\s*\*\*([^*]+)\*\*/i)
      const workflow = match ? match[1] : "PROCESS"
      items.push({
        type: "started",
        title: `Swarm Initiated: ${workflow}`,
        details: "Coordinating specialist machine intelligence cores."
      })
    } else if (trimmed.includes("is joining the workspace")) {
      const agentId = detectAgent(trimmed)
      items.push({
        type: "joined",
        agentId: agentId || undefined,
        title: agentId ? `${agentId.toUpperCase()} specialist joined workspace` : "Specialist joined workspace",
        details: "Synchronizing system telemetry and workspace benchmarks."
      })
    } else if (trimmed.includes("completed analysis:")) {
      const agentId = detectAgent(trimmed)
      const quoteMatch = trimmed.match(/>\s*\*([^*]+)\*/)
      const conclusion = quoteMatch ? quoteMatch[1] : ""
      items.push({
        type: "responded",
        agentId: agentId || undefined,
        title: agentId ? `${agentId.toUpperCase()} specialist completed review` : "Specialist completed review",
        details: conclusion
      })
    } else if (trimmed.includes("challenged the consensus!")) {
      const agentId = detectAgent(trimmed)
      items.push({
        type: "challenged",
        agentId: agentId || undefined,
        title: agentId ? `${agentId.toUpperCase()} specialist challenged consensus` : "Consensus challenged",
        details: "Initiating boardroom debate to resolve strategic discrepancies."
      })
    } else if (trimmed.includes("Confidence alignment shift")) {
      const agentId = detectAgent(trimmed)
      const shiftMatch = trimmed.match(/\*\*(\d+)%\*\*\s*→\s*\*\*(\d+)%\*\*\s*\(([^)]+)\)/)
      let details = ""
      if (shiftMatch) {
        details = `Confidence shifted ${shiftMatch[1]}% → ${shiftMatch[2]}% due to: ${shiftMatch[3]}`
      } else {
        details = trimmed.replace(/⚖️|Confidence alignment shift for|\*\*/g, "").trim()
      }
      items.push({
        type: "shifted",
        agentId: agentId || undefined,
        title: agentId ? `${agentId.toUpperCase()} confidence updated` : "Confidence updated",
        details: details
      })
    } else {
      items.push({
        type: "unknown",
        title: trimmed
      })
    }
  }

  return items
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

  const isTelemetry = message.content.startsWith("SwarmOps is preparing the brief...") || message.content.startsWith("Swarm initiated:")
  const telemetryItems = isTelemetry ? parseTelemetry(message.content) : []

  return (
    <div
      className="glass-panel rounded-xl overflow-hidden shadow-xl border border-white/5 transition-all duration-300 relative"
      style={{
        borderLeft: `3px solid ${agentCfg.color}`,
      }}
    >
      {/* Header */}
      <div className="px-5 py-3.5 flex items-center justify-between border-b border-white/5 bg-white/[0.02]">
        <div className="flex items-center gap-2.5">
          <div
            className="w-5 h-5 rounded flex items-center justify-center text-black text-xs font-semibold shadow-sm"
            style={{
              background: `linear-gradient(135deg, ${agentCfg.color}, ${agentCfg.color}bb)`,
            }}
          >
            <span className="text-[10px] select-none">{agentCfg.icon}</span>
          </div>
          <span className="text-xs font-semibold tracking-tight text-white">{agentCfg.name} Specialist</span>
          {hasMultiple && (
            <span className="text-[9px] font-mono text-muted-foreground bg-white/5 px-1.5 py-0.5 rounded border border-white/5">
              +{message.agents_used!.length - 1} co-agents
            </span>
          )}
        </div>
        <div className="flex items-center gap-3 text-[10px] font-mono text-muted-foreground/80">
          {message.confidence && (
            <span className="text-primary font-semibold">
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
        <div className="px-5 py-2.5 flex flex-wrap gap-2 border-b border-white/5 bg-white/[0.01]">
          {message.agents_used?.map((agentId) => {
            const a = getAgentConfig(agentId)
            return (
              <span
                key={agentId}
                className="inline-flex items-center gap-1.5 px-2.5 py-0.5 bg-white/5 border border-white/5 rounded text-[9px] font-mono text-muted-foreground transition duration-300 hover:border-white/10"
                style={{ borderLeft: `2px solid ${a.color}` }}
              >
                <span style={{ color: a.color }} className="text-[8px]">●</span>
                {a.name}
              </span>
            )
          })}
        </div>
      )}

      {/* Content */}
      <div className="px-5 py-5 text-xs leading-relaxed text-foreground">
        {isTelemetry ? (
          <div className="relative pl-6 space-y-4 py-2">
            {/* Timeline connector line */}
            <div className="absolute left-2.5 top-3 bottom-3 w-[1px] bg-white/10" />
            
            {telemetryItems.map((item, idx) => {
              const itemAgentCfg = item.agentId ? getAgentConfig(item.agentId) : null
              
              // Select timeline dot icon & color
              let iconElement = <div className="w-2 bg-white/30 h-2 rounded-full" />
              if (item.type === "init") {
                iconElement = (
                  <div className="w-5 h-5 rounded-full bg-white/5 border border-white/10 flex items-center justify-center -ml-1.5">
                    <Activity className="w-3 h-3 text-primary animate-pulse" />
                  </div>
                )
              } else if (item.type === "started") {
                iconElement = (
                  <div className="w-5 h-5 rounded-full bg-white/5 border border-white/10 flex items-center justify-center -ml-1.5">
                    <Sparkles className="w-3 h-3 text-amber-300" />
                  </div>
                )
              } else if (item.type === "joined") {
                const color = itemAgentCfg?.color || "#fff"
                iconElement = (
                  <div 
                    className="w-5 h-5 rounded-full flex items-center justify-center -ml-1.5 border" 
                    style={{ backgroundColor: `${color}15`, borderColor: `${color}30` }}
                  >
                    <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: color }} />
                  </div>
                )
              } else if (item.type === "responded") {
                const color = itemAgentCfg?.color || "#10b981"
                iconElement = (
                  <div 
                    className="w-5 h-5 rounded-full flex items-center justify-center -ml-1.5 border" 
                    style={{ backgroundColor: `${color}15`, borderColor: `${color}30` }}
                  >
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  </div>
                )
              } else if (item.type === "challenged") {
                iconElement = (
                  <div className="w-5 h-5 rounded-full bg-rose-500/10 border border-rose-500/30 flex items-center justify-center -ml-1.5">
                    <AlertTriangle className="w-3 h-3 text-rose-500" />
                  </div>
                )
              } else if (item.type === "shifted") {
                iconElement = (
                  <div className="w-5 h-5 rounded-full bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center -ml-1.5">
                    <Scale className="w-3 h-3 text-cyan-400" />
                  </div>
                )
              }

              return (
                <div key={idx} className="relative flex flex-col gap-1 shadow-sm">
                  {/* Icon dot container */}
                  <div className="absolute -left-[29px] top-0.5 flex items-center justify-center">
                    {iconElement}
                  </div>
                  
                  {/* Timeline Header */}
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-white text-xs">{item.title}</span>
                    {itemAgentCfg && (
                      <span 
                        className="text-[9px] font-mono px-1.5 py-0.2 rounded border"
                        style={{ 
                          color: itemAgentCfg.color, 
                          borderColor: `${itemAgentCfg.color}30`, 
                          backgroundColor: `${itemAgentCfg.color}08` 
                        }}
                      >
                        {itemAgentCfg.name}
                      </span>
                    )}
                  </div>
                  
                  {/* Timeline Body / Details */}
                  {item.details && (
                    <div className="text-muted-foreground text-xs leading-relaxed max-w-2xl bg-white/[0.01] border border-white/5 rounded-lg p-2.5 mt-0.5 font-sans">
                      {item.details}
                    </div>
                  )}
                </div>
              )
            })}

            {/* Pulsing Swarm Thinking State */}
            {!message.latency_ms && (
              <div className="relative flex items-center gap-2 text-muted-foreground text-[10px] font-mono tracking-wider pt-2">
                <div className="absolute -left-[24px] w-2 h-2 rounded-full bg-primary animate-ping" />
                <span className="animate-pulse">BOARDROOM CONFLICTS RESOLVING / DEBATING...</span>
              </div>
            )}
          </div>
        ) : (
          <div className="prose-swarm">
            <Markdown content={message.content} />
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-5 py-2.5 border-t border-white/5 bg-white/[0.01] flex items-center justify-between">
        <button
          onClick={handleCopy}
          className="flex items-center gap-1.5 text-[9px] font-mono uppercase tracking-wider text-muted-foreground hover:text-white transition-colors duration-300"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3 text-muted-foreground/60" />
              Copy Report
            </>
          )}
        </button>
        {message.workflow && (
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="flex items-center gap-1 text-[9px] font-mono uppercase tracking-wider text-muted-foreground hover:text-white transition-colors duration-300"
          >
            {showDetails ? <ChevronUp className="w-3 h-3 text-muted-foreground/60" /> : <ChevronDown className="w-3 h-3 text-muted-foreground/60" />}
            <span>{message.workflow.replace(/_/g, " ")}</span>
          </button>
        )}
      </div>
    </div>
  )
}
