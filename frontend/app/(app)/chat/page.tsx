"use client"

import { Suspense } from "react"
import { ChatInterface } from "@/components/chat/ChatInterface"
import { Loader2 } from "lucide-react"

export default function ChatPage() {
  return (
    <Suspense fallback={
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground">Loading Brief Room...</div>
        </div>
      </div>
    }>
      <ChatInterface />
    </Suspense>
  )
}
