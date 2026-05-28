import { useState, useEffect, useCallback } from "react"
import { listProjects } from "@/lib/api"
import type { Project } from "@/types"

export function useActiveProject() {
  const [projects, setProjects] = useState<Project[]>([])
  const [activeProject, setActiveProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)

  const loadProjects = useCallback(async () => {
    try {
      const res = await listProjects()
      const list = res.projects || []
      setProjects(list)
      
      if (list.length > 0) {
        const storedId = typeof window !== "undefined" ? localStorage.getItem("active_project_id") : null
        const found = list.find((p: Project) => p.id === storedId)
        const active = found || list[0]
        setActiveProject(active)
        if (typeof window !== "undefined" && active) {
          localStorage.setItem("active_project_id", active.id)
        }
      } else {
        setActiveProject(null)
      }
    } catch (err) {
      console.error("Failed to load active project:", err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  const selectProject = (projectId: string) => {
    const found = projects.find((p) => p.id === projectId)
    if (found) {
      setActiveProject(found)
      if (typeof window !== "undefined") {
        localStorage.setItem("active_project_id", projectId)
      }
    }
  }

  return {
    projects,
    activeProject,
    loading,
    selectProject,
    refreshProjects: loadProjects,
  }
}
