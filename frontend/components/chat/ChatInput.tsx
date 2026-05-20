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
    <div className="px-6 py-4 border-t border-border">
      <div className="max-w-3xl mx-auto relative">
        {showSlash && (
          <SlashPopup
            commands={filtered}
            activeIndex={slashIdx}
            onSelect={handleSelectCommand}
          />
        )}

        <div className="flex items-end gap-2 bg-card border border-border rounded-2xl p-2 focus-within:border-primary transition">
          <button
            onClick={() => fileRef.current?.click()}
            disabled={uploading || loading}
            className="w-9 h-9 flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted rounded-lg transition disabled:opacity-50"
            title="Upload any file"
          >
            {uploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
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
            placeholder="Ask SwarmOps anything... (type / for commands)"
            rows={1}
            disabled={loading}
            className="flex-1 bg-transparent text-foreground placeholder:text-muted-foreground text-sm py-2 px-2 outline-none resize-none disabled:opacity-50 min-h-[36px]"
          />

          <button
            onClick={handleSend}
            disabled={!input.trim() || loading}
            className="w-9 h-9 flex items-center justify-center bg-primary hover:bg-primary/90 text-primary-foreground rounded-lg transition disabled:opacity-30 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>

        <div className="mt-2 text-[11px] text-muted-foreground text-center">
          <kbd className="px-1.5 py-0.5 bg-muted border border-border rounded text-[10px]">Enter</kbd> send ·{" "}
          <kbd className="px-1.5 py-0.5 bg-muted border border-border rounded text-[10px]">Shift+Enter</kbd> new line ·{" "}
          <kbd className="px-1.5 py-0.5 bg-muted border border-border rounded text-[10px]">/</kbd> commands
        </div>
      </div>
    </div>
  )
}
