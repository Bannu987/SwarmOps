"use client"

import { useEffect, useState } from "react"

interface PulseActivity {
  agent: string
  action: string
}

interface Props {
  activities: PulseActivity[]
  signalsCount: number
}

export function PulseBar({ activities, signalsCount }: Props) {
  const [currentIndex, setCurrentIndex] = useState(0)

  useEffect(() => {
    if (activities.length === 0) return
    const interval = setInterval(() => {
      setCurrentIndex((i) => (i + 1) % activities.length)
    }, 3500)
    return () => clearInterval(interval)
  }, [activities.length])

  return (
    <div className="px-4 py-2 border-b border-border bg-card/30 flex items-center gap-3 text-[11px] font-mono">
      <div className="flex items-center gap-1.5 flex-shrink-0">
        <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
        <span className="text-muted-foreground tracking-wide">
          SWARM ACTIVE · 6 AGENTS ONLINE
        </span>
      </div>

      <span className="text-muted-foreground/40">·</span>

      <div className="flex-1 overflow-hidden">
        {activities.length > 0 ? (
          <span className="text-muted-foreground" key={currentIndex}>
            {activities[currentIndex].agent}{" "}
            <span className="text-foreground/70">{activities[currentIndex].action}</span>
          </span>
        ) : (
          <span className="text-muted-foreground">Idle · waiting for signals</span>
        )}
      </div>

      <span className="text-muted-foreground/40">·</span>

      <span
        className="flex-shrink-0"
        style={{ color: signalsCount > 0 ? "#22D3EE" : undefined }}
      >
        {signalsCount} active signal{signalsCount !== 1 ? "s" : ""}
      </span>
    </div>
  )
}
