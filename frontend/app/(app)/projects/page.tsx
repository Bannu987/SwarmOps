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
    let { data: { session } } = await supabase.auth.getSession()
    
    if (!session) {
      // Try fallback to getUser which can restore the session from cookies/refresh tokens
      console.info("[PROJECT CREATION] Active session not found via getSession. Attempting getUser recovery fallback...")
      const { data: { user } } = await supabase.auth.getUser()
      if (user) {
        console.info("[PROJECT CREATION] User recovered via getUser. Fetching fresh session...")
        const fresh = await supabase.auth.getSession()
        session = fresh.data.session
      }
    }
    
    if (!session) {
      setError("Your session has expired or is invalid. Please sign in again.")
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
      console.error("Failed to create workspace:", err)
      
      let errMsg = "Workspace setup failed. Please retry."
      if (err instanceof TypeError || (err.message && (err.message.toLowerCase().includes("fetch") || err.message.toLowerCase().includes("cors")))) {
        errMsg = "Workspace setup failed: Network connection blocked. Please try again."
      }
      
      setError(errMsg)
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8 animate-fade-in">
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-8 border-b border-border/60 pb-5">
          <div>
            <h1 className="text-2xl md:text-3xl font-serif font-normal tracking-tight text-foreground mb-1">
              Workspaces
            </h1>
            <p className="text-xs text-muted-foreground">Manage your strategic brands, campaigns, and machine networks.</p>
          </div>
          <button
            onClick={() => {
              setError(null)
              setSuccess(null)
              setShowCreate(true)
            }}
            className="px-3.5 py-1.5 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded transition-all duration-300 flex items-center gap-1.5 shadow-md border border-primary/20"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Workspace</span>
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-16 gap-3">
            <Loader2 className="w-5 h-5 text-primary animate-spin" />
            <div className="text-xs text-muted-foreground font-mono uppercase tracking-wider">SYNCING WORKSPACES...</div>
          </div>
        ) : projects.length === 0 ? (
          <WelcomeOnboarding onCreateProjectClick={() => setShowCreate(true)} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 animate-fade-in">
            {projects.map((p) => (
              <div
                key={p.id}
                onClick={() => {
                  selectProject(p.id)
                  router.push("/dashboard")
                }}
                className="bg-card/65 border border-border/40 rounded-lg p-5 hover:border-primary/45 hover:bg-card/90 transition-all duration-300 shadow-sm cursor-pointer relative group flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between mb-3 border-b border-border/30 pb-2.5">
                    <FolderKanban className="w-4 h-4 text-primary" />
                    {p.pinned && <Pin className="w-3 h-3 text-primary fill-primary/20" />}
                  </div>
                  <h3 className="font-sans font-semibold text-sm text-foreground mb-1 group-hover:text-primary transition duration-300">{p.name}</h3>
                </div>
                {p.website_url ? (
                  <p className="text-[10px] font-mono text-muted-foreground truncate bg-muted/40 px-2 py-0.5 rounded border border-border/20 mt-3">{p.website_url}</p>
                ) : (
                  <p className="text-[10px] font-mono text-muted-foreground/40 italic mt-3">NO_URL_DECLARED</p>
                )}
              </div>
            ))}
          </div>
        )}

        {showCreate && (
          <div className="fixed inset-0 bg-black/75 flex items-center justify-center z-50 p-4 backdrop-blur-[2px]">
            <div className="bg-card border border-border/60 rounded-lg max-w-md w-full p-6 animate-slide-up shadow-2xl">
              <h3 className="text-sm font-semibold text-foreground mb-4 uppercase tracking-wider">Create Workspace</h3>
              
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

              <div className="space-y-4">
                <div>
                  <label className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5 block">
                    Workspace Name
                  </label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Acme Marketing"
                    disabled={creating || success !== null}
                    className="w-full px-3 py-2 bg-card/75 border border-border/80 rounded text-xs text-foreground outline-none focus:border-primary/80 disabled:opacity-50 transition"
                  />
                </div>
                <div>
                  <label className="text-[9px] font-mono uppercase tracking-wider text-muted-foreground mb-1.5 block">
                    Website URL (optional)
                  </label>
                  <input
                    type="url"
                    value={website}
                    onChange={(e) => setWebsite(e.target.value)}
                    placeholder="https://acme.com"
                    disabled={creating || success !== null}
                    className="w-full px-3 py-2 bg-card/75 border border-border/80 rounded text-xs text-foreground outline-none focus:border-primary/80 disabled:opacity-50 transition"
                  />
                </div>
              </div>
              <div className="flex gap-2.5 mt-6 border-t border-border/30 pt-4 justify-end">
                <button
                  onClick={() => setShowCreate(false)}
                  disabled={creating}
                  className="px-4 py-2 bg-card border border-border hover:bg-muted text-xs text-foreground transition disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreate}
                  disabled={creating || !name.trim() || success !== null}
                  className="px-4 py-2 bg-primary hover:bg-primary/95 text-primary-foreground font-mono text-[10px] uppercase tracking-wider rounded transition-all duration-300 disabled:opacity-50 flex items-center justify-center gap-1.5 shadow-md border border-primary/20"
                >
                  {creating && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{creating ? "Creating..." : "Confirm Workspace"}</span>
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
