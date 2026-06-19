import { useEffect, useState } from "react"
import type { Project } from "./api"
import IntakeFlow from "./features/intake/IntakeFlow"
import ProjectDashboard from "./features/intake/components/ProjectDashboard"

const LAST_PROJECT_KEY = "zero-to-one:last-project"

function readStoredProject() {
  const storedProject = sessionStorage.getItem(LAST_PROJECT_KEY)
  if (!storedProject) return null

  try {
    return JSON.parse(storedProject) as Project
  } catch {
    sessionStorage.removeItem(LAST_PROJECT_KEY)
    return null
  }
}

function navigate(path: string) {
  window.history.pushState({}, "", path)
  window.dispatchEvent(new PopStateEvent("popstate"))
}

export default function App() {
  const [path, setPath] = useState(() => window.location.pathname)
  const [project, setProject] = useState<Project | null>(() => readStoredProject())

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

  function handleProjectCreated(createdProject: Project) {
    setProject(createdProject)
    sessionStorage.setItem(LAST_PROJECT_KEY, JSON.stringify(createdProject))
    navigate("/dashboard")
  }

  if (path === "/dashboard") {
    return <ProjectDashboard project={project} onBackHome={() => navigate("/home")} />
  }

  return <IntakeFlow onProjectCreated={handleProjectCreated} />
}
