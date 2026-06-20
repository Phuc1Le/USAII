import { useEffect, useState } from "react"
import type { Project } from "./api"
import IntakeFlow from "./features/intake/IntakeFlow"
import ProjectDashboard from "./features/intake/components/ProjectDashboard"

const PROJECTS_KEY = "zero-to-one:projects"
const SELECTED_KEY = "zero-to-one:last-project"

function readStored<T>(key: string, fallback: T): T {
  try {
    const raw = sessionStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : fallback
  } catch {
    return fallback
  }
}

function navigate(path: string) {
  window.history.pushState({}, "", path)
  window.dispatchEvent(new PopStateEvent("popstate"))
}

export default function App() {
  const [path, setPath] = useState(() => window.location.pathname)
  const [projects, setProjects] = useState<Project[]>(() =>
    readStored<Project[]>(PROJECTS_KEY, []),
  )
  const [selectedProject, setSelectedProject] = useState<Project | null>(() =>
    readStored<Project | null>(SELECTED_KEY, null),
  )

  useEffect(() => {
    function syncPath() {
      setPath(window.location.pathname)
    }
    window.addEventListener("popstate", syncPath)
    if (window.location.pathname === "/") {
      window.history.replaceState({}, "", "/home")
      syncPath()
    }
    return () => window.removeEventListener("popstate", syncPath)
  }, [])

  function handleProjectCreated(created: Project) {
    setProjects((prev) => {
      const next = [...prev.filter((p) => p.id !== created.id), created]
      sessionStorage.setItem(PROJECTS_KEY, JSON.stringify(next))
      return next
    })
    setSelectedProject(created)
    sessionStorage.setItem(SELECTED_KEY, JSON.stringify(created))
    navigate("/dashboard")
  }

  function handleSelectProject(p: Project) {
    setSelectedProject(p)
    sessionStorage.setItem(SELECTED_KEY, JSON.stringify(p))
  }

  if (path === "/dashboard") {
    return (
      <ProjectDashboard
        key={selectedProject?.id ?? "none"}
        projects={projects}
        selectedProject={selectedProject}
        onSelectProject={handleSelectProject}
        onBackHome={() => navigate("/home")}
      />
    )
  }

  return <IntakeFlow onProjectCreated={handleProjectCreated} />
}
