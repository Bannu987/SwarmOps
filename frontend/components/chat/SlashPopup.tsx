"use client"

import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"
import type { SlashCommand } from "@/types"

interface Props {
  commands: SlashCommand[]
  activeIndex: number
  onSelect: (cmd: SlashCommand) => void
}

export function SlashPopup({ commands, activeIndex, onSelect }: Props) {
  const activeRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: "nearest" })
  }, [activeIndex])

  if (commands.length === 0) {
    return (
      <div className="absolute bottom-full left-0 right-0 mb-2 bg-popover border border-border rounded-xl shadow-2xl p-3 text-sm text-muted-foreground text-center animate-slide-up">
        No matching commands
      </div>
    )
  }

  return (
    <div className="absolute bottom-full left-0 right-0 mb-2 bg-popover border border-border rounded-xl shadow-2xl overflow-hidden max-h-80 overflow-y-auto animate-slide-up">
      <div className="px-3 py-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider border-b border-border bg-background/50">
        Commands · {commands.length}
      </div>
      {commands.map((cmd, i) => (
        <button
          key={cmd.cmd}
          ref={i === activeIndex ? activeRef : null}
          onClick={() => onSelect(cmd)}
          className={cn(
            "w-full px-3 py-2 flex items-center gap-3 text-left transition",
            i === activeIndex ? "bg-primary/10" : "hover:bg-muted"
          )}
        >
          <span className="text-primary text-sm w-5 text-center">{cmd.icon}</span>
          <span className="font-mono text-sm text-primary min-w-[90px]">{cmd.cmd}</span>
          <span className="text-sm text-muted-foreground flex-1">{cmd.desc}</span>
        </button>
      ))}
    </div>
  )
}
