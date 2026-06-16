## 4. Domain model (shared vocabulary — contract-critical)

Everyone, every layer, uses these exact words.

| Concept | Definition |
|---|---|
| **Project** | One idea being taken to its goal. Has `category`, `description`, `idea`, `goal`, `status`, and one `plan`. |
| **Plan** | The steps + milestones + timeline for a project. `[DEMO]` one plan per project; regenerating replaces it. |
| **Step** | A major phase (e.g., "Build the API server"). Has `order`, optional dependencies, an intended date range, a status, and tasks. |
| **Task** | A concrete checkbox-level to-do inside a step. |
| **Milestone** | A checkpoint marker tied to completing a step (drives the celebration moment). |
| **Chat session** | A conversation scoped to a focus target (one step, or the whole project). |
| **Focus / Scope** | What the agent is grounded in: a single step, or the whole project. |
| **Project memory** | `[DEMO]` the project's plan + recorded decisions as plain text, passed into the agent prompt. (`[POST-DEMO]`: structured + embeddings.) |