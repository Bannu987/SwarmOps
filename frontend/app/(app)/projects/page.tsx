"use client"

import { useEffect, useState } from "react"
import { Plus, FolderKanban, Pin } from "lucide-react"
import { listProjects, createProject } from "@/lib/api"
import type { Project } from "@/types"

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState("")
  const [website, setWebsite] = useState("")
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    try {
      const data = await listProjects()
      setProjects(data.projects || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async () => {
    if (!name.trim()) return
    setCreating(true)
    try {
      await createProject({ name, website_url: website })
      setName("")
      setWebsite("")
      setShowCreate(false)
      loadProjects()
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold mb-1">Projects</h1>
            <p className="text-sm text-muted-foreground">Organize work by brand or workspace</p>
          </div>
          <button
            onClick={() => setShowCreate(true)}
            className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-lg transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> New Project
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12 text-muted-foreground text-sm">Loading...</div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16">
            <FolderKanban className="w-12 h-12 mx-auto text-muted-foreground mb-3" />
            <p className="text-sm text-muted-foreground mb-4">No projects yet</p>
            <button
              onClick={() => setShowCreate(true)}
              className="text-sm text-primary hover:underline"
            >
              Create your first project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => (
              <div
                key={p.id}
                className="bg-card border border-border rounded-xl p-5 hover:border-primary/50 transition cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <FolderKanban className="w-5 h-5 text-primary" />
                  {p.pinned && <Pin className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />}
                </div>
                <h3 className="font-semibold mb-1">{p.name}</h3>
                {p.website_url && (
                  <p className="text-xs text-muted-foreground truncate">{p.website_url}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {showCreate && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-card border border-border rounded-2xl max-w-md w-full p-6 animate-slide-up">
              <h3 className="text-lg font-semibold mb-4">Create Project</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Project name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="My Brand"
                    className="w-full px-3 py-2 bg-input border border-border rounded-lg text-sm outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Website URL (optional)
                  </label>
                  <input
                    type="url"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://yoursite.com"
                    className="w-full px-3 py-2 bg-input border border-border rounded-lg text-sm outline-none focus:border-primary"
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-5">
                <button
                  onClick={handleCreate}
                  disabled={creating || !name.trim()}
                  className="flex-1 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-lg transition disabled:opacity-50"
                >
                  {creating ? "Creating..." : "Create"}
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 bg-muted text-sm rounded-lg hover:bg-muted/80"
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
