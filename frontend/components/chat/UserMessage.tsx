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
                className="flex items-center gap-2 bg-card border border-border rounded-lg px-3 py-1.5 text-xs text-muted-foreground"
              >
                <Paperclip className="w-3 h-3" />
                <span>{att.filename}</span>
                <span className="text-[10px]">
                  {(att.file_size / 1024).toFixed(1)}KB
                </span>
              </div>
            ))}
          </div>
        )}
        <div className="bg-primary text-primary-foreground rounded-2xl rounded-br-md px-4 py-2.5 text-sm whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    </div>
  )
}
