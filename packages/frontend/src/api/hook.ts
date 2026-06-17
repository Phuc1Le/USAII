// src/api/hooks.ts
import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "./client"
import type { Project } from "./index"   // ← from the generated file

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => apiFetch<Project>(`/projects/${projectId}`),
  })
}