"use client"

import { useState } from "react"
import { Database, FileText, Sparkles, ExternalLink, X, BookOpen, AlertCircle } from "lucide-react"
import Link from "next/link"

const INTEGRATIONS = [
  {
    id: "ga4",
    name: "Google Analytics 4",
    desc: "Traffic, conversions, and user behavior trends.",
    color: "#f59e0b",
    unlocks: [
      "Traffic source spikes and drops identification",
      "Audience conversion rate friction analysis",
      "High-bounce landing pages content audits"
    ],
    instructions: [
      "Log into your Google Analytics 4 property.",
      "Navigate to Reports > Engagement > Pages and screens.",
      "In the top-right corner, click the Share icon > Download File > Download CSV.",
      "Open the AI Brief Room in SwarmOps and upload this CSV file. The specialist agents will analyze the data immediately."
    ]
  },
  {
    id: "gsc",
    name: "Search Console",
    desc: "Keyword queries, organic impressions, and CTR metrics.",
    color: "#06b6d4",
    unlocks: [
      "Click-Through Rate (CTR) optimization suggestions",
      "Search ranking drop alerts & content decay mapping",
      "Hidden organic keyword opportunities discovery"
    ],
    instructions: [
      "Open Google Search Console and select your verified domain property.",
      "Go to the Performance report in the left sidebar.",
      "Set your desired date range (e.g. Last 3 months).",
      "Click Export in the top-right corner and choose Download CSV.",
      "Upload the exported queries CSV into the AI Brief Room to trigger an SEO specialist sweep."
    ]
  },
  {
    id: "google_ads",
    name: "Google Ads",
    desc: "Campaign spend, conversion numbers, and ROAS optimization.",
    color: "#22c55e",
    unlocks: [
      "Return on Ad Spend (ROAS) optimization strategies",
      "Wasteful CPC keywords detection and exclusion lists",
      "Ad copy performance variation tests and outlines"
    ],
    instructions: [
      "Log into your Google Ads dashboard.",
      "Go to the Campaigns tab.",
      "Adjust columns to include Spend, Conversions, CTR, and Impressions.",
      "Click Download in the toolbar and select CSV.",
      "Attach this CSV report in the AI Brief Room to let Nexus review budget efficiency."
    ]
  },
  {
    id: "hubspot",
    name: "HubSpot CRM",
    desc: "Inbound leads, sales contacts, and deal pipeline status.",
    color: "#f97316",
    unlocks: [
      "Marketing-to-sales funnel leakage diagnostics",
      "High-intent lead segment strategy suggestions",
      "Lead conversion velocity and touchpoint tracking"
    ],
    instructions: [
      "Log into your HubSpot portal.",
      "Go to Contacts > Lists or Deals.",
      "Click Actions > Export list.",
      "Select CSV as the file format and export.",
      "Upload this CSV inside the AI Brief Room to align agent strategies with your active deals."
    ]
  }
]

export default function SourcesPage() {
  const [openModal, setOpenModal] = useState<string | null>(null)
  const [showInstructions, setShowInstructions] = useState(false)

  const selectedSource = INTEGRATIONS.find((s) => s.id === openModal)

  return (
    <div className="flex-grow overflow-y-auto px-8 py-8 bg-background">
      <div className="max-w-5xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold mb-1 text-foreground">Integrations</h1>
          <p className="text-sm text-muted-foreground">
            Connect marketing tools to unlock real performance analysis. Manual setup is available now; OAuth connectors are coming soon.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {INTEGRATIONS.map((source) => (
            <div key={source.id} className="bg-card border border-border rounded-xl p-5 hover:border-primary/20 transition flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-start justify-between mb-4">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-lg font-bold"
                    style={{
                      background: `linear-gradient(135deg, ${source.color}, ${source.color}99)`,
                    }}
                  >
                    ◎
                  </div>
                  <span className="px-2 py-0.5 bg-muted text-muted-foreground text-[10px] font-medium rounded uppercase tracking-wider">
                    ● Not connected
                  </span>
                </div>
                <h3 className="font-semibold text-sm mb-1 text-foreground">{source.name}</h3>
                <p className="text-xs text-muted-foreground mb-4 leading-relaxed">{source.desc}</p>
              </div>
              <button
                onClick={() => {
                  setShowInstructions(false)
                  setOpenModal(source.id)
                }}
                className="w-full py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition"
              >
                Connect Data
              </button>
            </div>
          ))}
        </div>

        {openModal && selectedSource && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-card border border-border rounded-2xl max-w-md w-full p-6 animate-slide-up shadow-2xl relative">
              <button
                onClick={() => setOpenModal(null)}
                className="absolute top-4 right-4 text-muted-foreground hover:text-foreground transition"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="flex items-center gap-2 mb-3">
                <div
                  className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                  style={{
                    background: `linear-gradient(135deg, ${selectedSource.color}, ${selectedSource.color}99)`,
                  }}
                >
                  ◎
                </div>
                <h3 className="text-lg font-semibold text-foreground">
                  Connect {selectedSource.name}
                </h3>
              </div>

              <div className="mb-4 p-3 bg-primary/10 border border-primary/20 rounded-xl text-xs text-primary flex gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-medium">OAuth Integration coming soon.</span> Automatic API connection is in development. Follow instructions below to import reports manually today.
                </div>
              </div>

              {/* Unlocked Features */}
              <div className="mb-4">
                <h4 className="text-xs font-semibold text-foreground mb-2 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-primary" /> Unlocks Capabilities
                </h4>
                <ul className="text-xs text-muted-foreground space-y-1.5 list-disc list-inside bg-muted/30 p-3 rounded-lg border border-border/50">
                  {selectedSource.unlocks.map((item, idx) => (
                    <li key={idx} className="leading-relaxed">{item}</li>
                  ))}
                </ul>
              </div>

              {/* Setup instructions */}
              <div className="mb-5">
                <button
                  onClick={() => setShowInstructions(!showInstructions)}
                  className="w-full text-left py-2 px-3 bg-muted border border-border rounded-lg text-xs font-medium text-foreground transition hover:bg-muted/80 flex items-center justify-between"
                >
                  <span className="flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-primary" />
                    {showInstructions ? "Hide Instructions" : "View Setup Instructions"}
                  </span>
                  <span>{showInstructions ? "▲" : "▼"}</span>
                </button>

                {showInstructions && (
                  <div className="mt-2 bg-muted/20 border border-border p-3.5 rounded-lg text-xs text-muted-foreground space-y-2 max-h-48 overflow-y-auto animate-fade-in">
                    {selectedSource.instructions.map((step, idx) => (
                      <div key={idx} className="flex gap-2">
                        <span className="font-bold text-primary flex-shrink-0">{idx + 1}.</span>
                        <p className="leading-relaxed">{step}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex gap-2">
                <Link
                  href="/chat"
                  onClick={() => setOpenModal(null)}
                  className="flex-1 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1.5 shadow-md"
                >
                  <FileText className="w-3.5 h-3.5" /> Upload report instead
                </Link>
                <button
                  onClick={() => setOpenModal(null)}
                  className="px-4 py-2 bg-muted hover:bg-muted/80 text-xs text-foreground font-medium rounded-lg transition"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
