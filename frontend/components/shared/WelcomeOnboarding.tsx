"use client"

import Link from "next/link"
import { Sparkles, FolderPlus, HelpCircle, Circle } from "lucide-react"

interface Props {
  onCreateProjectClick?: () => void
  onTrySampleBriefClick?: () => void
}

export function WelcomeOnboarding({ onCreateProjectClick, onTrySampleBriefClick }: Props) {
  const steps = [
    { title: "Create your first project", desc: "Set up a workspace for your brand, business, or client" },
    { title: "Add website or business context", desc: "Let the swarm know what they are analyzing" },
    { title: "Run your first swarm brief", desc: "Ask Nexus and specialists to run audits, strategies, or SEO keyword maps" },
    { title: "Review recommendations in Approvals", desc: "Verify, edit, or approve AI-generated campaign actions" },
    { title: "Connect data sources later", desc: "Optionally link Search Console, Analytics, GA4, etc. for deep reports" },
  ]

  return (
    <div className="max-w-2xl mx-auto py-12 px-6 flex flex-col items-center">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary to-swarm-cyan flex items-center justify-center text-white mb-6 animate-pulse">
        <Sparkles className="w-6 h-6" />
      </div>

      <h1 className="text-2xl font-bold mb-2 text-center text-foreground tracking-tight animate-fade-in">
        Welcome to SwarmOps
      </h1>
      <p className="text-sm text-muted-foreground mb-8 text-center max-w-lg leading-relaxed">
        Create a marketing workspace, brief the AI agent network, and turn signals into approved campaign actions.
      </p>

      {/* Checklist */}
      <div className="w-full bg-card border border-border rounded-2xl p-6 mb-8 space-y-4 shadow-xl">
        <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
          Guided Onboarding Steps
        </h3>
        {steps.map((step, idx) => (
          <div key={idx} className="flex gap-3 items-start">
            <div className="mt-0.5 flex-shrink-0">
              {idx === 0 ? (
                <div className="w-4 h-4 rounded-full border border-primary flex items-center justify-center bg-primary/10">
                  <div className="w-1.5 h-1.5 rounded-full bg-primary" />
                </div>
              ) : (
                <Circle className="w-4 h-4 text-muted-foreground/40" />
              )}
            </div>
            <div>
              <h4 className="text-sm font-medium text-foreground">{step.title}</h4>
              <p className="text-xs text-muted-foreground mt-0.5 leading-relaxed">{step.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* CTAs */}
      <div className="flex flex-col sm:flex-row gap-3 w-full justify-center">
        {onCreateProjectClick ? (
          <button
            onClick={onCreateProjectClick}
            className="px-5 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-lg text-sm transition flex items-center justify-center gap-2 shadow-lg"
          >
            <FolderPlus className="w-4 h-4" /> Create first project
          </button>
        ) : (
          <Link
            href="/projects?create=true"
            className="px-5 py-2.5 bg-primary hover:bg-primary/90 text-primary-foreground font-medium rounded-lg text-sm transition flex items-center justify-center gap-2 shadow-lg"
          >
            <FolderPlus className="w-4 h-4" /> Create first project
          </Link>
        )}

        {onTrySampleBriefClick ? (
          <button
            onClick={onTrySampleBriefClick}
            className="px-5 py-2.5 bg-card hover:bg-muted border border-border text-foreground font-medium rounded-lg text-sm transition flex items-center justify-center gap-2"
          >
            <HelpCircle className="w-4 h-4" /> Try sample brief
          </button>
        ) : (
          <Link
            href="/chat?sample=true"
            className="px-5 py-2.5 bg-card hover:bg-muted border border-border text-foreground font-medium rounded-lg text-sm transition flex items-center justify-center gap-2"
          >
            <HelpCircle className="w-4 h-4" /> Try sample brief
          </Link>
        )}
      </div>
    </div>
  )
}
