"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { cn, getInitials } from "@/lib/utils"
import type { User } from "@supabase/supabase-js"
import {
  MessageSquare,
  Users,
  CheckSquare,
  Database,
  FolderKanban,
  Plus,
  Settings,
  LogOut,
  ChevronDown,
  Bot,
} from "lucide-react"

interface SidebarProps {
  user: User
}

export function Sidebar({ user }: SidebarProps) {
  const pathname = usePathname()
  const router = useRouter()
  const supabase = createClient()
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const navItems = [
    { href: "/dashboard", icon: MessageSquare, label: "Command Center" },
    { href: "/projects", icon: FolderKanban, label: "Projects" },
    { href: "/agents", icon: Users, label: "Agents" },
    { href: "/approval", icon: CheckSquare, label: "Approval Queue", badge: 0 },
    { href: "/sources", icon: Database, label: "Data Sources" },
  ]

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push("/login")
    router.refresh()
  }

  const userName = user.user_metadata?.full_name || user.email?.split("@")[0] || "User"

  return (
    <aside className="w-60 flex-shrink-0 bg-card border-r border-border flex flex-col">
      {/* Logo */}
      <div className="px-4 py-4 flex items-center gap-2">
        <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-swarm-cyan flex items-center justify-center text-white text-sm font-bold">
          S
        </div>
        <span className="font-semibold text-sm">
          Swarm<span className="text-primary">Ops</span>
        </span>
      </div>

      {/* New chat */}
      <div className="px-3 pb-3">
        <Link
          href="/dashboard"
          className="w-full py-2 px-3 bg-input hover:bg-muted border border-border rounded-lg text-foreground text-sm font-medium transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4 text-primary" />
          New Chat
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2 py-2 space-y-0.5 overflow-y-auto">
        <div className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider px-2 py-2">
          Workspace
        </div>
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-2 py-2 rounded-md text-sm flex items-center gap-2.5 transition relative",
                isActive
                  ? "bg-primary/10 text-primary"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              )}
            >
              <item.icon className="w-4 h-4" />
              <span>{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="ml-auto bg-primary text-primary-foreground text-[10px] font-semibold px-1.5 py-0.5 rounded-full">
                  {item.badge}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* User menu */}
      <div className="px-2 py-3 border-t border-border relative">
        <button
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className="w-full px-2 py-2 hover:bg-muted rounded-md flex items-center gap-2.5 transition"
        >
          <div className="w-7 h-7 rounded-full bg-primary/20 flex items-center justify-center text-primary text-xs font-semibold">
            {getInitials(userName)}
          </div>
          <div className="flex-1 text-left overflow-hidden">
            <div className="text-sm text-foreground truncate">{userName}</div>
            <div className="text-[11px] text-muted-foreground truncate">{user.email}</div>
          </div>
          <ChevronDown className="w-4 h-4 text-muted-foreground" />
        </button>

        {userMenuOpen && (
          <div className="absolute bottom-full left-2 right-2 mb-2 bg-popover border border-border rounded-lg shadow-2xl py-1 animate-fade-in">
            <Link
              href="/settings"
              onClick={() => setUserMenuOpen(false)}
              className="w-full px-3 py-2 text-left text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition flex items-center gap-2"
            >
              <Settings className="w-4 h-4" /> Settings
            </Link>
            <div className="h-px bg-border my-1" />
            <button
              onClick={handleSignOut}
              className="w-full px-3 py-2 text-left text-sm text-destructive hover:bg-destructive/10 transition flex items-center gap-2"
            >
              <LogOut className="w-4 h-4" /> Sign out
            </button>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 border-t border-border">
        <div className="text-[10px] text-muted-foreground flex items-center gap-1.5">
          <Bot className="w-3 h-3" />
          v2.0 · 6 agents · 6 workflows
        </div>
      </div>
    </aside>
  )
}
