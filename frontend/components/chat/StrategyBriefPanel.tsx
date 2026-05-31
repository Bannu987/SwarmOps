"use client"

import { useState, useEffect, useCallback } from "react"
import { listStrategyBriefs, generateStrategyBrief, getStrategyBrief } from "@/lib/api"
import type { StrategyBrief } from "@/lib/api"
import { FileText, Download, Copy, Check, Loader2, Sparkles, X, ChevronRight, Calendar, Plus } from "lucide-react"

interface Props {
  projectId: string
  onClose: () => void
}

export function StrategyBriefPanel({ projectId, onClose }: Props) {
  const [briefs, setBriefs] = useState<StrategyBrief[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedBrief, setSelectedBrief] = useState<StrategyBrief | null>(null)
  const [generating, setGenerating] = useState(false)
  const [directive, setDirective] = useState("")
  const [copied, setCopied] = useState(false)
  const [showCreate, setShowCreate] = useState(false)
  const [template, setTemplate] = useState("general_strategy")

  const loadBriefs = useCallback(async () => {
    setLoading(true)
    try {
      const res = await listStrategyBriefs(projectId)
      const list = res.briefs || []
      setBriefs(list)
      if (list.length > 0 && !selectedBrief) {
        setSelectedBrief(list[0])
      }
    } catch (e) {
      console.error("Failed to load strategy briefs:", e)
    } finally {
      setLoading(false)
    }
  }, [projectId, selectedBrief])

  useEffect(() => {
    loadBriefs()
  }, [loadBriefs])

  const handleGenerate = async () => {
    setGenerating(true)
    try {
      const res = await generateStrategyBrief(projectId, directive, template)
      if (res && res.id) {
        setDirective("")
        setShowCreate(false)
        setSelectedBrief(res)
        // Refresh list
        const listRes = await listStrategyBriefs(projectId)
        setBriefs(listRes.briefs || [])
      }
    } catch (e) {
      console.error("Brief generation failed:", e)
    } finally {
      setGenerating(false)
    }
  }

  const handleSelectBrief = async (brief: StrategyBrief) => {
    try {
      const detailed = await getStrategyBrief(brief.id)
      setSelectedBrief(detailed)
    } catch (e) {
      console.error("Failed to load brief details:", e)
      setSelectedBrief(brief)
    }
  }

  const handleCopy = () => {
    if (!selectedBrief) return
    navigator.clipboard.writeText(selectedBrief.content.markdown)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    if (!selectedBrief) return
    const blob = new Blob([selectedBrief.content.markdown], { type: "text/markdown" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${selectedBrief.title.toLowerCase().replace(/[^a-z0-9]+/g, "_")}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-card border-l border-border shadow-2xl z-50 flex animate-slide-in">
      {/* Left Sidebar: Brief History */}
      <div className="w-64 border-r border-border flex flex-col h-full bg-muted/20">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-xs text-muted-foreground uppercase tracking-wider">
            Strategy Briefs
          </h3>
          <button
            onClick={() => setShowCreate(true)}
            className="p-1 hover:bg-muted rounded text-primary transition"
            title="Generate new brief"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            </div>
          ) : briefs.length === 0 ? (
            <div className="text-center py-8 text-[11px] text-muted-foreground">
              No briefs generated yet
            </div>
          ) : (
            briefs.map((b) => {
              const isSelected = selectedBrief?.id === b.id
              return (
                <button
                  key={b.id}
                  onClick={() => handleSelectBrief(b)}
                  className={`w-full text-left p-2.5 rounded-lg text-xs transition flex flex-col gap-1 ${
                    isSelected ? "bg-primary/10 border border-primary/20 text-foreground" : "hover:bg-muted/40 text-muted-foreground hover:text-foreground"
                  }`}
                >
                  <span className="font-medium truncate max-w-full">{b.title}</span>
                  <span className="text-[9px] text-muted-foreground/60 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {new Date(b.created_at).toLocaleDateString()}
                  </span>
                </button>
              )
            })
          )}
        </div>
      </div>

      {/* Right Content Pane */}
      <div className="flex-1 flex flex-col h-full bg-card">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-muted/10">
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-primary" />
            <h2 className="font-semibold text-sm text-foreground">Boardroom Brief Engine</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-muted rounded text-muted-foreground hover:text-foreground transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Workspace Panels */}
        <div className="flex-1 overflow-y-auto p-6 relative">
          {showCreate || briefs.length === 0 ? (
            <div className="max-w-md mx-auto py-8">
              <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mb-5">
                <Sparkles className="w-5 h-5" />
              </div>
              <h3 className="text-base font-semibold text-foreground mb-2">Compile Strategy Brief</h3>
              <p className="text-xs text-muted-foreground mb-6 leading-relaxed">
                nexus gathers GSC telemetry, signals, RICE opportunities, and persistent strategic memory to compile a comprehensive marketing campaign brief.
              </p>
              
              <div className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-muted-foreground block mb-1.5">
                    Brief Template
                  </label>
                  <select
                    value={template}
                    onChange={(e) => setTemplate(e.target.value)}
                    disabled={generating}
                    className="w-full px-3 py-2 bg-input border border-border rounded-lg text-xs text-foreground outline-none focus:border-primary transition mb-4"
                  >
                    <option value="general_strategy">General Strategy Brief</option>
                    <option value="seo_growth">SEO Growth Brief</option>
                    <option value="paid_ads">Paid Ads Funnel Brief</option>
                    <option value="lead_generation">Lead Generation Brief</option>
                    <option value="product_launch">Product Launch Brief</option>
                    <option value="content_calendar">Content Calendar Brief</option>
                    <option value="crm_lifecycle">CRM Lifecycle Brief</option>
                    <option value="competitor_attack">Competitor Attack Brief</option>
                    <option value="cro_landing_page">CRO / Landing Page Brief</option>
                  </select>

                  <label className="text-xs font-semibold text-muted-foreground block mb-2">
                    Custom directives / campaign focus (optional)
                  </label>
                  <textarea
                    value={directive}
                    onChange={(e) => setDirective(e.target.value)}
                    placeholder="Focus on conversion leaks, landing page design, or ad spend reallocation rules..."
                    disabled={generating}
                    className="w-full h-32 px-3 py-2 bg-input border border-border rounded-lg text-xs text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary disabled:opacity-50 transition resize-none leading-relaxed"
                  />
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={handleGenerate}
                    disabled={generating}
                    className="flex-1 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-semibold rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-1.5 shadow-md"
                  >
                    {generating ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Sparkles className="w-3.5 h-3.5" />
                    )}
                    {generating ? "Coordinating Boardroom..." : "Compile Growth Brief"}
                  </button>
                  {briefs.length > 0 && (
                    <button
                      onClick={() => setShowCreate(false)}
                      disabled={generating}
                      className="px-4 py-2 bg-muted text-xs font-semibold rounded-lg hover:bg-muted/80 text-foreground transition"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            </div>
          ) : selectedBrief ? (
            <div className="prose prose-sm dark:prose-invert max-w-none text-xs leading-relaxed text-foreground/90 space-y-4">
              <div className="flex items-center justify-between border-b border-border/60 pb-3 mb-5">
                <div>
                  <h1 className="text-lg font-bold tracking-tight text-foreground m-0">
                    {selectedBrief.title}
                  </h1>
                  <p className="text-[10px] text-muted-foreground mt-1 m-0">
                    Generated on {new Date(selectedBrief.created_at).toLocaleString()}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleCopy}
                    className="p-2 border border-border hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition flex items-center gap-1.5"
                    title="Copy Markdown content"
                  >
                    {copied ? (
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span className="text-[10px] font-semibold">{copied ? "Copied" : "Copy"}</span>
                  </button>
                  <button
                    onClick={handleDownload}
                    className="p-2 border border-border hover:bg-muted rounded-lg text-muted-foreground hover:text-foreground transition flex items-center gap-1.5"
                    title="Download as Markdown"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span className="text-[10px] font-semibold">Download</span>
                  </button>
                </div>
              </div>

              {/* Render raw markdown scannably with clean HSL spaces */}
              <div className="whitespace-pre-wrap font-sans text-xs bg-muted/20 border border-border/30 rounded-xl p-5 leading-relaxed overflow-x-auto">
                {selectedBrief.content.markdown}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-xs text-muted-foreground">
              Select a brief from history or compile a new one.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
