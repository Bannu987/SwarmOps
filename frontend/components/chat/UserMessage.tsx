"use client"

import { Paperclip } from "lucide-react"
import type { Message } from "@/types"

export function UserMessage({ message }: { message: Message }) {
  return (
    <div className="flex justify-end animate-fade-in">
      <div className="max-w-[80%] space-y-2">
        {message.attachments && message.attachments.length > 0 && (
          <div className="flex flex-wrap gap-2 justify-end">
            {message.attachments.map((att, i) => (
              <div
                key={i}
                className="flex items-center gap-1.5 bg-card/65 border border-border/50 rounded px-2.5 py-1 text-[10px] font-mono text-muted-foreground"
              >
                <Paperclip className="w-3 h-3 text-primary/70" />
                <span>{att.filename}</span>
                <span className="text-[9px] text-muted-foreground/60">
                  ({(att.file_size / 1024).toFixed(1)}KB)
                </span>
              </div>
            ))}
          </div>
        )}
        <div className="bg-primary text-primary-foreground rounded-xl rounded-tr-none px-4 py-3 text-[12px] leading-relaxed whitespace-pre-wrap shadow-sm">
          {message.content}
        </div>
      </div>
    </div>
  )
}
