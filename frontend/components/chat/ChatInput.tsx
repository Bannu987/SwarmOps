"use client"

import { useState, useRef, type KeyboardEvent } from "react"
import { Paperclip, Send, Loader2 } from "lucide-react"
import { SlashPopup } from "./SlashPopup"
import { filterCommands } from "@/lib/constants/commands"
import type { SlashCommand } from "@/types"

interface Props {
  onSend: (text: string) => void
  onFileUpload: (file: File) => Promise<void>
  loading: boolean
  uploading: boolean
}

export function ChatInput({ onSend, onFileUpload, loading, uploading }: Props) {
  const [input, setInput] = useState("")
  const [showSlash, setShowSlash] = useState(false)
  const [slashIdx, setSlashIdx] = useState(0)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileRef = useRef<HTMLInputElement>(null)

  const filtered = filterCommands(input)

  const handleSend = () => {
    const text = input.trim()
    if (!text || loading) return
    onSend(text)
    setInput("")
    setShowSlash(false)
    if (inputRef.current) {
      inputRef.current.style.height = "auto"
    }
  }

  const handleSelectCommand = (cmd: SlashCommand) => {
    setInput(cmd.cmd + " ")
    setShowSlash(false)
    inputRef.current?.focus()
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value
    setInput(val)

    // Auto-resize
    e.target.style.height = "auto"
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + "px"

    // Show slash popup only when input starts with / and hasn't branched into arguments
    if (val.startsWith("/") && !val.includes(" ")) {
      setShowSlash(true)
      setSlashIdx(0)
    } else {
      setShowSlash(false)
    }
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (showSlash) {
      if (e.key === "ArrowDown") {
        e.preventDefault()
        setSlashIdx((i) => Math.min(i + 1, filtered.length - 1))
        return
      }
      if (e.key === "ArrowUp") {
        e.preventDefault()
        setSlashIdx((i) => Math.max(i - 1, 0))
        return
      }
      if (e.key === "Escape") {
        setShowSlash(false)
        return
      }
      if (e.key === "Tab" && filtered.length > 0) {
        e.preventDefault()
        handleSelectCommand(filtered[slashIdx])
        return
      }
      // Enter selects command only while still in the command portion (no space yet)
      if (e.key === "Enter" && !e.shiftKey && filtered.length > 0 && !input.includes(" ")) {
        e.preventDefault()
        handleSelectCommand(filtered[slashIdx])
        return
      }
    }

    if (e.key === "Enter" && !e.shiftKey && !showSlash) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    await onFileUpload(file)
    e.target.value = ""
  }

  return (
    <div className="px-6 py-4 border-t border-border/50 bg-card/5">
      <div className="max-w-3xl mx-auto relative">
        {showSlash && (
          <SlashPopup
            commands={filtered}
            activeIndex={slashIdx}
            onSelect={handleSelectCommand}
          />
        )}

        <div className="flex items-end gap-2 bg-card/65 border border-border/50 rounded-xl p-2 focus-within:border-primary/55 transition-all duration-300 shadow-sm">
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading || loading}
            className="w-9 h-9 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/40 rounded-lg transition disabled:opacity-50"
            title="Upload any file"
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
            ) : (
              <Paperclip className="w-4 h-4" />
            )}
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="*/*"
            onChange={handleFile}
            className="hidden"
          />

          <textarea
            ref={inputRef}
            value={input}
            onChange={handleChange}
            onKeyDown={handleKeyDown}
            placeholder="Instruct SwarmOps or trigger slash command /..."
            rows={1}
            disabled={loading}
            className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground/60 text-xs py-2 px-2.5 outline-none resize-none disabled:opacity-50 min-h-[36px] font-sans leading-relaxed"
          />

          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="w-9 h-9 flex items-center justify-center bg-primary hover:bg-primary/95 text-primary-foreground rounded-lg transition-all duration-300 disabled:opacity-30 disabled:cursor-not-allowed shadow-md"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin text-primary-foreground/95" />
            ) : (
              <Send className="w-4 h-4 text-primary-foreground/95" />
            )}
          </button>
        </div>

        <div className="mt-2 text-[9px] font-mono uppercase tracking-wider text-muted-foreground/80 text-center">
          <kbd className="px-1.5 py-0.5 bg-muted/65 border border-border/50 rounded text-[9px]">Enter</kbd> send brief ·{" "}
          <kbd className="px-1.5 py-0.5 bg-muted/65 border border-border/50 rounded text-[9px]">Shift+Enter</kbd> line break ·{" "}
          <kbd className="px-1.5 py-0.5 bg-muted/65 border border-border/50 rounded text-[9px]">/</kbd> command swarm
        </div>
      </div>
    </div>
  )
}
