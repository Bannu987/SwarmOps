"use client"

import { useState, useEffect, useCallback } from "react"
import { listProjectMemories, createProjectMemory, deleteProjectMemory } from "@/lib/api"
import type { ProjectMemory } from "@/lib/api"
import { useActiveProject } from "@/lib/hooks/useActiveProject"
import { 
  Brain, 
  Trash2, 
  Plus, 
  Sparkles, 
  Check, 
  Loader2, 
  Tag, 
  Calendar, 
  Bookmark, 
  User, 
  Search,
  BookOpen,
  Target,
  ArrowUpRight,
  ShieldAlert
} from "lucide-react"

export function ProjectMemoryManager() {
  const { activeProject } = useActiveProject()
  const [memories, setMemories] = useState<ProjectMemory[]>([])
  const [loading, setLoading] = useState(true)
  const [filterType, setFilterType] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState("")

  // Form states for creating a new memory manually
  const [showAddForm, setShowAddForm] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [newType, setNewType] = useState("brand_voice")
  const [newTitle, setNewTitle] = useState("")
  const [newSummary, setNewSummary] = useState("")
  const [newTagsStr, setNewTagsStr] = useState("")
  const [successMsg, setSuccessMsg] = useState(false)

  const loadMemories = useCallback(async () => {
    if (!activeProject?.id) return
    setLoading(true)
    try {
      const res = await listProjectMemories(activeProject.id)
      setMemories(res.memories || [])
    } catch (e) {
      console.error("Failed to load project memories:", e)
    } finally {
      setLoading(false)
    }
  }, [activeProject?.id])

  useEffect(() => {
    loadMemories()
  }, [loadMemories])

  const handleDelete = async (id: string) => {
    try {
      const res = await deleteProjectMemory(id)
      if (res.success) {
        setMemories((prev) => prev.filter((m) => m.id !== id))
      }
    } catch (e) {
      console.error("Failed to delete project memory:", e)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!activeProject?.id || !newTitle || !newSummary) return

    setSubmitting(true)
    try {
      const tags = newTagsStr
        .split(",")
        .map((t) => t.trim())
        .filter((t) => t.length > 0)

      const res = await createProjectMemory(activeProject.id, {
        memory_type: newType,
        title: newTitle,
        summary: newSummary,
        source: "user",
        tags
      })

      if (res && res.id) {
        setNewTitle("")
        setNewSummary("")
        setNewTagsStr("")
        setShowAddForm(false)
        setSuccessMsg(true)
        setTimeout(() => setSuccessMsg(false), 3000)
        
        // Refresh memories
        await loadMemories()
      }
    } catch (err) {
      console.error("Failed to create memory:", err)
    } finally {
      setSubmitting(false)
    }
  }

  if (!activeProject) {
    return (
      <div className="bg-card border border-border rounded-xl p-6 text-center py-12">
        <Brain className="w-8 h-8 text-muted-foreground/60 mx-auto mb-3" />
        <h3 className="font-semibold text-sm mb-1 text-foreground">No Active Workspace</h3>
        <p className="text-xs text-muted-foreground max-w-sm mx-auto">
          Please select or create a project workspace from the top navigation to view and manage its strategic memory.
        </p>
      </div>
    )
  }

  // Count memories by category
  const counts = memories.reduce((acc, m) => {
    acc[m.memory_type] = (acc[m.memory_type] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const memoryTypes = [
    { value: "all", label: "All Memories", icon: BookOpen, count: memories.length },
    { value: "brand_voice", label: "Brand Voice", icon: Bookmark, count: counts["brand_voice"] || 0 },
    { value: "icp", label: "ICP / Target Audience", icon: Target, count: counts["icp"] || 0 },
    { value: "competitor", label: "Competitors", icon: ShieldAlert, count: counts["competitor"] || 0 },
    { value: "campaign_goal", label: "Campaign Goals", icon: ArrowUpRight, count: counts["campaign_goal"] || 0 },
    { value: "previous_decision", label: "Strategic Decisions", icon: Brain, count: counts["previous_decision"] || 0 },
    { value: "experiment", label: "Experiments", icon: Sparkles, count: counts["experiment"] || 0 },
    { value: "data_gap", label: "Data Gaps", icon: Tag, count: counts["data_gap"] || 0 }
  ]

  const filteredMemories = memories.filter((m) => {
    const matchesFilter = filterType === "all" || m.memory_type === filterType
    const matchesSearch = 
      m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
    return matchesFilter && matchesSearch
  })

  return (
    <div className="space-y-6">
      {/* Title & Add Action */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
            <Brain className="w-4 h-4 text-primary" />
            Strategy Brain (Persistent Memory)
          </h2>
          <p className="text-[11px] text-muted-foreground mt-0.5 leading-relaxed">
            Persistent marketing knowledge, competitor insights, brand positioning guidelines, and swarm-extracted facts for <span className="text-foreground font-semibold">{activeProject.name}</span>.
          </p>
        </div>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="flex items-center gap-1 px-3 py-1.5 bg-primary hover:bg-primary/95 text-primary-foreground font-semibold rounded-lg text-xs transition shadow-sm"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Add Fact</span>
        </button>
      </div>

      {successMsg && (
        <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium rounded-lg flex items-center gap-2 animate-fade-in">
          <Check className="w-4 h-4" />
          <span>Fact successfully committed to SwarmOps memory!</span>
        </div>
      )}

      {/* Manual Memory Form */}
      {showAddForm && (
        <form onSubmit={handleSubmit} className="bg-card border border-border/80 rounded-xl p-5 space-y-4 animate-slide-in">
          <div className="flex items-center justify-between border-b border-border/40 pb-2">
            <h3 className="font-semibold text-xs text-foreground flex items-center gap-1.5">
              <Plus className="w-3.5 h-3.5 text-primary" />
              Commit Fact to Strategy Brain
            </h3>
            <button 
              type="button" 
              onClick={() => setShowAddForm(false)}
              className="text-[10px] text-muted-foreground hover:text-foreground"
            >
              Cancel
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1.5">
                Fact Classification
              </label>
              <select
                value={newType}
                onChange={(e) => setNewType(e.target.value)}
                className="w-full px-3 py-2 bg-input border border-border rounded-lg text-xs text-foreground outline-none focus:border-primary transition"
              >
                <option value="brand_voice">Brand Voice (Tone, guidelines)</option>
                <option value="icp">ICP / Target Audience (Personas)</option>
                <option value="competitor">Competitor Insight</option>
                <option value="campaign_goal">Campaign Goal / OKRs</option>
                <option value="previous_decision">Strategic Decision Made</option>
                <option value="experiment">Experiment Roadmap / Learns</option>
                <option value="data_gap">Data Gap / System Audit</option>
                <option value="report_insight">Report Insight / KPI Fact</option>
              </select>
            </div>

            <div>
              <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1.5">
                Core tags (comma separated)
              </label>
              <input
                type="text"
                value={newTagsStr}
                onChange={(e) => setNewTagsStr(e.target.value)}
                placeholder="organic, seo, low-cac, pricing"
                className="w-full px-3 py-2 bg-input border border-border rounded-lg text-xs text-foreground outline-none focus:border-primary transition"
              />
            </div>
          </div>

          <div>
            <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1.5">
              Title / Short Summary (e.g. competitor G2 score is 4.8)
            </label>
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="e.g., ICP prefers product-led growth onboarding flows"
              required
              className="w-full px-3 py-2 bg-input border border-border rounded-lg text-xs text-foreground outline-none focus:border-primary transition"
            />
          </div>

          <div>
            <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider block mb-1.5">
              Descriptive Rationale or Context
            </label>
            <textarea
              value={newSummary}
              onChange={(e) => setNewSummary(e.target.value)}
              placeholder="Provide a specific 2-3 sentence fact. Agents use this to adapt their creative recommendations and GTM campaigns so they do not repeat old strategies."
              required
              rows={3}
              className="w-full px-3 py-2 bg-input border border-border rounded-lg text-xs text-foreground outline-none focus:border-primary transition resize-none leading-relaxed"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="w-full py-2 bg-primary hover:bg-primary/95 text-primary-foreground text-xs font-semibold rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-1.5 shadow-sm"
          >
            {submitting ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Brain className="w-3.5 h-3.5" />
            )}
            {submitting ? "Writing to Supabase..." : "Commit to Persistent Memory"}
          </button>
        </form>
      )}

      {/* Main Panel Content */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Sidebar Category Filter */}
        <div className="lg:col-span-1 space-y-1 bg-muted/10 border border-border/40 rounded-xl p-2 h-fit">
          <div className="text-[9px] font-bold text-muted-foreground uppercase tracking-wider px-2 py-2 border-b border-border/30 mb-1">
            Filter by Class
          </div>
          {memoryTypes.map((type) => {
            const Icon = type.icon
            const isSelected = filterType === type.value
            return (
              <button
                key={type.value}
                onClick={() => setFilterType(type.value)}
                className={`w-full flex items-center justify-between px-2.5 py-2 rounded-lg text-[11px] transition ${
                  isSelected 
                    ? "bg-primary/10 text-primary border border-primary/10 font-medium" 
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/40"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className="w-3.5 h-3.5" />
                  <span>{type.label}</span>
                </div>
                {type.count > 0 && (
                  <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                    isSelected ? "bg-primary/20 text-primary" : "bg-muted text-muted-foreground"
                  }`}>
                    {type.count}
                  </span>
                )}
              </button>
            )
          })}
        </div>

        {/* Right Pane List */}
        <div className="lg:col-span-3 space-y-4">
          {/* Search bar */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-muted-foreground absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search persistent memories by title, tag, or content..."
              className="w-full pl-9 pr-4 py-2 bg-card border border-border rounded-xl text-xs text-foreground outline-none focus:border-primary transition"
            />
          </div>

          {/* Memories Cards */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 bg-card border border-border rounded-xl">
              <Loader2 className="w-5 h-5 text-primary animate-spin mb-2" />
              <span className="text-xs text-muted-foreground">Reading project database...</span>
            </div>
          ) : filteredMemories.length === 0 ? (
            <div className="text-center py-20 bg-card border border-border rounded-xl">
              <Brain className="w-6 h-6 text-muted-foreground/40 mx-auto mb-3" />
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                No persistent memories found for filter <span className="font-semibold text-foreground">"{filterType}"</span>. Swarm decisions and manual additions will compile here.
              </p>
            </div>
          ) : (
            <div className="space-y-3.5">
              {filteredMemories.map((m) => (
                <div 
                  key={m.id} 
                  className="bg-card border border-border rounded-xl p-4.5 hover:border-border-hover transition group flex flex-col justify-between gap-3 relative"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      {/* Classification Badge */}
                      <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider bg-primary/10 border border-primary/20 text-primary mb-2.5">
                        {m.memory_type.replace("_", " ")}
                      </span>
                      <h4 className="font-semibold text-xs text-foreground leading-snug">
                        {m.title}
                      </h4>
                      <p className="text-[11px] text-muted-foreground mt-1.5 leading-relaxed whitespace-pre-line">
                        {m.summary}
                      </p>
                    </div>

                    <button
                      onClick={() => handleDelete(m.id)}
                      className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive rounded transition-all"
                      title="Delete memory"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>

                  {/* Metadata Row */}
                  <div className="flex flex-wrap items-center gap-3 pt-3 border-t border-border/30 text-[10px] text-muted-foreground/70">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {new Date(m.created_at).toLocaleDateString()}
                    </span>
                    <span className="flex items-center gap-1 capitalize">
                      <User className="w-3 h-3" />
                      Source: {m.source.replace("_", " ")}
                    </span>
                    {m.confidence !== undefined && (
                      <span>
                        Confidence: <span className="text-primary font-medium">{Math.round(m.confidence * 100)}%</span>
                      </span>
                    )}
                    {m.tags && m.tags.length > 0 && (
                      <div className="flex items-center gap-1.5 ml-auto">
                        <Tag className="w-3 h-3 text-primary/60" />
                        <div className="flex items-center gap-1 flex-wrap">
                          {m.tags.map((t, idx) => (
                            <span key={idx} className="bg-muted px-1.5 py-0.5 rounded text-[9px] text-muted-foreground">
                              {t}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
