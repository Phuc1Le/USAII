// src/api/types.ts  ← your generated file, don't touch this

// src/api/index.ts  ← create this file manually, import from here everywhere
import type { components } from "./types"

export type Project  = components["schemas"]["Project"]
export type Step     = components["schemas"]["Step"]
export type Task     = components["schemas"]["Task"]
export type Milestone = components["schemas"]["Milestone"]
export type ChatSession = components["schemas"]["ChatSession"]
export type ChatMessage = components["schemas"]["ChatMessage"]
export type OpenSessionRequest = components["schemas"]["OpenSessionRequest"]
export type SendMessageRequest = components["schemas"]["SendMessageRequest"]
export type ClarityAnswersRequest = components["schemas"]["ClarityAnswersRequest"]
export type ClarityResult = components["schemas"]["ClarityResult"]
export type CreateProjectRequest = components["schemas"]["CreateProjectRequest"]
export type GoalsRequest = components["schemas"]["GoalsRequest"]
export type IntakeRequest = components["schemas"]["IntakeRequest"]
export type Goal = components["schemas"]["Goal"]
export type GoalsResponse = components["schemas"]["GoalsResponse"]
