"use client"

import { Sparkles } from "lucide-react"

export function LoadingMessage() {
  return (
    <div className="bg-card border border-border rounded-2xl p-5 animate-fade-in">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-primary to-swarm-cyan flex items-center justify-center text-white">
          <Sparkles className="w-3 h-3 animate-pulse" />
        </div>
        <span className="text-sm font-medium">Nexus</span>
        <span className="text-xs text-muted-foreground">thinking...</span>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-muted rounded animate-pulse w-3/4" />
        <div className="h-3 bg-muted rounded animate-pulse w-1/2" />
        <div className="h-3 bg-muted rounded animate-pulse w-2/3" />
      </div>
    </div>
  )
}
