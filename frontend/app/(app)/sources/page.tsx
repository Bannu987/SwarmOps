"use client"

import { useState } from "react"
import { Database, FileText, Sparkles, X, BookOpen, AlertCircle, Cpu, Radio, Network } from "lucide-react"
import Link from "next/link"

const INTEGRATIONS = [
  {
    id: "ga4",
    name: "Google Analytics 4",
    desc: "Traffic, conversions, and user behavior trends.",
    color: "#f59e0b",
    status: "Telemetry Active",
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
    status: "Telemetry Active",
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
    status: "Pending Link",
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
    status: "Pending Link",
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
    <div className="flex-grow overflow-y-auto px-8 py-8 bg-transparent animate-fade-in text-white">
      <div className="max-w-5xl mx-auto">
        
        {/* Header */}
        <div className="mb-8 border-b border-white/5 pb-5">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl md:text-2xl font-serif font-normal tracking-tight text-white">
              Integrations
            </h1>
            <span className="text-[9px] font-mono text-primary bg-primary/10 border border-primary/25 px-2 py-0.5 rounded-full uppercase tracking-wider">
              Telemetry Ingest
            </span>
          </div>
          <p className="text-xs text-muted-foreground mt-1 max-w-2xl leading-relaxed">
            Connect search engines, CRM, and tracking pipelines to compile swarm memory. Follow manual import guidelines to scan raw reports.
          </p>
        </div>

        {/* Integration Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {INTEGRATIONS.map((source) => (
            <div 
              key={source.id} 
              className="glass-panel border border-white/5 rounded-xl p-5 hover:border-white/10 hover:bg-white/[0.02] transition-all duration-300 flex flex-col justify-between shadow-lg relative group"
            >
              <div>
                {/* Integration Header */}
                <div className="flex items-start justify-between mb-4 border-b border-white/5 pb-3">
                  <div className="flex items-center gap-2">
                    <div
                      className="w-6 h-6 rounded flex items-center justify-center text-black text-[10px] font-bold shadow-sm"
                      style={{
                        background: `linear-gradient(135deg, ${source.color}, ${source.color}bb)`,
                      }}
                    >
                      ◉
                    </div>
                    <h3 className="font-sans font-semibold text-xs text-white">{source.name}</h3>
                  </div>
                  
                  <span className={`px-2 py-0.5 text-[8px] font-mono uppercase tracking-wider rounded-full border ${
                    source.status.includes("Active") 
                      ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/20" 
                      : "text-amber-400 bg-amber-500/10 border-amber-500/20"
                  }`}>
                    {source.status}
                  </span>
                </div>
                
                <p className="text-xs text-muted-foreground mb-5 leading-relaxed">{source.desc}</p>
              </div>

              <button
                onClick={() => {
                  setShowInstructions(false)
                  setOpenModal(source.id)
                }}
                className="w-full py-1.5 border border-white/10 hover:border-white/25 hover:bg-white/5 text-white font-mono text-[9px] uppercase tracking-wider rounded-lg transition-all duration-300 shadow-sm"
              >
                Configure Telemetry
              </button>
            </div>
          ))}
        </div>

        {/* Configuration Modal */}
        {openModal && selectedSource && (
          <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4 backdrop-blur-sm">
            <div className="bg-[#08080f] border border-white/10 rounded-xl max-w-md w-full p-6 animate-slide-up shadow-2xl relative">
              <button
                onClick={() => setOpenModal(null)}
                className="absolute top-4 right-4 text-muted-foreground hover:text-white transition"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="flex items-center gap-2 mb-4 border-b border-white/5 pb-3">
                <div
                  className="w-6 h-6 rounded flex items-center justify-center text-black text-[10px] font-bold"
                  style={{
                    background: `linear-gradient(135deg, ${selectedSource.color}, ${selectedSource.color}bb)`,
                  }}
                >
                  ◉
                </div>
                <h3 className="text-xs font-semibold text-white uppercase tracking-wider font-mono">
                  {selectedSource.name} setup
                </h3>
              </div>

              <div className="mb-4 p-3 bg-primary/10 border border-primary/20 rounded-lg text-xs text-white flex gap-2.5 font-sans leading-relaxed">
                <AlertCircle className="w-4 h-4 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-white">Manual Export Sync.</span> SwarmOps uses secure local CSV parses for data sovereignty. Follow instructions below to sync.
                </div>
              </div>

              {/* Unlocked Capabilities */}
              <div className="mb-4 space-y-2">
                <h4 className="text-[9px] font-mono uppercase tracking-wider text-primary font-bold flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-primary" /> Unlocks swarm intelligence
                </h4>
                <ul className="text-xs text-muted-foreground space-y-1.5 list-disc list-inside bg-white/[0.01] p-3 rounded-lg border border-white/5">
                  {selectedSource.unlocks.map((item, idx) => (
                    <li key={idx} className="leading-relaxed font-sans">{item}</li>
                  ))}
                </ul>
              </div>

              {/* Setup instructions toggle */}
              <div className="mb-5">
                <button
                  onClick={() => setShowInstructions(!showInstructions)}
                  className="w-full text-left py-2 px-3 bg-white/5 border border-white/10 rounded-lg text-[9px] font-mono uppercase tracking-wider text-white transition hover:bg-white/10 flex items-center justify-between"
                >
                  <span className="flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-primary" />
                    {showInstructions ? "Hide instructions" : "Setup instructions"}
                  </span>
                  <span className="text-[8px]">{showInstructions ? "▲" : "▼"}</span>
                </button>

                {showInstructions && (
                  <div className="mt-2 bg-black/60 border border-white/5 p-3 rounded-lg font-mono text-[10px] text-muted-foreground space-y-2 max-h-40 overflow-y-auto">
                    {selectedSource.instructions.map((step, idx) => (
                      <div key={idx} className="flex gap-2">
                        <span className="font-bold text-primary flex-shrink-0">{idx + 1}.</span>
                        <p className="leading-relaxed font-sans text-xs">{step}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-2.5 border-t border-white/5 pt-4">
                <Link
                  href="/chat"
                  onClick={() => setOpenModal(null)}
                  className="flex-grow py-2 bg-primary hover:bg-primary/95 text-white font-mono text-[9px] uppercase tracking-wider rounded-lg transition-all duration-300 flex items-center justify-center gap-1.5 shadow-sm border border-primary/20"
                >
                  <FileText className="w-3.5 h-3.5" />
                  <span>Upload telemetry CSV</span>
                </Link>
                <button
                  onClick={() => setOpenModal(null)}
                  className="px-4 py-2 border border-white/10 hover:bg-white/5 text-xs text-white font-medium rounded-lg transition duration-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
