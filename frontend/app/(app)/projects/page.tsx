"use client"

import { useEffect, useState, Suspense } from "react"
import { Plus, FolderKanban, Pin, Loader2 } from "lucide-react"
import { listProjects, createProject } from "@/lib/api"
import type { Project } from "@/types"
import { createClient } from "@/lib/supabase/client"
import { WelcomeOnboarding } from "@/components/shared/WelcomeOnboarding"
import { useSearchParams, useRouter } from "next/navigation"
import { useActiveProject } from "@/lib/hooks/useActiveProject"

function ProjectsList() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { selectProject } = useActiveProject()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [name, setName] = useState("")
  const [website, setWebsite] = useState("")
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    loadProjects()
  }, [])

  useEffect(() => {
    if (searchParams && searchParams.get("create") === "true") {
      setShowCreate(true)
    }
  }, [searchParams])

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
    const trimmedName = name.trim()
    if (!trimmedName) {
      setError("Project name is required")
      return
    }

    if (website && !/^https?:\/\/[^\s$.?#].[^\s]*$/i.test(website.trim())) {
      setError("Please provide a valid website URL starting with http:// or https://")
      return
    }

    const supabase = createClient()
    const { data: { session } } = await supabase.auth.getSession()
    if (!session) {
      setError("Your session has expired. Please log in again.")
      return
    }

    setCreating(true)
    setError(null)
    setSuccess(null)

    try {
      const res = await createProject({ name: trimmedName, website_url: website.trim() })
      
      if (res.error || res.detail) {
        throw new Error(res.error || res.detail || "Failed to create project")
      }
      
      if (res.id) {
        if (typeof window !== "undefined") {
          localStorage.setItem("active_project_id", res.id)
        }
        setSuccess(`Project created. SwarmOps is ready for ${res.name}.`)
      } else {
        setSuccess(`Project created successfully.`)
      }

      setName("")
      setWebsite("")
      
      // Close modal and reload page after a brief reading delay
      setTimeout(() => {
        setShowCreate(false)
        setSuccess(null)
        loadProjects()
        window.location.reload()
      }, 2000)

    } catch (err: any) {
      console.error("Failed to create project:", err)
      
      let errMsg = "Could not create project. Check if backend is waking up and try again."
      if (err instanceof TypeError || (err.message && (err.message.toLowerCase().includes("fetch") || err.message.toLowerCase().includes("cors")))) {
        errMsg = "Browser blocked the workspace request. Backend CORS must allow this Netlify domain or verify the Render service is running."
      } else if (err.message) {
        errMsg = err.message
      }
      
      setError(errMsg)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold mb-1">Workspaces</h1>
            <p className="text-sm text-muted-foreground">Create one workspace per brand, client, or business.</p>
          </div>
          <button
            onClick={() => {
              setError(null)
              setSuccess(null)
              setShowCreate(true)
            }}
            className="px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-lg transition flex items-center gap-2"
          >
            <Plus className="w-4 h-4" /> New Workspace
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <Loader2 className="w-5 h-5 text-primary animate-spin" />
            <div className="text-xs text-muted-foreground">Loading workspaces...</div>
          </div>
        ) : projects.length === 0 ? (
          <WelcomeOnboarding onCreateProjectClick={() => setShowCreate(true)} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-fade-in">
            {projects.map((p) => (
              <div
                key={p.id}
                onClick={() => {
                  selectProject(p.id)
                  router.push("/dashboard")
                }}
                className="bg-card border border-border rounded-xl p-5 hover:border-primary/50 transition cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <FolderKanban className="w-5 h-5 text-primary" />
                  {p.pinned && <Pin className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />}
                </div>
                <h3 className="font-semibold mb-1 text-foreground">{p.name}</h3>
                {p.website_url ? (
                  <p className="text-xs text-muted-foreground truncate">{p.website_url}</p>
                ) : (
                  <p className="text-xs text-muted-foreground/40 italic">No website URL</p>
                )}
              </div>
            ))}
          </div>
        )}

        {showCreate && (
          <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-card border border-border rounded-2xl max-w-md w-full p-6 animate-slide-up shadow-2xl">
              <h3 className="text-lg font-semibold mb-4 text-foreground">Create Workspace</h3>
              
              {error && (
                <div className="mb-4 p-3 bg-destructive/10 border border-destructive/30 rounded-lg text-xs text-destructive">
                  {error}
                </div>
              )}
              {success && (
                <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs text-emerald-400">
                  {success}
                </div>
              )}

              <div className="space-y-3">
                <div>
                  <label className="text-xs font-medium text-muted-foreground mb-1.5 block">
                    Workspace name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="My Brand"
                    disabled={creating || success !== null}
                    className="w-full px-3 py-2 bg-input border border-border rounded-lg text-sm text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary disabled:opacity-50 transition"
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
                    disabled={creating || success !== null}
                    className="w-full px-3 py-2 bg-input border border-border rounded-lg text-sm text-foreground outline-none focus:border-primary focus:ring-1 focus:ring-primary disabled:opacity-50 transition"
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-5">
                <button
                  onClick={handleCreate}
                  disabled={creating || !name.trim() || success !== null}
                  className="flex-1 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-lg transition disabled:opacity-50 flex items-center justify-center gap-2 shadow-md"
                >
                  {creating && <Loader2 className="w-4 h-4 animate-spin" />}
                  {creating ? "Creating..." : "Create"}
                </button>
                <button
                  onClick={() => setShowCreate(false)}
                  disabled={creating}
                  className="px-4 py-2 bg-muted text-sm rounded-lg hover:bg-muted/80 text-foreground transition disabled:opacity-50"
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

export default function ProjectsPage() {
  return (
    <Suspense fallback={
      <div className="flex-grow flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="w-6 h-6 text-primary animate-spin" />
          <div className="text-xs text-muted-foreground">Loading page context...</div>
        </div>
      </div>
    }>
      <ProjectsList />
    </Suspense>
  )
}
