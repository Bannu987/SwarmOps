"use client"

import React, { useState, useEffect } from "react"
import { usePathname, useRouter } from "next/navigation"
import Link from "next/link"
import type { User } from "@supabase/supabase-js"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { Sidebar } from "@/components/sidebar/Sidebar"
import { 
  Bot, 
  Terminal, 
  Cpu, 
  Radio, 
  ChevronRight, 
  Sparkles, 
  Send, 
  X, 
  CheckSquare, 
  Compass, 
  Workflow, 
  CheckCircle2, 
  Settings,
  HelpCircle
} from "lucide-react"
import { cn } from "@/lib/utils"
import { streamChat } from "@/lib/api"

interface AppShellProps {
  user: User
  children: React.ReactNode
}

export function AppShell({ user, children }: AppShellProps) {
  const pathname = usePathname()
  const router = useRouter()
  const { projects, activeProject, selectProject, loading: projectsLoading } = useActiveProject()
  
  // Assistant Dock states
  const [dockOpen, setDockOpen] = useState(false)
  const [prompt, setPrompt] = useState("")
  const [messages, setMessages] = useState<Array<{ role: "user" | "assistant"; content: string }>>([])
  const [streaming, setStreaming] = useState(false)
  const [activeTab, setActiveTab] = useState<"chat" | "logs">("chat")

  // Mock Active Agent States for the Specialist Rail
  const [agentsState, setAgentsState] = useState([
    { id: "nexus", name: "Nexus", role: "CMO Orchestrator", status: "idle", color: "#6366f1", icon: "🧠" },
    { id: "seo", name: "SEO", role: "Search Audits", status: "idle", color: "#06b6d4", icon: "🔍" },
    { id: "aeo", name: "AEO", role: "AI Optimization", status: "idle", color: "#fbbf24", icon: "🤖" },
    { id: "content", name: "Content", role: "Copy & Briefs", status: "idle", color: "#a855f7", icon: "✍️" },
    { id: "analytics", name: "Analytics", role: "Data Metrics", status: "idle", color: "#10b981", icon: "📊" },
    { id: "cro", name: "CRO", role: "Conversion Optimization", status: "idle", color: "#22c55e", icon: "🎯" }
  ])

  // Random agent status simulator to show a "live" command center
  useEffect(() => {
    const interval = setInterval(() => {
      setAgentsState(prev => 
        prev.map(agent => {
          // 80% chance to remain in current state, 20% to shift
          if (Math.random() > 0.2) return agent
          const statuses = ["idle", "idle", "idle", "active", "thinking"]
          const nextStatus = statuses[Math.floor(Math.random() * statuses.length)]
          return { ...agent, status: nextStatus }
        })
      )
    }, 8000)
    return () => clearInterval(interval)
  }, [])

  const handleSendPrompt = async () => {
    const query = prompt.trim()
    if (!query || streaming) return
    
    setPrompt("")
    const newMessages = [...messages, { role: "user" as const, content: query }]
    setMessages(newMessages)
    setStreaming(true)
    
    // Add temporary assistant placeholder
    const assistantIndex = newMessages.length
    setMessages(prev => [...prev, { role: "assistant", content: "Synthesizing consensus..." }])

    // Update Nexus agent status to "thinking"
    setAgentsState(prev => prev.map(a => a.id === "nexus" ? { ...a, status: "thinking" } : a))

    try {
      let currentResponse = ""
      await streamChat(
        query,
        "default",
        (event) => {
          if (event.type === "agent.started") {
            const agentId = event.agent_id
            setAgentsState(prev => prev.map(a => a.id === agentId ? { ...a, status: "thinking" } : a))
          } else if (event.type === "agent.responded") {
            const agentId = event.agent_id
            setAgentsState(prev => prev.map(a => a.id === agentId ? { ...a, status: "idle" } : a))
          } else if (event.type === "final.answer") {
            currentResponse = event.answer || event.decision || event.final_answer || event.content || ""
            setMessages(prev => {
              const copy = [...prev]
              if (copy[assistantIndex]) {
                copy[assistantIndex].content = currentResponse
              }
              return copy
            })
          }
        },
        activeProject?.id
      )
    } catch (err) {
      console.error("Dock Chat error:", err)
      setMessages(prev => {
        const copy = [...prev]
        if (copy[assistantIndex]) {
          copy[assistantIndex].content = "Workflow streaming failed. Check network or verify backend is online."
        }
        return copy
      })
    } finally {
      setStreaming(false)
      // Restore agents to idle/active states
      setAgentsState(prev => prev.map(a => ({ ...a, status: "idle" })))
    }
  }

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background select-none font-sans">
      
      {/* 1. Sidebar Area */}
      <Sidebar user={user} />

      {/* Main Content Area */}
      <div className="flex-grow flex flex-col h-full overflow-hidden relative">
        
        {/* 2. Topbar Header */}
        <header className="h-14 border-b border-border/80 bg-background/40 backdrop-blur-md px-6 flex items-center justify-between z-10">
          <div className="flex items-center gap-4.5">
            {/* Workspace Selector Dropdown */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-muted-foreground uppercase tracking-widest">Workspace:</span>
              {projectsLoading ? (
                <div className="h-6 w-28 bg-muted/30 rounded animate-pulse" />
              ) : projects.length > 0 ? (
                <select
                  value={activeProject?.id || ""}
                  onChange={(e) => selectProject(e.target.value)}
                  className="bg-card/40 hover:bg-card/75 border border-border/70 rounded px-2.5 py-1 text-xs text-foreground font-semibold outline-none cursor-pointer focus:border-primary/50 transition"
                >
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
              ) : (
                <span className="text-xs text-muted-foreground italic">No Workspace</span>
              )}
            </div>
            {activeProject?.website_url && (
              <>
                <span className="text-muted-foreground/30 text-xs">|</span>
                <span className="text-[10px] font-mono text-muted-foreground bg-muted/40 px-2 py-0.5 rounded border border-border/40">
                  {activeProject.website_url.replace(/https?:\/\/(www\.)?/, "")}
                </span>
              </>
            )}
          </div>

          {/* Quick System Telemetry */}
          <div className="hidden md:flex items-center gap-5 text-[10px] font-mono text-muted-foreground/80">
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-primary/80" />
              <span>CORES: 6/6 ONLINE</span>
            </div>
            <div className="flex items-center gap-1.5">
              <Radio className="w-3.5 h-3.5 text-accent/80" />
              <span>LATENCY: 42ms</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
              <span className="text-emerald-400">SYNCED</span>
            </div>
          </div>
        </header>

        {/* Content Shell with specialist activity rail */}
        <div className="flex-1 flex overflow-hidden relative">
          
          {/* 3. Page Body */}
          <main className="flex-grow overflow-hidden relative flex flex-col">
            {children}
          </main>

          {/* 4. Specialist Activity Rail (Right Side) */}
          <aside className="w-16 border-l border-border/80 bg-background/20 backdrop-blur-sm flex flex-col items-center py-5 gap-6 select-none z-10 flex-shrink-0">
            <div className="text-[9px] font-mono text-muted-foreground/50 tracking-wider rotate-90 my-2 select-none uppercase pointer-events-none">
              SWARM_CORES
            </div>
            
            <div className="flex flex-col gap-4.5 flex-grow justify-start">
              {agentsState.map(agent => (
                <div 
                  key={agent.id} 
                  className="group relative flex flex-col items-center cursor-help"
                >
                  <div 
                    className={cn(
                      "w-9 h-9 rounded-lg flex items-center justify-center border transition-all duration-300 relative shadow-md",
                      agent.status === "thinking" 
                        ? "border-primary glow-blue scale-105" 
                        : agent.status === "active"
                          ? "border-accent glow-cyan"
                          : "border-border/60 hover:border-primary/40 bg-card/45"
                    )}
                    style={{
                      borderColor: agent.status !== "idle" ? agent.color : undefined
                    }}
                  >
                    <span className="text-sm">{agent.icon}</span>
                    
                    {/* Glowing status indicator */}
                    <span 
                      className={cn(
                        "absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full border border-background",
                        agent.status === "thinking"
                          ? "bg-primary animate-pulse"
                          : agent.status === "active"
                            ? "bg-accent animate-ping"
                            : "bg-muted-foreground/40"
                      )}
                      style={{
                        backgroundColor: agent.status !== "idle" ? agent.color : undefined
                      }}
                    />
                  </div>

                  {/* Tooltip Hover Overlay */}
                  <div className="absolute right-full mr-3 top-1/2 -translate-y-1/2 w-48 bg-card border border-border/90 rounded-lg p-3 opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-300 shadow-2xl z-40 text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-foreground">{agent.name}</span>
                      <span 
                        className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded border"
                        style={{
                          color: agent.color,
                          borderColor: `${agent.color}40`,
                          backgroundColor: `${agent.color}08`
                        }}
                      >
                        {agent.status}
                      </span>
                    </div>
                    <div className="text-[10px] text-muted-foreground mb-1.5">{agent.role}</div>
                    <div className="text-[9px] font-mono text-muted-foreground/50 border-t border-border/30 pt-1">
                      INTELLIGENCE CODE: AP_x0{agent.id.toUpperCase()}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="text-muted-foreground/40 hover:text-foreground transition cursor-pointer" title="Swarm Engine Status">
              <HelpCircle className="w-4 h-4" />
            </div>
          </aside>
        </div>

        {/* 5. Persistent Assistant Floating Dock */}
        <div 
          className={cn(
            "fixed bottom-5 right-20 transition-all duration-300 z-50",
            dockOpen ? "w-[420px]" : "w-11"
          )}
        >
          {dockOpen ? (
            /* Opened Command Panel */
            <div className="glass-panel border border-primary/25 rounded-xl shadow-2xl flex flex-col h-[520px] overflow-hidden animate-slide-up">
              
              {/* Header */}
              <div className="p-3 border-b border-border/80 flex items-center justify-between bg-primary/5">
                <div className="flex items-center gap-2">
                  <Bot className="w-4.5 h-4.5 text-primary" />
                  <span className="text-xs font-semibold tracking-wide text-foreground uppercase">Swarm Boardroom Dock</span>
                  <span className="text-[8px] font-mono px-1.5 py-0.2 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded">LIVE</span>
                </div>
                
                <div className="flex items-center gap-1">
                  <button 
                    onClick={() => setDockOpen(false)}
                    className="p-1 text-muted-foreground hover:text-foreground hover:bg-muted/40 rounded transition"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex border-b border-border/40 text-[10px] font-mono uppercase tracking-wider bg-[#08080f]/40">
                <button
                  onClick={() => setActiveTab("chat")}
                  className={cn(
                    "flex-1 py-2 text-center border-r border-border/40 transition",
                    activeTab === "chat" ? "bg-card text-primary font-bold" : "text-muted-foreground hover:bg-muted/20"
                  )}
                >
                  Prompt Swarm
                </button>
                <button
                  onClick={() => setActiveTab("logs")}
                  className={cn(
                    "flex-1 py-2 text-center transition",
                    activeTab === "logs" ? "bg-card text-accent font-bold" : "text-muted-foreground hover:bg-muted/20"
                  )}
                >
                  Telemetry Logs
                </button>
              </div>

              {/* Message scroll list */}
              {activeTab === "chat" ? (
                <div className="flex-grow overflow-y-auto p-4 space-y-3.5 bg-background/25">
                  {messages.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-center p-6 text-muted-foreground/60">
                      <Terminal className="w-8 h-8 text-primary/50 mb-3 animate-pulse" />
                      <p className="text-xs font-medium text-foreground/80 mb-1">Boardroom Quick Terminal</p>
                      <p className="text-[10px] leading-relaxed max-w-xs">
                        Query the 6 specialist agents instantly. Ask for marketing advice, copy suggestions, or signal diagnosis.
                      </p>
                    </div>
                  ) : (
                    messages.map((m, idx) => (
                      <div 
                        key={idx} 
                        className={cn(
                          "flex flex-col max-w-[85%] rounded-lg p-3 text-xs leading-relaxed border shadow-sm",
                          m.role === "user"
                            ? "bg-primary/10 border-primary/20 text-foreground self-end rounded-br-none"
                            : "bg-card border-border/80 text-foreground/90 self-start rounded-bl-none"
                        )}
                      >
                        <div className="text-[8px] font-mono uppercase tracking-wider text-muted-foreground/60 mb-1 font-semibold">
                          {m.role === "user" ? "USER_PROMPT" : "SWARM_SYNTHESIS"}
                        </div>
                        <div className="font-sans whitespace-pre-line">{m.content}</div>
                      </div>
                    ))
                  )}
                </div>
              ) : (
                /* Telemetry Logs Panel */
                <div className="flex-grow overflow-y-auto p-4 bg-[#020204]/90 font-mono text-[9px] text-[#a3b899] space-y-1">
                  <div>[SYS_INIT] Loading swarm state telemetry logs...</div>
                  <div>[SYS_OK] 6 agents synced on client port 3000</div>
                  <div>[SUPABASE] Authenticated profile user ID: {user.id.substring(0, 8)}...</div>
                  {activeProject && (
                    <>
                      <div>[PROJECT_OK] Active Project: {activeProject.name}</div>
                      <div>[PROJECT_URL] Web telemetry target: {activeProject.website_url}</div>
                    </>
                  )}
                  <div>[SSE_BUS_OK] Event stream listener initialized successfully.</div>
                  <div className="text-muted-foreground/50 border-t border-border/30 pt-1 mt-2">[LOG_TAIL] Listening for websocket signals...</div>
                </div>
              )}

              {/* Bottom Input Area */}
              {activeTab === "chat" && (
                <div className="p-3 border-t border-border/80 bg-[#08080f]/60 flex items-center gap-2">
                  <input
                    type="text"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSendPrompt()}
                    placeholder="Command the swarm..."
                    disabled={streaming}
                    className="flex-1 bg-background border border-border/80 rounded px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground/60 outline-none focus:border-primary/50 disabled:opacity-50 transition"
                  />
                  <button
                    onClick={handleSendPrompt}
                    disabled={streaming || !prompt.trim()}
                    className="p-2 bg-primary hover:bg-primary/90 text-primary-foreground rounded transition disabled:opacity-50 shadow-md flex-shrink-0"
                  >
                    <Send className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

            </div>
          ) : (
            /* Minimized Icon Button */
            <button
              onClick={() => setDockOpen(true)}
              className="w-11 h-11 bg-primary hover:bg-primary/95 text-primary-foreground border border-primary/20 rounded-full flex items-center justify-center shadow-lg transition duration-300 hover:scale-105 relative glow-blue group"
              title="Open Swarm Assistant Dock"
            >
              <Bot className="w-5 h-5 text-primary-foreground group-hover:rotate-12 transition-transform duration-300" />
              {/* Pulse status dot */}
              <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-accent border-2 border-background rounded-full animate-pulse-slow" />
            </button>
          )}
        </div>

      </div>
    </div>
  )
}
