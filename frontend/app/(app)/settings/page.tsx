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
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Settings</h1>
        <p className="text-sm text-muted-foreground mb-8">
          Manage your account preferences and strategic memories
        </p>

        {/* Tab Selection */}
        <div className="flex gap-2 border-b border-border pb-px mb-6">
          <button
            onClick={() => setActiveTab("memory")}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "memory"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <Brain className="w-3.5 h-3.5" />
            Strategy Brain
          </button>
          <button
            onClick={() => setActiveTab("profile")}
            className={`px-4 py-2 text-xs font-semibold border-b-2 transition flex items-center gap-1.5 ${
              activeTab === "profile"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <UserIcon className="w-3.5 h-3.5" />
            Profile Settings
          </button>
        </div>

        {activeTab === "profile" ? (
          <div className="bg-card border border-border rounded-xl p-6 space-y-4 max-w-2xl">
            <h2 className="font-semibold text-sm">Profile Details</h2>
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Email</label>
              <div className="text-sm">{user?.email}</div>
            </div>
            <div>
              <label className="text-xs font-medium text-muted-foreground mb-1.5 block">Full name</label>
              <div className="text-sm">
                {user?.user_metadata?.full_name || "Not set"}
              </div>
            </div>
          </div>
        ) : (
          <ProjectMemoryManager />
        )}
      </div>
    </div>
  )
}
