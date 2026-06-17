// src/api/types.ts  ← your generated file, don't touch this

// src/api/index.ts  ← create this file manually, import from here everywhere
import type { components } from "./types"

export type Project  = components["schemas"]["Project"]
export type Step     = components["schemas"]["Step"]
export type Task     = components["schemas"]["Task"]
export type Milestone = components["schemas"]["Milestone"]
export type ChatSession = components["schemas"]["ChatSession"]
export type ChatMessage = components["schemas"]["ChatMessage"]
export type ClarityResult = components["schemas"]["ClarityResult"]
export type Goal = components["schemas"]["Goal"]
export type GoalsResponse = components["schemas"]["GoalsResponse"]