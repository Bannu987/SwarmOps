"use client"

import { useState } from "react"

const SOURCES = [
  { id: "ga4", name: "Google Analytics 4", desc: "Traffic, conversions, user behavior", color: "#f59e0b" },
  { id: "gsc", name: "Search Console", desc: "Keyword rankings, impressions, CTR", color: "#06b6d4" },
  { id: "hubspot", name: "HubSpot CRM", desc: "Contacts, leads, deal pipeline", color: "#f97316" },
  { id: "google_ads", name: "Google Ads", desc: "Campaign spend, ROAS, conversions", color: "#22c55e" },
]

export default function SourcesPage() {
  const [openModal, setOpenModal] = useState<string | null>(null)

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-5xl mx-auto">
        <h1 className="text-2xl font-semibold mb-1">Data Sources</h1>
        <p className="text-sm text-muted-foreground mb-8">
          Connect your marketing stack for real-data analysis
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {SOURCES.map((source) => (
            <div key={source.id} className="bg-card border border-border rounded-xl p-5">
              <div className="flex items-start justify-between mb-3">
                <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center text-white text-lg"
                  style={{
                    background: `linear-gradient(135deg, ${source.color}, ${source.color}99)`,
                  }}
                >
                  ◎
                </div>
                <span className="px-2 py-0.5 bg-muted text-muted-foreground text-[10px] font-medium rounded uppercase tracking-wider">
                  ○ Not connected
                </span>
              </div>
              <h3 className="font-semibold mb-1">{source.name}</h3>
              <p className="text-xs text-muted-foreground mb-4">{source.desc}</p>
              <button
                onClick={() => setOpenModal(source.id)}
                className="w-full py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-lg transition"
              >
                Connect
              </button>
            </div>
          ))}
        </div>

        {openModal && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-card border border-border rounded-2xl max-w-md w-full p-6 animate-slide-up">
              <h3 className="text-lg font-semibold mb-3">
                Connect {SOURCES.find((s) => s.id === openModal)?.name}
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                OAuth flow coming in v2.1. For now, set environment variables on Render.
              </p>
              <button
                onClick={() => setOpenModal(null)}
                className="w-full py-2 bg-muted text-sm rounded-lg hover:bg-muted/80"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
