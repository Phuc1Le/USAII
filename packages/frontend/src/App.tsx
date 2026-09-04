import { useEffect, useState } from "react"
import type { Project } from "./api"
import {
  apiFetch,
  clearSession,
  getStoredUser,
  SIGNED_OUT_EVENT,
  type AuthUser,
} from "./api/client"
import AuthPanel from "./features/auth/AuthPanel"
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
  const [user, setUser] = useState<AuthUser | null>(() => getStoredUser())
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

  // The cached projects belong to whoever was signed in when they were cached.
  // Signing in or out changes who the backend answers as, so the cache has to go
  // with the old identity — otherwise the new one briefly sees someone else's list.
  function forgetCachedProjects() {
    sessionStorage.removeItem(PROJECTS_KEY)
    sessionStorage.removeItem(SELECTED_KEY)
    setProjects([])
    setSelectedProject(null)
  }

  // A token can expire in the middle of any request, so client.ts clears the
  // session and announces it once rather than every caller handling a 401.
  useEffect(() => {
    function handleSignedOut() {
      setUser(null)
      forgetCachedProjects()
    }
    window.addEventListener(SIGNED_OUT_EVENT, handleSignedOut)
    return () => window.removeEventListener(SIGNED_OUT_EVENT, handleSignedOut)
  }, [])

  // sessionStorage is scoped per tab, so a fresh tab/session lands here with no local
  // project state even though the backend already has projects — fall back to fetching
  // them instead of showing "no project yet" incorrectly.
  useEffect(() => {
    if (projects.length > 0) return
    let cancelled = false
    apiFetch<Project[]>("/projects")
      .then((fetched) => {
        if (cancelled || fetched.length === 0) return
        setProjects(fetched)
        sessionStorage.setItem(PROJECTS_KEY, JSON.stringify(fetched))
        const lastSelectedId = readStored<Project | null>(SELECTED_KEY, null)?.id
        const toSelect = fetched.find((p) => p.id === lastSelectedId) ?? fetched[fetched.length - 1]
        setSelectedProject(toSelect)
        sessionStorage.setItem(SELECTED_KEY, JSON.stringify(toSelect))
      })
      .catch(() => {
        // stay on the "no project yet" state if the backend is unreachable
      })
    return () => {
      cancelled = true
    }
  }, [projects.length, user?.id])

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

  function handleSignedIn(signedIn: AuthUser) {
    setUser(signedIn)
    // Registering keeps this browser's projects, but signing in as someone else
    // does not — either way the safe move is to drop the cache and re-read.
    forgetCachedProjects()
    navigate("/home")
  }

  function handleSignOut() {
    clearSession()
    setUser(null)
    forgetCachedProjects()
    navigate("/home")
  }

  if (path === "/login") {
    return <AuthPanel onSignedIn={handleSignedIn} onCancel={() => navigate("/home")} />
  }

  const accountBar = (
    <div className="account-bar">
      {user ? (
        <>
          <span>{user.email ?? user.display_name}</span>
          <button type="button" onClick={handleSignOut}>
            Sign out
          </button>
        </>
      ) : (
        <button type="button" onClick={() => navigate("/login")}>
          Sign in
        </button>
      )}
    </div>
  )

  if (path === "/dashboard") {
    return (
      <>
        {accountBar}
        <ProjectDashboard
          key={selectedProject?.id ?? "none"}
          projects={projects}
          selectedProject={selectedProject}
          onSelectProject={handleSelectProject}
          onBackHome={() => navigate("/home")}
        />
      </>
    )
  }

  return (
    <>
      {accountBar}
      <IntakeFlow onProjectCreated={handleProjectCreated} />
    </>
  )
}
