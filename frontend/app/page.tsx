import Link from "next/link"
import { createClient } from "@/lib/supabase/server"
import { redirect } from "next/navigation"

export default async function LandingPage() {
  const supabase = createClient()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  if (user) {
    redirect("/dashboard")
  }

  const agents = [
    { name: "Nexus", desc: "CMO orchestrator", color: "#6366f1" },
    { name: "SEO", desc: "Search optimization", color: "#22d3ee" },
    { name: "Content", desc: "Strategy & copy", color: "#a855f7" },
    { name: "Analytics", desc: "Data insights", color: "#10b981" },
    { name: "CRO", desc: "Conversion expert", color: "#22c55e" },
    { name: "AEO", desc: "AI search expert", color: "#fbbf24" },
  ]

  return (
    <div className="min-h-screen flex flex-col">
      {/* Nav */}
      <nav className="border-b border-border">
        <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-primary to-swarm-cyan flex items-center justify-center text-white text-sm font-bold">
              S
            </div>
            <span className="font-semibold">SwarmOps</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm text-muted-foreground hover:text-foreground transition"
            >
              Sign in
            </Link>
            <Link
              href="/signup"
              className="px-4 py-1.5 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-lg transition"
            >
              Get started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="max-w-3xl text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 mb-6 bg-primary/10 border border-primary/20 rounded-full text-xs font-medium text-primary">
            <span className="w-1.5 h-1.5 bg-primary rounded-full animate-pulse" />
            Multi-agent AI for marketing teams
          </div>

          <h1 className="text-4xl md:text-6xl font-bold mb-6 tracking-tight">
            Your AI marketing team.
            <br />
            <span className="bg-gradient-to-r from-primary to-swarm-cyan bg-clip-text text-transparent">
              Always on, always coordinated.
            </span>
          </h1>

          <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
            6 specialist AI agents work together under a strategic orchestrator.
            SEO, content, analytics, conversion optimization, and AI search
            optimization — all in one platform.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href="/signup"
              className="px-6 py-3 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-lg transition"
            >
              Start free
            </Link>
            <Link
              href="/login"
              className="px-6 py-3 bg-card hover:bg-muted border border-border text-foreground font-medium rounded-lg transition"
            >
              Sign in
            </Link>
          </div>

          <div className="mt-16 grid grid-cols-2 md:grid-cols-3 gap-4 max-w-2xl mx-auto">
            {agents.map((agent) => (
              <div
                key={agent.name}
                className="px-4 py-3 bg-card border border-border rounded-lg text-left"
              >
                <div
                  className="w-2 h-2 rounded-full mb-2"
                  style={{ background: agent.color }}
                />
                <div className="font-medium text-sm">{agent.name}</div>
                <div className="text-xs text-muted-foreground">{agent.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </main>

      <footer className="border-t border-border py-6 text-center text-xs text-muted-foreground">
        SwarmOps v2.0 · The Claude of marketing
      </footer>
    </div>
  )
}
