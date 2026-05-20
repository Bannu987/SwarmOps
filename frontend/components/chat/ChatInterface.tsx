"use client"

import { useState, useRef, useEffect } from "react"
import { sendChat, uploadFile } from "@/lib/api"
import { UserMessage } from "./UserMessage"
import { AgentMessageCard } from "./AgentMessageCard"
import { ChatInput } from "./ChatInput"
import { LoadingMessage } from "./LoadingMessage"
import { EmptyState } from "./EmptyState"
import type { Message, FileAttachment } from "@/types"

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [pendingAttachments, setPendingAttachments] = useState<FileAttachment[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    })
  }, [messages, loading])

  const handleSend = async (text: string) => {
    const userMsg: Message = {
      role: "user",
      content: text,
      attachments: pendingAttachments.length > 0 ? pendingAttachments : undefined,
      timestamp: Date.now(),
    }
    setMessages((prev) => [...prev, userMsg])
    setPendingAttachments([])
    setLoading(true)

    try {
      const data = await sendChat(text)
      const assistantMsg: Message = {
        role: "assistant",
        content: data.response || data.message || "No response received.",
        agents_used: data.agents_used || [],
        workflow: data.workflow,
        latency_ms: data.latency_ms,
        confidence: data.confidence,
        artifact_id: data.artifact_id,
        timestamp: Date.now(),
      }
      setMessages((prev) => [...prev, assistantMsg])
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            "Connection error. The backend may be waking up (free tier sleeps after 15 min). Try again in 30 seconds.",
          timestamp: Date.now(),
        },
      ])
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    setUploading(true)
    try {
      const result = await uploadFile(file)
      if (result.success) {
        const attachment: FileAttachment = {
          filename: result.filename,
          file_type: result.file_type,
          file_size: result.file_size,
          word_count: result.word_count,
          summary: result.summary,
        }
        setPendingAttachments((prev) => [...prev, attachment])

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `📎 **${result.filename}** uploaded (${(result.file_size / 1024).toFixed(1)}KB)\n\n${result.summary}\n\nAsk me anything about this file.`,
            timestamp: Date.now(),
          },
        ])
      } else {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `Upload failed: ${result.error || "unknown error"}`,
            timestamp: Date.now(),
          },
        ])
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "unknown error"
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Upload failed: ${msg}`,
          timestamp: Date.now(),
        },
      ])
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-6 py-3 border-b border-border flex items-center justify-between">
        <div>
          <h1 className="font-semibold">Command Center</h1>
          <p className="text-xs text-muted-foreground">Orchestrated by Nexus CMO</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          Online
        </div>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-6 py-6">
        {messages.length === 0 ? (
          <EmptyState onQuickAction={handleSend} />
        ) : (
          <div className="max-w-3xl mx-auto space-y-5">
            {messages.map((msg, i) =>
              msg.role === "user" ? (
                <UserMessage key={i} message={msg} />
              ) : (
                <AgentMessageCard key={i} message={msg} />
              )
            )}
            {loading && <LoadingMessage />}
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        onFileUpload={handleFileUpload}
        loading={loading}
        uploading={uploading}
      />
    </div>
  )
}
