"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { cn, getInitials } from "@/lib/utils"
import type { User } from "@supabase/supabase-js"
import {
  Compass,
  Radio,
  Users,
  ClipboardList,
  Bot,
  Activity,
  FolderKanban,
  Database,
  Plus,
  Settings,
  LogOut,
  ChevronDown,
  Terminal
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
    { href: "/dashboard", icon: Compass, label: "Mission Control" },
    { href: "/signal-intelligence", icon: Radio, label: "Signal Intelligence" },
    { href: "/chat", icon: Users, label: "Boardroom" },
    { href: "/action-plans", icon: ClipboardList, label: "Operations Floor" },
    { href: "/agents", icon: Bot, label: "AI Agents" },
    { href: "/audit-timeline", icon: Activity, label: "Audit Timeline" },
    { href: "/projects", icon: FolderKanban, label: "Workspaces" },
    { href: "/sources", icon: Database, label: "Integrations" },
  ]

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push("/login")
    router.refresh()
  }

  const userName = user.user_metadata?.full_name || user.email?.split("@")[0] || "User"

  return (
    <aside className="w-56 flex-shrink-0 bg-[#040409] border-r border-border/80 flex flex-col relative z-20 select-none">
      {/* Brand logo */}
      <div className="px-5 py-4.5 flex items-center gap-2.5 border-b border-border/60">
        <div className="w-6 h-6 rounded bg-gradient-to-br from-primary to-accent flex items-center justify-center text-primary-foreground text-xs font-black shadow-md glow-blue">
          S
        </div>
        <span className="text-xs font-black tracking-widest uppercase text-foreground">
          Swarm<span className="text-primary font-light">Ops</span>
        </span>
      </div>

      {/* New AI Brief CTA */}
      <div className="px-3.5 py-3.5">
        <Link
          href="/chat"
          className="w-full py-2 px-3 bg-primary/10 hover:bg-primary/20 border border-primary/30 hover:border-primary/50 rounded-lg text-primary text-[10px] font-mono uppercase tracking-wider transition-all duration-300 flex items-center justify-center gap-2 group shadow-md"
        >
          <Plus className="w-3.5 h-3.5 text-primary group-hover:rotate-90 transition-transform duration-300" />
          <span>Brief Swarm</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-grow px-3 py-2 space-y-1 overflow-y-auto">
        <div className="text-[8px] font-mono tracking-widest font-bold text-muted-foreground/40 uppercase px-2 mb-2 select-none">
          OPERATIONAL CORES
        </div>
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-3 py-2 rounded-lg text-xs flex items-center gap-2.5 transition-all duration-200 border relative group",
                isActive
                  ? "bg-primary/10 border-primary/20 text-foreground font-semibold shadow-inner"
                  : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/30"
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/4 bottom-1/4 w-0.75 bg-primary rounded-r shadow-[0_0_10px_#3b82f6]" />
              )}
              <item.icon className={cn("w-4 h-4 transition-colors duration-200", isActive ? "text-primary" : "text-muted-foreground/50 group-hover:text-primary")} />
              <span className="tracking-tight">{item.label}</span>
            </Link>
          )
        })}
      </nav>

      {/* User settings menu */}
      <div className="px-3 py-3 border-t border-border/60 relative bg-background/25">
        <button
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className="w-full px-2 py-1.5 hover:bg-muted/40 rounded-lg flex items-center gap-2.5 transition text-left"
        >
          <div className="w-7 h-7 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary text-xs font-bold shadow-inner">
            {getInitials(userName)}
          </div>
          <div className="flex-grow min-w-0">
            <div className="text-xs text-foreground font-semibold truncate leading-none mb-1">{userName}</div>
            <div className="text-[9px] font-mono text-muted-foreground/60 truncate leading-none">{user.email}</div>
          </div>
          <ChevronDown className={cn("w-3.5 h-3.5 text-muted-foreground/50 transition-transform duration-300 flex-shrink-0", userMenuOpen && "rotate-180")} />
        </button>

        {userMenuOpen && (
          <div className="absolute bottom-full left-3 right-3 mb-2 bg-[#08080f] border border-border rounded-lg shadow-2xl py-1 animate-slide-up relative z-30">
            <Link
              href="/settings"
              onClick={() => setUserMenuOpen(false)}
              className="w-full px-3 py-1.5 text-left text-xs text-muted-foreground hover:bg-muted/40 hover:text-foreground transition flex items-center gap-2"
            >
              <Settings className="w-3.5 h-3.5 text-primary" /> Settings
            </Link>
            <div className="h-px bg-border/40 my-1" />
            <button
              onClick={handleSignOut}
              className="w-full px-3 py-1.5 text-left text-xs text-destructive hover:bg-destructive/10 transition flex items-center gap-2"
            >
              <LogOut className="w-3.5 h-3.5" /> Sign out
            </button>
          </div>
        )}
      </div>

      {/* System detail footer */}
      <div className="px-5 py-3.5 border-t border-border/60 bg-background/50 flex items-center justify-between text-[9px] font-mono text-muted-foreground/50">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          <span className="text-accent uppercase font-bold">CORE_LIVE</span>
        </div>
        <div className="flex items-center gap-1">
          <Terminal className="w-3 h-3 text-muted-foreground/40" />
          <span>v2.0</span>
        </div>
      </div>
    </aside>
  )
}
