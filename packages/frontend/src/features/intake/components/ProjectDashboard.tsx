import { useEffect, useState } from "react"
import type { Project, Step, Task } from "../../../api"
import { apiFetch } from "../../../api/client"
import TopNav from "./TopNav"
import "../IntakeFlow.css"
import "../../project/Dashboard.css"

type Props = {
  projects: Project[]
  selectedProject: Project | null
  onSelectProject: (p: Project) => void
  onBackHome: () => void
}

type LockAlert = { stepTitle: string; depNames: string[] } | null
type TaskMap = Record<string, "todo" | "done">
type StepStatusMap = Record<string, Step["status"]>

const CARDS_PER_PAGE = 3

function buildTaskMap(steps: Step[]): TaskMap {
  const map: TaskMap = {}
  for (const step of steps) {
    for (const task of step.tasks) {
      map[task.id] = task.status
    }
  }
  return map
}

function buildStepStatusMap(steps: Step[]): StepStatusMap {
  const map: StepStatusMap = {}
  for (const step of steps) {
    map[step.id] = step.status
  }
  return map
}

function getDayLabel(steps: Step[], idx: number): string {
  const step = steps[idx]
  const base = steps[0]?.intended_start
  if (!step?.intended_start || !base) return `Day ${idx * 7}`
  const days = Math.round(
    (new Date(step.intended_start).getTime() - new Date(base).getTime()) / 86400000,
  )
  return `Day ${days}`
}

export default function ProjectDashboard({
  projects: propProjects,
  selectedProject: propSelected,
  onSelectProject,
  onBackHome,
}: Props) {
  const [allProjects, setAllProjects] = useState<Project[]>(propProjects)
  const [selectedProject] = useState<Project | null>(propSelected)

  // project completion checkbox — synced from backend on mount
  const [completedIds, setCompletedIds] = useState<Set<string>>(
    () => new Set(propProjects.filter((p) => p.status === "completed").map((p) => p.id)),
  )

  // lazily-fetched tasks per step id
  const [stepTasks, setStepTasks] = useState<Record<string, Task[]>>({})

  // local step statuses (updated when user marks a step done)
  const [stepStatuses, setStepStatuses] = useState<StepStatusMap>(() =>
    buildStepStatusMap(propSelected?.steps ?? []),
  )

  const [offset, setOffset] = useState(0)
  const [expandedId, setExpandedId] = useState<string | null>(null)
  const [taskMap, setTaskMap] = useState<TaskMap>(() =>
    buildTaskMap(propSelected?.steps ?? []),
  )
  const [lockAlert, setLockAlert] = useState<LockAlert>(null)

  // Fetch all projects from backend — also refreshes completedIds from real DB state
  useEffect(() => {
    apiFetch<Project[]>("/projects")
      .then((fetched) => {
        setAllProjects(fetched)
        setCompletedIds(
          new Set(fetched.filter((p) => p.status === "completed").map((p) => p.id)),
        )
      })
      .catch(() => {})
  }, [])

  // Lazy-load tasks when a step is expanded
  useEffect(() => {
    if (!expandedId) return
    const step = selectedProject?.steps.find((s) => s.id === expandedId)
    if (!step) return
    if (stepTasks[expandedId] !== undefined) return
    if (step.tasks.length > 0) {
      setStepTasks((prev) => ({ ...prev, [expandedId]: step.tasks }))
      return
    }
    apiFetch<Task[]>(`/steps/${expandedId}/tasks`)
      .then((tasks) => {
        setStepTasks((prev) => ({ ...prev, [expandedId]: tasks }))
        setTaskMap((prev) => {
          const next = { ...prev }
          for (const t of tasks) next[t.id] = t.status
          return next
        })
      })
      .catch(() => setStepTasks((prev) => ({ ...prev, [expandedId]: [] })))
  }, [expandedId])

  // ── Helpers ──

  function displayName(project: Project): string {
    const idx = allProjects.findIndex((p) => p.id === project.id)
    return idx === -1 ? project.title : `Project ${idx + 1}`
  }

  function toggleProjectComplete(p: Project) {
    const nowComplete = !completedIds.has(p.id)
    setCompletedIds((prev) => {
      const next = new Set(prev)
      nowComplete ? next.add(p.id) : next.delete(p.id)
      return next
    })
    apiFetch(`/projects/${p.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: nowComplete ? "completed" : "active" }),
    }).catch(() =>
      setCompletedIds((prev) => {
        const next = new Set(prev)
        nowComplete ? next.delete(p.id) : next.add(p.id)
        return next
      }),
    )
  }

  function stepStatus(step: Step): Step["status"] {
    return stepStatuses[step.id] ?? step.status
  }

  function isStepLocked(step: Step): boolean {
    return step.depends_on.some((depId) => {
      const dep = steps.find((s) => s.id === depId)
      return dep && stepStatus(dep) !== "done"
    })
  }

  function getBlockingDepNames(step: Step): string[] {
    return step.depends_on
      .map((depId) => steps.find((s) => s.id === depId))
      .filter((s): s is Step => !!s && stepStatus(s) !== "done")
      .map((s) => s.title)
  }

  function allTasksDone(step: Step): boolean {
    const tasks = stepTasks[step.id] ?? step.tasks
    return tasks.length > 0 && tasks.every((t) => taskMap[t.id] === "done")
  }

  function isStepMarkedDone(step: Step): boolean {
    return stepStatus(step) === "done"
  }

  // Bug fix: only the checkbox toggles the task, not the whole row
  function toggleTask(taskId: string) {
    const newStatus: "todo" | "done" = taskMap[taskId] === "done" ? "todo" : "done"
    setTaskMap((prev) => ({ ...prev, [taskId]: newStatus }))
    apiFetch(`/tasks/${taskId}`, {
      method: "PATCH",
      body: JSON.stringify({ status: newStatus }),
    }).catch(() =>
      // revert on failure
      setTaskMap((prev) => ({ ...prev, [taskId]: newStatus === "done" ? "todo" : "done" })),
    )
  }

  function markStepDone(step: Step) {
    setStepStatuses((prev) => ({ ...prev, [step.id]: "done" }))
    apiFetch(`/steps/${step.id}`, {
      method: "PATCH",
      body: JSON.stringify({ status: "done" }),
    }).catch(() =>
      setStepStatuses((prev) => ({ ...prev, [step.id]: step.status })),
    )
  }

  // ── Derived ──

  const project = selectedProject
  const steps = project?.steps ?? []
  const milestones = project?.milestones ?? []
  const visibleSteps = steps.slice(offset, offset + CARDS_PER_PAGE)
  const expandedStep = steps.find((s) => s.id === expandedId) ?? null
  const expandedTasks = expandedId !== null
    ? (stepTasks[expandedId] ?? expandedStep?.tasks ?? [])
    : []

  /* ── No project ── */
  if (!project) {
    return (
      <main className="idea-shell">
        <TopNav />
        <section className="hero-stage">
          <div className="form-panel" style={{ textAlign: "center", maxWidth: 560 }}>
            <span className="eyebrow">Dashboard</span>
            <h1 style={{ fontSize: "clamp(32px,4vw,54px)", margin: 0 }}>No project yet.</h1>
            <p style={{ marginTop: 16 }}>Create a project from the home flow first.</p>
            <div className="panel-actions" style={{ marginTop: 24 }}>
              <button className="primary-button" onClick={onBackHome}>Back home</button>
            </div>
          </div>
        </section>
      </main>
    )
  }

  /* ── Dashboard ── */
  return (
    <div className="db-shell">
      {/* Sidebar */}
      <aside className="db-sidebar">
        <div className="db-sidebar-top">
          <span className="db-sidebar-app-name">Dashboard</span>
          <button className="db-detail-btn" onClick={onBackHome} title="Back home">✕</button>
        </div>

        <div className="db-sidebar-section-header">
          <span className="db-sidebar-label">Projects</span>
          <span className="db-sidebar-label">Detail</span>
        </div>

        <ul className="db-project-list">
          {allProjects.map((p: Project) => (
            <li key={p.id} className={`db-project-item ${p.id === project.id ? "active" : ""}`}>
              <button
                className={`db-project-icon-btn${completedIds.has(p.id) ? " completed" : ""}`}
                title={completedIds.has(p.id) ? "Mark active" : "Mark complete"}
                onClick={() => toggleProjectComplete(p)}
              />
              <span className="db-project-name" onClick={() => onSelectProject(p)}>
                {displayName(p)}
              </span>
              <button className="db-detail-btn" onClick={() => onSelectProject(p)}>Detail</button>
            </li>
          ))}
        </ul>
      </aside>

      {/* Main content */}
      <main className="db-main">
        <h1 className="db-project-title">{displayName(project)}</h1>

        {/* Slider: timeline + cards + arrows */}
        <div className="db-slider-wrap">
          <button
            className="db-arrow"
            onClick={() => setOffset((o) => Math.max(0, o - 1))}
            disabled={offset === 0}
          >←</button>

          <div className="db-cards-column">
            {/* Timeline */}
            <div className="db-timeline">
              <div className="db-timeline-line" />
              {visibleSteps.map((step, i) => {
                const pct = visibleSteps.length === 1
                  ? "50%"
                  : `${(i / (visibleSteps.length - 1)) * 100}%`
                const hasMilestone = milestones.some((m) => m.step_id === step.id)
                return (
                  <div key={step.id} className="db-timeline-marker" style={{ left: pct }}>
                    <span className="db-timeline-label">{getDayLabel(steps, offset + i)}</span>
                    {hasMilestone
                      ? <div className="db-timeline-diamond" />
                      : <div className="db-timeline-dot" />}
                  </div>
                )
              })}
            </div>

            {/* Step cards */}
            <div className="db-cards">
              {visibleSteps.map((step) => {
                const locked = isStepLocked(step)
                const done = allTasksDone(step) || isStepMarkedDone(step)
                const active = step.id === expandedId
                return (
                  <div
                    key={step.id}
                    className={`db-step-card${done ? " step-done" : ""}${active ? " step-active" : ""}`}
                    onClick={() => {
                      // Bug fix: locked card shows alert instead of expanding
                      if (locked) {
                        setLockAlert({ stepTitle: step.title, depNames: getBlockingDepNames(step) })
                        return
                      }
                      setExpandedId((prev) => (prev === step.id ? null : step.id))
                    }}
                  >
                    <div className="db-card-header">
                      <h3 className="db-card-title">{step.title}</h3>
                      <div className="db-card-actions">
                        {locked ? (
                          <button
                            className="db-icon-btn db-lock-btn"
                            title="Dependencies not complete"
                            onClick={(e) => {
                              e.stopPropagation()
                              setLockAlert({ stepTitle: step.title, depNames: getBlockingDepNames(step) })
                            }}
                          >🔒</button>
                        ) : (
                          <button
                            className="db-icon-btn"
                            title={active ? "Minimize" : "Expand"}
                            onClick={(e) => {
                              e.stopPropagation()
                              setExpandedId((prev) => (prev === step.id ? null : step.id))
                            }}
                          >{active ? "▲" : "▼"}</button>
                        )}
                      </div>
                    </div>
                    <p className="db-card-desc">{step.description}</p>
                  </div>
                )
              })}
            </div>
          </div>

          <button
            className="db-arrow"
            onClick={() => setOffset((o) => Math.min(steps.length - CARDS_PER_PAGE, o + 1))}
            disabled={offset + CARDS_PER_PAGE >= steps.length}
          >→</button>
        </div>

        {/* Task panel for expanded step */}
        {expandedStep && (
          <div className="db-task-panel">
            {expandedTasks.length === 0 ? (
              <p style={{ color: "var(--muted)", margin: 0, fontSize: 15 }}>
                {stepTasks[expandedStep.id] === undefined ? "Loading tasks…" : "No tasks yet for this step."}
              </p>
            ) : (
              expandedTasks.map((task) => {
                const done = taskMap[task.id] === "done"
                return (
                  // Bug fix: onClick only on the checkbox, not the whole row
                  <div key={task.id} className={`db-task-item${done ? " task-done" : ""}`}>
                    <div className="db-avatar">A</div>
                    <span className="db-task-title">{task.title}</span>
                    <button
                      className={`db-checkbox${done ? " checked" : ""}`}
                      onClick={() => toggleTask(task.id)}
                    >{done && "✓"}</button>
                  </div>
                )
              })
            )}

            {/* Show "Mark step as complete" only when all tasks are ticked */}
            {expandedStep && allTasksDone(expandedStep) && !isStepMarkedDone(expandedStep) && (
              <div className="db-task-actions" style={{ justifyContent: "space-between" }}>
                <button
                  className="primary-button"
                  style={{ background: "var(--green)", borderColor: "var(--green)" }}
                  onClick={() => markStepDone(expandedStep)}
                >
                  Mark step as complete
                </button>
                <button className="secondary-button">Apply to chat</button>
              </div>
            )}
            {!(expandedStep && allTasksDone(expandedStep) && !isStepMarkedDone(expandedStep)) && (
              <div className="db-task-actions">
                <button className="primary-button">Apply to chat</button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Lock alert modal */}
      {lockAlert && (
        <div className="db-modal-overlay" onClick={() => setLockAlert(null)}>
          <div className="db-modal" onClick={(e) => e.stopPropagation()}>
            <p className="db-modal-title">Step locked</p>
            <p className="db-modal-body">
              You should complete{" "}
              <strong>{lockAlert.depNames.map((n) => `"${n}"`).join(", ")}</strong>{" "}
              before moving on with <strong>"{lockAlert.stepTitle}"</strong>.
            </p>
            <div className="db-modal-actions">
              <button className="secondary-button" onClick={() => setLockAlert(null)}>Cancel</button>
              <button className="primary-button" onClick={() => setLockAlert(null)}>Proceed anyway</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
