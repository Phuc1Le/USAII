import type { Project } from "../../../api"
import "../IntakeFlow.css"

type ProjectDashboardProps = {
  project: Project | null
  onBackHome: () => void
}

export default function ProjectDashboard({ project, onBackHome }: ProjectDashboardProps) {
  if (!project) {
    return (
      <main className="idea-shell">
        <section className="hero-stage">
          <div className="dashboard-panel">
            <div>
              <span className="eyebrow">Project dashboard</span>
              <h1>No project yet.</h1>
            </div>
            <p>Create a project from the home flow first, then the dashboard will print it here.</p>
            <div className="panel-actions">
              <button className="primary-button" onClick={onBackHome}>
                Back home
              </button>
            </div>
          </div>
        </section>
      </main>
    )
  }

  return (
    <main className="idea-shell">
      <section className="hero-stage">
        <div className="dashboard-panel">
          <div>
            <span className="eyebrow">Project dashboard</span>
            <h1>{project.title}</h1>
          </div>

          <section className="dashboard-section">
            <h2>Project</h2>
            <dl>
              <div>
                <dt>ID</dt>
                <dd>{project.id}</dd>
              </div>
              <div>
                <dt>Category</dt>
                <dd>{project.category}</dd>
              </div>
              <div>
                <dt>Description</dt>
                <dd>{project.description}</dd>
              </div>
              <div>
                <dt>Idea</dt>
                <dd>{project.idea}</dd>
              </div>
              <div>
                <dt>Goal</dt>
                <dd>{project.goal}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{project.status}</dd>
              </div>
            </dl>
          </section>

          <section className="dashboard-section">
            <h2>Steps</h2>
            {project.steps.map((step) => (
              <article className="dashboard-item" key={step.id}>
                <h3>{step.order_index}. {step.title}</h3>
                <p>{step.description}</p>
                <dl>
                  <div>
                    <dt>ID</dt>
                    <dd>{step.id}</dd>
                  </div>
                  <div>
                    <dt>Status</dt>
                    <dd>{step.status}</dd>
                  </div>
                  <div>
                    <dt>Start</dt>
                    <dd>{step.intended_start ?? "Not set"}</dd>
                  </div>
                  <div>
                    <dt>End</dt>
                    <dd>{step.intended_end ?? "Not set"}</dd>
                  </div>
                  <div>
                    <dt>Depends on</dt>
                    <dd>{step.depends_on.length > 0 ? step.depends_on.join(", ") : "None"}</dd>
                  </div>
                </dl>
                <h4>Tasks</h4>
                {step.tasks.length > 0 ? (
                  <ul>
                    {step.tasks.map((task) => (
                      <li key={task.id}>
                        <strong>{task.title}</strong> ({task.status}) - {task.detail}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p>No tasks yet.</p>
                )}
              </article>
            ))}
          </section>

          <section className="dashboard-section">
            <h2>Milestones</h2>
            {project.milestones.map((milestone) => (
              <article className="dashboard-item" key={milestone.id}>
                <h3>{milestone.title}</h3>
                <dl>
                  <div>
                    <dt>ID</dt>
                    <dd>{milestone.id}</dd>
                  </div>
                  <div>
                    <dt>Step ID</dt>
                    <dd>{milestone.step_id ?? "Not set"}</dd>
                  </div>
                  <div>
                    <dt>Achieved at</dt>
                    <dd>{milestone.achieved_at ?? "Not achieved"}</dd>
                  </div>
                </dl>
              </article>
            ))}
          </section>
        </div>
      </section>
    </main>
  )
}
