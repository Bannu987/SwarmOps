"use client"

import { useEffect, useState } from "react"
import { createClient } from "@/lib/supabase/client"
import type { User } from "@supabase/supabase-js"
import { ProjectMemoryManager } from "@/components/shared/ProjectMemoryManager"
import { User as UserIcon, Brain } from "lucide-react"

export default function SettingsPage() {
  const supabase = createClient()
  const [user, setUser] = useState<User | null>(null)
  const [activeTab, setActiveTab] = useState<"profile" | "memory">("memory")

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user))
  }, [supabase.auth])

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8 bg-transparent text-white animate-fade-in">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="mb-8 border-b border-white/5 pb-5">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl md:text-2xl font-serif font-normal tracking-tight text-white">
              Settings
            </h1>
            <span className="text-[9px] font-mono text-primary bg-primary/10 border border-primary/25 px-2 py-0.5 rounded-full uppercase tracking-wider">
              Swarm Control
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
            Manage your account preferences and strategic boardroom memories.
          </p>
        </div>

        {/* Tab Selection */}
        <div className="flex gap-2 border-b border-white/5 pb-px mb-6">
          <button
            onClick={() => setActiveTab("memory")}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition flex items-center gap-2 ${
              activeTab === "memory"
                ? "border-primary text-primary font-bold"
                : "border-transparent text-muted-foreground hover:text-white"
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            Strategy Memory
          </button>
          <button
            onClick={() => setActiveTab("profile")}
            className={`px-4 py-2.5 text-xs font-semibold border-b-2 transition flex items-center gap-2 ${
              activeTab === "profile"
                ? "border-primary text-primary font-bold"
                : "border-transparent text-muted-foreground hover:text-white"
            }`}
          >
            <UserIcon className="w-3.5 h-3.5" />
            Profile Settings
          </button>
        </div>

        {activeTab === "profile" ? (
          <div className="glass-panel border border-white/5 rounded-xl p-6 space-y-4 max-w-xl shadow-lg">
            <h2 className="font-semibold text-sm border-b border-white/5 pb-2 text-white">Profile Details</h2>
            
            <div className="space-y-1">
              <label className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">Email</label>
              <div className="text-xs text-white bg-white/5 border border-white/10 px-3 py-2.5 rounded-lg select-all">
                {user?.email}
              </div>
            </div>
            
            <div className="space-y-1">
              <label className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground">Full name</label>
              <div className="text-xs text-white bg-white/5 border border-white/10 px-3 py-2.5 rounded-lg">
                {user?.user_metadata?.full_name || "Not set"}
              </div>
            </div>
          </div>
        ) : (
          <div className="animate-fade-in">
            <ProjectMemoryManager />
          </div>
        )}
      </div>
    </div>
  )
}
