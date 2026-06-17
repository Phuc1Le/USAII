// src/features/project/ProjectPage.tsx  ← move the JSX here later

import { useProject } from "../../api/hook"

export default function ProjectPage({ projectId }: { projectId: string }) {
  const { data: project, isLoading, isError } = useProject(projectId)

  if (isLoading) return <div>Loading...</div>
  if (isError)   return <div>Error — is the backend running on :8000?</div>
  if (!project)  return <div>No project found</div>

  return (
    <div style={{ padding: "2rem", fontFamily: "sans-serif" }}>
      <h1>{project.title}</h1>
      <p><strong>Idea:</strong> {project.idea}</p>
      <p><strong>Goal:</strong> {project.goal}</p>
      <h2>Steps</h2>
      <ul>
        {project.steps.map(step => (
          <li key={step.id}>
            <strong>{step.title}</strong> — {step.status}
          </li>
        ))}
      </ul>
    </div>
  )
}