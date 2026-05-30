"use client"

import { CheckSquare, ArrowRight, Sparkles } from "lucide-react"
import Link from "next/link"

export default function ApprovalPage() {
  return (
    <div className="flex-grow overflow-y-auto px-8 py-8 bg-background">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold mb-1 text-foreground">Approvals</h1>
          <p className="text-sm text-muted-foreground">
            Review, edit, approve, or reject AI-generated recommendations before execution.
          </p>
        </div>

        <div className="bg-card border border-border rounded-2xl p-8 max-w-lg mx-auto text-center mt-12 shadow-lg">
          <div className="w-12 h-12 mx-auto rounded-xl bg-primary/10 flex items-center justify-center mb-4">
            <CheckSquare className="w-5 h-5 text-primary" />
          </div>
          <h3 className="text-base font-semibold text-foreground mb-2">No pending approvals</h3>
          <p className="text-xs text-muted-foreground mb-6 leading-relaxed">
            Once you run a swarm brief (e.g. asking for a blog strategy, landing page copy, or marketing audit), specialist agents will generate recommended actions. They will appear here for your review and approval before execution.
          </p>
          <Link
            href="/chat"
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition shadow-md"
          >
            Go to AI Brief Room <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    </div>
  )
}
