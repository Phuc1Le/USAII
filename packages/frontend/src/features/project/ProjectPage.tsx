// src/features/project/ProjectPage.tsx

import { useProject } from "../../api/hook"

export default function ProjectPage() {
  const { data: project, isLoading } = useProject("p1")  // hardcoded for now

  if (isLoading) return <div>Loading...</div>
  if (!project) return <div>No project found</div>

  return (
    <div>
      <h1>{project.title}</h1>
      <p>{project.idea}</p>
      <ul>
        {project.steps.map(step => (
          <li key={step.id}>{step.title}</li>
        ))}
      </ul>
    </div>
  )
}