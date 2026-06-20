import json
from textwrap import dedent

from app.schemas import (
    ChatRequest,
    ClarityAnswersRequest,
    ClarityRequest,
    GenerateTasksRequest,
    GoalsRequest,
    PlanRequest,
)


def _normalize_category(category: str | None) -> str:
    return (category or "").strip().lower()


def _category_guidance(category: str | None) -> str:
    normalized = _normalize_category(category)
    if normalized == "technology":
        return (
            "Category-specific lens for technology projects: prioritize feasibility, "
            "architecture choices, integrations, scalability, security, testing, "
            "deployment readiness, and maintainability."
        )
    if normalized == "social media":
        return (
            "Category-specific lens for social media projects: prioritize audience fit, "
            "engagement loops, content strategy, community growth, moderation, retention, "
            "analytics, and virality potential."
        )
    return (
        "Category-specific lens: adapt the analysis to the project's domain and prioritize "
        "the constraints, behaviors, and success signals that matter most for that audience."
    )


def _build_prompt(
    task: str,
    payload: dict,
    *,
    category: str | None = None,
) -> str:
    return dedent(
        f"""
        You are the Zero to One planning assistant.
        {task}

        {_category_guidance(category)}

        Rules:
        - Return valid JSON only, with no markdown, no commentary, and no extra text.
        - Use exactly the keys requested in the schema.
        - Do not invent facts that are not supported by the input payload.
        - If a value is uncertain, choose the safest reasonable default rather than guessing beyond the payload.

        Input payload:
        {json.dumps(payload, indent=2, sort_keys=True)}
        """
    ).strip()


def build_clarity_prompt(body: ClarityRequest) -> str:
    return _build_prompt(
        """
        Evaluate how clear the project idea is for execution.
        Score clarity from 0.0 to 1.0 using the idea, category, and description.
        Focus on whether the goal, target users, value proposition, risks, and delivery scope are specific enough to plan realistically.
        For technology ideas, pay extra attention to technical complexity, integrations, and deployment constraints.
        For social media ideas, pay extra attention to audience definition, engagement mechanics, moderation needs, and content workflow.
        If the idea is vague, ask up to 3 concise clarifying questions that remove the biggest uncertainties.
        If the idea is already clear, ask for none.
        The JSON must contain exactly:
        - clarity_score: float between 0.0 and 1.0
        - needs_clarification: boolean
        - clarifying_questions: array of short, useful questions
        """,
        body.model_dump(mode="json"),
        category=body.category,
    )


def build_clarity_answers_prompt(
    body: ClarityAnswersRequest,
    enriched_idea: str,
) -> str:
    return _build_prompt(
        """
        Re-score the idea after the user answered the clarifying questions.
        Use the original idea, the answers, and the enriched idea to assess whether the project is now specific enough to execute.
        Update the clarity score and decide whether any remaining ambiguity still blocks planning.
        If the answers remove the uncertainty, return an empty clarifying_questions array.
        The JSON must contain exactly:
        - clarity_score: float between 0.0 and 1.0
        - needs_clarification: boolean
        - clarifying_questions: array of short, high-value follow-up questions only if needed
        """,
        {
            "idea": body.idea,
            "answers": [pair.model_dump(mode="json") for pair in body.answers],
            "enriched_idea": enriched_idea,
        },
    )


def build_goals_prompt(body: GoalsRequest) -> str:
    return _build_prompt(
        """
        Suggest 3 to 5 realistic goals for this project.
        Each goal should be scoped by a practical delivery timeline, not by vague ambition.
        Use time estimates that are easy to understand and executable, such as a few days, 1 week, 2 weeks, or 1 month.
        For technology projects, emphasize goals around architecture validation, core feature delivery, reliability, and deployment readiness.
        For social media projects, emphasize goals around audience growth, engagement quality, content pipeline setup, and community management.
        For each goal:
        - title should be short and outcome-focused
        - description should explain the result, constraints, and what success looks like
        - complete_in should be a realistic numeric estimate in days, using the closest day-based value that matches the timeline
        The JSON must contain an array named goals where each item has exactly:
        - title
        - description
        - complete_in
        """,
        body.model_dump(mode="json"),
        category=body.category,
    )


def build_plan_prompt(body: PlanRequest) -> str:
    return _build_prompt(
        """
        Turn the idea and selected goal into a realistic project plan.
        Generate a practical sequence of steps and milestones that progress from discovery to delivery.
        Make the steps logically ordered, time-boxed, and dependency-aware.
        For technology projects, include architecture decisions, prototyping, testing, deployment, and iteration planning.
        For social media projects, include positioning, content planning, launch sequence, community engagement, and analytics review.
        Use dates in YYYY-MM-DD format.
        Keep the plan specific enough to be actionable but concise enough to be read quickly.
        The JSON must contain exactly:
        - steps: an array where each item has title, description, order_index, intended_start, intended_end, depends_on
        - milestones: an array where each item has title and after_step_index
        """,
        body.model_dump(mode="json"),
        category=body.category,
    )


def build_tasks_prompt(body: GenerateTasksRequest) -> str:
    return _build_prompt(
        """
        Break the given step into a practical, implementation-ready task list.
        Generate 3 to 7 actionable tasks that are specific, measurable, and small enough to complete without ambiguity.
        Each task should describe a concrete action, not a broad theme.
        If the step relates to a technology product, emphasize technical setup, validation, integration, testing, or deployment work.
        If the step relates to social media, emphasize content creation, campaign setup, analytics review, moderation, or community engagement work.
        The JSON must contain an array named tasks where each item has exactly:
        - title: short action-oriented label
        - detail: clear explanation of what to do and why it matters
        """,
        body.model_dump(mode="json"),
    )


def build_chat_prompt(body: ChatRequest) -> str:
    return _build_prompt(
        """
        You are helping the user continue work on their project.
        Use the supplied project context, current step, chat history, and the latest user message to respond helpfully.
        Keep the answer practical, concise, and grounded in the plan.
        Prefer specific next actions over generic advice.
        If the project appears to be a technology idea, frame suggestions around architecture, implementation, validation, and rollout.
        If the project appears to be a social media idea, frame suggestions around audience growth, content rhythm, engagement, and community management.
        If the user is asking something that cannot be answered safely from the context, ask a short clarifying question instead of guessing.
        Do not invent facts that are not present in the context.
        """,
        body.model_dump(mode="json"),
    )
