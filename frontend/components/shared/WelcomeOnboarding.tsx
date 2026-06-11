"use client"

import Link from "next/link"
import { Sparkles, FolderPlus, HelpCircle, Circle, CircleDot } from "lucide-react"

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
    <div className="max-w-2xl mx-auto py-12 px-6 flex flex-col items-center select-none animate-fade-in">
      <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center text-primary-foreground mb-6 shadow-lg glow-blue animate-pulse-slow">
        <Sparkles className="w-5 h-5" />
      </div>

      <h1 className="text-xl md:text-2xl font-serif font-normal tracking-tight text-foreground mb-2 text-center">
        Welcome to SwarmOps
      </h1>
      <p className="text-xs text-muted-foreground mb-8 text-center max-w-md leading-relaxed">
        Create a marketing workspace, brief the AI agent network, and turn signals into approved campaign actions.
      </p>

      {/* Guided Onboarding steps */}
      <div className="w-full bg-[#08080f]/60 backdrop-blur-sm border border-border/80 rounded-xl p-5.5 mb-8 space-y-4.5 shadow-xl">
        <h3 className="text-[8px] font-mono text-primary/80 uppercase tracking-widest mb-3">
          Guided Onboarding Steps
        </h3>
        
        {steps.map((step, idx) => (
          <div key={idx} className="flex gap-3.5 items-start">
            <div className="mt-0.5 flex-shrink-0">
              {idx === 0 ? (
                <CircleDot className="w-4 h-4 text-primary animate-pulse" />
              ) : (
                <Circle className="w-4 h-4 text-muted-foreground/35" />
              )}
            </div>
            <div>
              <h4 className="text-xs font-semibold text-foreground">{step.title}</h4>
              <p className="text-[11px] text-muted-foreground/80 mt-0.5 leading-relaxed">{step.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Action CTA Buttons */}
      <div className="flex flex-col sm:flex-row gap-3 w-full justify-center">
        {onCreateProjectClick ? (
          <button
            onClick={onCreateProjectClick}
            className="px-5 py-2.5 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition duration-300 flex items-center justify-center gap-2 shadow-md border border-primary/20 hover:scale-[1.01] active:scale-100"
          >
            <FolderPlus className="w-4 h-4" /> 
            <span>Create first project</span>
          </button>
        ) : (
          <Link
            href="/projects?create=true"
            className="px-5 py-2.5 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition duration-300 flex items-center justify-center gap-2 shadow-md border border-primary/20 hover:scale-[1.01] active:scale-100"
          >
            <FolderPlus className="w-4 h-4" /> 
            <span>Create first project</span>
          </Link>
        )}

        {onTrySampleBriefClick ? (
          <button
            onClick={onTrySampleBriefClick}
            className="px-5 py-2.5 bg-card hover:bg-muted/30 border border-border/80 text-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition duration-300 flex items-center justify-center gap-2 shadow-sm"
          >
            <HelpCircle className="w-4 h-4" /> 
            <span>Try sample brief</span>
          </button>
        ) : (
          <Link
            href="/chat?sample=true"
            className="px-5 py-2.5 bg-card hover:bg-muted/30 border border-border/80 text-foreground font-mono text-[10px] uppercase tracking-wider rounded-lg transition duration-300 flex items-center justify-center gap-2 shadow-sm"
          >
            <HelpCircle className="w-4 h-4" /> 
            <span>Try sample brief</span>
          </Link>
        )}
      </div>
    </div>
  )
}
