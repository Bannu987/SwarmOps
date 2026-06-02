"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname, useRouter } from "next/navigation"
import { createClient } from "@/lib/supabase/client"
import { cn, getInitials } from "@/lib/utils"
import type { User } from "@supabase/supabase-js"
import {
  Activity,
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
  ClipboardList,
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
    { href: "/dashboard", icon: Activity, label: "Command Center" },
    { href: "/chat", icon: MessageSquare, label: "AI Brief Room" },
    { href: "/projects", icon: FolderKanban, label: "Workspaces" },
    { href: "/action-plans", icon: ClipboardList, label: "Action Plans" },
    { href: "/agents", icon: Users, label: "Agent Network" },
    { href: "/approval", icon: CheckSquare, label: "Approvals", badge: 0 },
    { href: "/sources", icon: Database, label: "Integrations" },
  ]

  const handleSignOut = async () => {
    await supabase.auth.signOut()
    router.push("/login")
    router.refresh()
  }

  const userName = user.user_metadata?.full_name || user.email?.split("@")[0] || "User"

  return (
    <aside className="w-56 flex-shrink-0 bg-void border-r border-border/40 flex flex-col relative z-20">
      {/* Brand logo */}
      <div className="px-4.5 py-5 flex items-center gap-2 border-b border-border/30 bg-plum/40">
        <div className="w-6 h-6 rounded bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold font-serif shadow-md shadow-primary/10">
          S
        </div>
        <span className="font-serif text-base tracking-tight font-semibold text-parchment">
          Swarm<span className="text-primary font-normal italic">Ops</span>
        </span>
      </div>

      {/* New chat brief CTA */}
      <div className="px-3 py-3.5">
        <Link
          href="/chat"
          className="w-full py-1.5 px-3 bg-accent/30 hover:bg-accent/60 border border-primary/20 rounded-lg text-parchment text-xs font-medium transition flex items-center justify-center gap-2 group shadow-sm"
        >
          <Plus className="w-3.5 h-3.5 text-primary group-hover:rotate-90 transition-transform duration-300" />
          <span>New AI Brief</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-2.5 py-2.5 space-y-1.5 overflow-y-auto">
        <div className="text-[9px] font-mono tracking-widest font-semibold text-primary/75 uppercase px-2.5 py-1 mb-1">
          OPERATIONAL HUB
        </div>
        {navItems.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "px-3 py-2 rounded text-xs flex items-center gap-2.5 transition-all duration-300 border relative group",
                isActive
                  ? "bg-accent/40 border-primary/35 text-parchment font-semibold shadow-inner"
                  : "border-transparent text-muted-foreground/80 hover:text-foreground hover:bg-card/45 hover:border-border/30"
              )}
            >
              {isActive && (
                <span className="absolute left-0 top-1/4 bottom-1/4 w-0.5 bg-primary rounded-r" />
              )}
              <item.icon className={cn("w-3.5 h-3.5 transition-colors duration-300", isActive ? "text-primary" : "text-muted-foreground/50 group-hover:text-primary/90")} />
              <span className="tracking-tight">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="ml-auto bg-primary text-primary-foreground text-[8px] font-mono font-bold px-1.5 py-0.5 rounded-full">
                  {item.badge}
                </span>
              )}
            </Link>
          )
        })}
      </nav>

      {/* User settings menu */}
      <div className="px-2.5 py-3 border-t border-border/30 relative bg-plum/30">
        <button
          onClick={() => setUserMenuOpen(!userMenuOpen)}
          className="w-full px-2 py-1.5 hover:bg-card/45 rounded flex items-center gap-2.5 transition text-left"
        >
          <div className="w-6.5 h-6.5 rounded-full bg-accent/80 border border-primary/20 flex items-center justify-center text-primary text-xs font-semibold shadow-inner">
            {getInitials(userName)}
          </div>
          <div className="flex-1 text-left overflow-hidden">
            <div className="text-xs text-parchment font-medium truncate leading-none mb-1">{userName}</div>
            <div className="text-[9px] font-mono text-muted-foreground/50 truncate leading-none">{user.email}</div>
          </div>
          <ChevronDown className="w-3 h-3 text-muted-foreground/60 transition-transform duration-300" style={{ transform: userMenuOpen ? "rotate(180deg)" : "rotate(0)" }} />
        </button>

        {userMenuOpen && (
          <div className="absolute bottom-full left-2 right-2 mb-2 bg-[#0d090d] border border-border/80 rounded shadow-2xl py-1 animate-slide-up relative z-30">
            <Link
              href="/settings"
              onClick={() => setUserMenuOpen(false)}
              className="w-full px-3 py-1.5 text-left text-xs text-muted-foreground hover:bg-card hover:text-foreground transition flex items-center gap-2"
            >
              <Settings className="w-3.5 h-3.5 text-primary/70" /> Settings
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

      {/* Footer system details */}
      <div className="px-4 py-3.5 border-t border-border/30 bg-void">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-[#a3b899] animate-pulse" />
          <span className="text-[9px] font-mono tracking-widest text-[#a3b899] uppercase font-semibold">CORE_ONLINE</span>
        </div>
        <div className="text-[8px] font-mono text-muted-foreground/45 mt-1 uppercase tracking-wider">
          Node: swarm_os_c19
        </div>
      </div>
    </aside>
  )
}

