"use client"

import Link from "next/link"
import { Sparkles, ArrowRight } from "lucide-react"

interface Props {
  hasProject: boolean
  onTriggerScan?: () => void
  scanning?: boolean
}

export function EmptyOperationsState({ hasProject, onTriggerScan, scanning }: Props) {
  if (!hasProject) {
    return (
      <div className="h-full flex items-center justify-center px-6">
        <div className="max-w-md text-center">
          <div className="w-12 h-12 mx-auto rounded-xl bg-primary/10 flex items-center justify-center mb-4">
            <Sparkles className="w-5 h-5 text-primary" />
          </div>
          <h2 className="text-lg font-medium mb-2">No projects yet</h2>
          <p className="text-sm text-muted-foreground mb-5 leading-relaxed">
            Create a project with your website URL to let the swarm start watching your business.
            We&apos;ll detect issues, surface opportunities, and rank them by impact.
          </p>
          <Link
            href="/projects"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-lg transition"
          >
            Create a project <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex items-center justify-center px-6">
      <div className="max-w-md text-center">
        <div className="w-12 h-12 mx-auto rounded-xl bg-primary/10 flex items-center justify-center mb-4">
          <Sparkles className="w-5 h-5 text-primary" />
        </div>
        <h2 className="text-lg font-medium mb-2">No signals yet</h2>
        <p className="text-sm text-muted-foreground mb-5 leading-relaxed">
          Run your first scan. The swarm will analyze your site, detect issues, and propose ranked
          opportunities in seconds.
        </p>
        <button
          onClick={onTriggerScan}
          disabled={scanning}
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-lg transition disabled:opacity-50"
        >
          {scanning ? "Scanning..." : "Run first scan"}
          {!scanning && <ArrowRight className="w-4 h-4" />}
        </button>
      </div>
    </div>
  )
}
