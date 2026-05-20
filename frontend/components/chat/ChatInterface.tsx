"use client"

import { useState } from "react"
import { Sparkles } from "lucide-react"

export function ChatInterface() {
  const [message, setMessage] = useState("")

  const quickActions = [
    "Run a marketing audit on my site",
    "Create a content strategy for Q1",
    "Find SEO keyword opportunities",
    "Analyze my conversion funnel",
  ]

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-3 border-b border-border">
        <h1 className="font-semibold">Command Center</h1>
        <p className="text-xs text-muted-foreground">Orchestrated by Nexus CMO</p>
      </div>

      {/* Empty state */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 max-w-2xl mx-auto w-full">
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-swarm-cyan flex items-center justify-center text-white mb-5">
          <Sparkles className="w-6 h-6" />
        </div>

        <h2 className="text-2xl font-semibold mb-2 text-center">
          How can your AI marketing team help?
        </h2>
        <p className="text-sm text-muted-foreground mb-8 text-center">
          6 specialist agents · 6 workflows · Ready to execute
        </p>

        <div className="grid grid-cols-2 gap-2 w-full mb-8">
          {quickActions.map((action) => (
            <button
              key={action}
              onClick={() => setMessage(action)}
              className="text-left px-4 py-3 bg-card hover:bg-muted border border-border rounded-lg text-sm text-muted-foreground hover:text-foreground transition"
            >
              {action}
            </button>
          ))}
        </div>

        {/* Input placeholder — full chat ships in Part 4 */}
        <div className="w-full">
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Full chat interface ships in Part 4..."
            rows={2}
            className="w-full px-4 py-3 bg-card border border-border rounded-xl text-foreground placeholder:text-muted-foreground text-sm focus:outline-none focus:border-primary resize-none"
            disabled
          />
          <p className="mt-2 text-xs text-muted-foreground text-center">
            Part 4 will add: slash commands · file upload · agent cards · streaming
          </p>
        </div>
      </div>
    </div>
  )
}
