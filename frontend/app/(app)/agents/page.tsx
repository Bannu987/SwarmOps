"use client"

import { AGENTS } from "@/lib/constants/agents"

export default function AgentsPage() {
  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold mb-1">Agent Network</h1>
          <p className="text-sm text-muted-foreground">
            6 specialized agents orchestrated by Nexus CMO
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.values(AGENTS).map((agent) => (
            <div
              key={agent.id}
              className="bg-card border border-border rounded-xl p-5 hover:border-primary/30 transition cursor-pointer group"
              style={{
                background: `linear-gradient(180deg, ${agent.color}08 0%, transparent 100%)`,
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-lg font-bold transition-transform group-hover:scale-110"
                  style={{
                    background: `linear-gradient(135deg, ${agent.color}, ${agent.color}99)`,
                  }}
                >
                  {agent.icon}
                </div>
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              </div>
              <h3 className="font-semibold mb-0.5">{agent.name}</h3>
              <p className="text-xs text-muted-foreground mb-3">{agent.role}</p>
              <div className="text-[11px] text-muted-foreground">
                <span className="text-emerald-500">●</span> Idle · Ready
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
