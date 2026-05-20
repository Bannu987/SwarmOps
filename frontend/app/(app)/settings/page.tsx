"use client"

import { useEffect, useState } from "react"
import { createClient } from "@/lib/supabase/client"
import type { User } from "@supabase/supabase-js"

export default function SettingsPage() {
  const supabase = createClient()
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user))
  }, [supabase.auth])

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Settings</h1>
        <p className="text-sm text-muted-foreground mb-8">
          Manage your account and preferences
        </p>

        <div className="bg-card border border-border rounded-xl p-6 space-y-4">
          <h2 className="font-semibold">Profile</h2>
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
      </div>
    </div>
  )
}
