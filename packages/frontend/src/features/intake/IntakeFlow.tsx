import { useMemo, useState } from "react"
import type { FormEvent } from "react"
import { useMutation } from "@tanstack/react-query"
import { apiFetch } from "../../api/client"
import type {
  ClarityAnswersRequest,
  ClarityResult,
  CreateProjectRequest,
  Goal,
  GoalsRequest,
  GoalsResponse,
  IntakeRequest,
  Project,
} from "../../api"
import ChoicePanel from "./components/ChoicePanel"
import Starfield from "./components/Starfield"
import ThinkingPanel from "./components/ThinkingPanel"
import { categories, descriptionOptions, fallbackDescriptions } from "./intakeOptions"
import type { IntakeStep } from "./types"
import "./IntakeFlow.css"

type IntakeFlowProps = {
  onProjectCreated: (project: Project) => void
}

export default function IntakeFlow({ onProjectCreated }: IntakeFlowProps) {
  const [step, setStep] = useState<IntakeStep>("landing")
  const [category, setCategory] = useState("")
  const [description, setDescription] = useState("")
  const [idea, setIdea] = useState("")
  const [clarity, setClarity] = useState<ClarityResult | null>(null)
  const [goals, setGoals] = useState<GoalsResponse["goals"]>([])
  const [goalIdea, setGoalIdea] = useState("")
  const [selectedGoal, setSelectedGoal] = useState<Goal | null>(null)
  const [questionIndex, setQuestionIndex] = useState(0)
  const [answers, setAnswers] = useState<string[]>([])

  const createProjectMutation = useMutation({
    mutationFn: (payload: CreateProjectRequest) =>
      apiFetch<Project>("/projects", {
        method: "POST",
        body: JSON.stringify(payload),
    }),
    onMutate: () => setStep("projectThinking"),
    onSuccess: (result) => {
      onProjectCreated(result)
    },
    onError: () => setStep("goals"),
  })

  const goalsMutation = useMutation({
    mutationFn: (payload: GoalsRequest) =>
      apiFetch<GoalsResponse>("/projects/goals", {
        method: "POST",
        body: JSON.stringify(payload),
    }),
    onMutate: () => setStep("goalThinking"),
    onSuccess: (result) => {
      setGoals(result.goals)
      setSelectedGoal(result.goals[0] ?? null)
      setStep("goals")
    },
    onError: () => setStep("clarify"),
  })

  const answersMutation = useMutation({
    mutationFn: (payload: ClarityAnswersRequest) =>
      apiFetch<ClarityResult>("/projects/intake/answers", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onMutate: () => setStep("thinking"),
    onSuccess: (result) => {
      setClarity(result)
      if (result.needs_clarification && result.clarifying_questions.length > 0) {
        setQuestionIndex(0)
        setAnswers([])
        setStep("clarify")
        return
      }
      requestGoalSuggestions(result)
    },
    onError: () => setStep("clarify"),
  })

  const intakeMutation = useMutation({
    mutationFn: (payload: IntakeRequest) =>
      apiFetch<ClarityResult>("/projects/intake", {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    onMutate: () => setStep("thinking"),
    onSuccess: (result) => {
      setClarity(result)
      setQuestionIndex(0)
      setAnswers([])
      if (result.needs_clarification && result.clarifying_questions.length > 0) {
        setStep("clarify")
        return
      }
      requestGoalSuggestions(result)
    },
    onError: () => setStep("idea"),
  })

  const descriptions = useMemo(
    () => descriptionOptions[category] ?? fallbackDescriptions,
    [category]
  )

  const currentQuestion = clarity?.clarifying_questions[questionIndex]
  const progressLabel = step === "clarify" && clarity
    ? `Question ${questionIndex + 1} of ${clarity.clarifying_questions.length}`
    : undefined

  function submitCategory(value: string) {
    if (!value.trim()) return
    setCategory(value.trim())
    setDescription("")
    setStep("description")
  }

  function submitDescription(value: string) {
    if (!value.trim()) return
    setDescription(value.trim())
    setStep("idea")
  }

  function submitIdea(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!category.trim() || !description.trim() || !idea.trim()) return
    intakeMutation.mutate({
      category: category.trim(),
      description: description.trim(),
      idea: idea.trim(),
    })
  }

  function requestGoalSuggestions(result: ClarityResult | null = clarity) {
    const enrichedIdea = result?.enriched_idea?.trim()
    const ideaForGoals = enrichedIdea || idea.trim()
    setGoalIdea(ideaForGoals)
    goalsMutation.mutate({
      category: category.trim(),
      description: description.trim(),
      idea: ideaForGoals,
    })
  }

  function submitClarifyingAnswers() {
    if (!clarity) return
    answersMutation.mutate({
      idea: idea.trim(),
      answers: clarity.clarifying_questions.map((question, index) => ({
        question: question.question,
        answer: answers[index]?.trim() ?? "",
      })),
    })
  }

  function goToNextQuestion({ submitAtEnd = true }: { submitAtEnd?: boolean } = {}) {
    if (!clarity) return
    const isLast = questionIndex >= clarity.clarifying_questions.length - 1
    if (isLast) {
      if (submitAtEnd) {
        submitClarifyingAnswers()
      } else {
        requestGoalSuggestions()
      }
      return
    }
    setQuestionIndex((index) => index + 1)
  }

  function updateAnswer(value: string) {
    setAnswers((current) => {
      const next = [...current]
      next[questionIndex] = value
      return next
    })
  }

  function goBackFromGoals() {
    if (clarity?.clarifying_questions.length) {
      setQuestionIndex(clarity.clarifying_questions.length - 1)
      setStep("clarify")
      return
    }
    setStep("idea")
  }

  function createProject() {
    if (!selectedGoal) return
    createProjectMutation.mutate({
      category: category.trim(),
      description: description.trim(),
      idea: goalIdea || idea.trim(),
      goal: selectedGoal.title,
      complete_in: selectedGoal.complete_in,
    } as any)
  }

  const clarityPercent = Math.round((clarity?.clarity_score ?? 0) * 100)

  return (
    <main className="idea-shell">
      <Starfield />
      <section className="hero-stage">
        {step === "landing" && (
          <div className="landing-copy">
            <h1>Welcome to Stella</h1>
            <p>Let's get started</p>
            <button className="primary-button" onClick={() => setStep("category")}>
              Dive in
            </button>
          </div>
        )}

        {step === "category" && (
          <ChoicePanel
            key="category"
            eyebrow="First shape"
            title="Choose your category"
            value={category}
            options={categories}
            placeholder="Type a category"
            submitLabel="Continue"
            onBack={() => setStep("landing")}
            onSubmit={submitCategory}
          />
        )}

        {step === "description" && (
          <ChoicePanel
            key="description"
            eyebrow={category}
            title="Choose a description"
            value={description}
            options={descriptions}
            placeholder="Type what you want to build"
            submitLabel="Continue"
            onBack={() => setStep("category")}
            onSubmit={submitDescription}
          />
        )}

        {step === "idea" && (
          <form className="form-panel idea-panel" onSubmit={submitIdea}>
            <div>
              <span className="eyebrow">{category} / {description}</span>
              <h1>Jot down your idea here ....</h1>
            </div>
            <textarea
              value={idea}
              onChange={(event) => setIdea(event.target.value)}
              placeholder="Write the raw version. Fuzzy is welcome."
              rows={7}
            />
            {intakeMutation.isError && (
              <p className="error-text">The backend did not answer. Check that it is running on port 8000.</p>
            )}
            <div className="panel-actions">
              <button type="button" className="secondary-button" onClick={() => setStep("description")}>
                Back
              </button>
              <button type="submit" className="primary-button" disabled={!idea.trim() || intakeMutation.isPending}>
                Submit idea
              </button>
            </div>
          </form>
        )}

        {step === "thinking" && <ThinkingPanel />}

        {step === "goalThinking" && (
          <ThinkingPanel
            eyebrow="Suggesting goals"
            title="Shaping the path..."
            message="Using your category, description, and enriched idea to suggest the next ambition level."
          />
        )}

        {step === "projectThinking" && (
          <ThinkingPanel
            eyebrow="Creating project"
            title="Building your plan..."
            message="Saving the project and asking the backend to generate steps, milestones, and timeline details."
          />
        )}

        {step === "clarify" && currentQuestion && (
          <form
            className="form-panel idea-panel question-panel"
            onSubmit={(event) => {
              event.preventDefault()
              goToNextQuestion()
            }}
          >
            <div className="question-copy">
              <span className="eyebrow">{progressLabel}</span>
              <h2 className="question-title">{currentQuestion.question}</h2>
            </div>
            <textarea
              value={answers[questionIndex] ?? ""}
              onChange={(event) => updateAnswer(event.target.value)}
              placeholder="Add a quick answer, or skip this question."
              rows={6}
            />
            <div className="panel-actions three-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => requestGoalSuggestions()}
                disabled={goalsMutation.isPending || answersMutation.isPending}
              >
                Skip assessment
              </button>
              <button
                type="button"
                className="secondary-button"
                onClick={() => goToNextQuestion({ submitAtEnd: false })}
                disabled={goalsMutation.isPending || answersMutation.isPending}
              >
                Skip question
              </button>
              <button type="submit" className="primary-button" disabled={goalsMutation.isPending || answersMutation.isPending}>
                Next
              </button>
            </div>
            {(answersMutation.isError || goalsMutation.isError) && (
              <p className="error-text">The backend did not answer. Check that it is running on port 8000.</p>
            )}
          </form>
        )}

        {step === "goals" && (
          <div className="form-panel result-panel goals-panel">
            <span className="eyebrow">Goal suggestions</span>
            <h1>Choose where this idea should land.</h1>
            <div className="goals-meta">
              <span className="clarity-badge">Clarity {clarityPercent}%</span>
              {goalIdea && (
                <details className="idea-details">
                  <summary>View enriched idea</summary>
                  <p className="idea-details-body">{goalIdea}</p>
                </details>
              )}
            </div>
            <div className="goal-list">
              {goals.map((goal) => (
                <button
                  type="button"
                  className={`goal-option ${selectedGoal?.title === goal.title ? "selected" : ""}`}
                  key={goal.title}
                  onClick={() => setSelectedGoal(goal)}
                >
                  <span>{goal.title}</span>
                  <small>{goal.description}</small>
                  <strong>{goal.complete_in} days</strong>
                </button>
              ))}
            </div>
            <div className="panel-actions">
              <button className="secondary-button" onClick={goBackFromGoals}>
                Back
              </button>
              <button
                className="primary-button"
                onClick={createProject}
                disabled={!selectedGoal || createProjectMutation.isPending}
              >
                Create project
              </button>
            </div>
            {createProjectMutation.isError && (
              <p className="error-text">The backend did not create the project. Check that it is running on port 8000.</p>
            )}
          </div>
        )}

      </section>
    </main>
  )
}
