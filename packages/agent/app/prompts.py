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

    category_map = {
        "technology": (
            "Category-specific lens for technology projects: prioritize feasibility, "
            "architecture choices, integrations, scalability, security, testing, "
            "deployment readiness, and maintainability."
        ),
        "social media": (
            "Category-specific lens for social media projects: prioritize audience fit, "
            "engagement loops, content strategy, community growth, moderation, retention, "
            "analytics, and virality potential."
        ),
        "business": (
            "Category-specific lens for business projects: prioritize market demand, "
            "value proposition, revenue model, customer segments, operations, compliance, "
            "competitive differentiation, and growth constraints."
        ),
        "education": (
            "Category-specific lens for education projects: prioritize learning outcomes, "
            "curriculum fit, accessibility, engagement, assessment methods, progression, "
            "user onboarding, and instructional clarity."
        ),
        "health": (
            "Category-specific lens for health projects: prioritize user safety, privacy, "
            "trust, evidence quality, accessibility, compliance, care workflow fit, "
            "data handling, and reliability."
        ),
        "finance": (
            "Category-specific lens for finance projects: prioritize trust, transparency, "
            "risk management, compliance, auditability, security, fraud prevention, "
            "user understanding, and regulatory constraints."
        ),
        "creative arts": (
            "Category-specific lens for creative arts projects: prioritize originality, "
            "creative process, audience resonance, iteration, production quality, "
            "brand voice, collaboration, and distribution strategy."
        ),
        "community": (
            "Category-specific lens for community projects: prioritize participation, "
            "belonging, moderation, trust, local relevance, inclusion, volunteer coordination, "
            "feedback loops, and sustainable engagement."
        ),
        "productivity": (
            "Category-specific lens for productivity projects: prioritize workflow efficiency, "
            "time savings, usability, habit formation, integration depth, friction reduction, "
            "reliability, and adoption."
        ),
        "sustainability": (
            "Category-specific lens for sustainability projects: prioritize environmental impact, "
            "resource efficiency, measurable outcomes, stakeholder alignment, lifecycle thinking, "
            "accessibility, and long-term resilience."
        ),
    }

    return category_map.get(
        normalized,
        (
            "Category-specific lens: adapt the analysis to the project's domain and prioritize "
            "the constraints, behaviors, and success signals that matter most for that audience."
        ),
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
        Focus on whether the goal, target users, value proposition, risks, delivery scope, and domain-specific constraints are specific enough to plan realistically.
        Tailor the review to the category: for technology, emphasize implementation complexity, integrations, and deployment; for social media, emphasize audience definition, engagement mechanics, moderation, and content workflow; for business, emphasize market demand, customer segment clarity, operations, and revenue logic; for education, emphasize learning outcomes, pedagogy, accessibility, and assessment; for health, emphasize safety, privacy, compliance, and caregiver or patient workflows; for finance, emphasize trust, transparency, risk, and regulation; for creative arts, emphasize audience resonance, production process, and distribution; for community, emphasize participation model, moderation, trust, and inclusion; for productivity, emphasize workflow friction and adoption; for sustainability, emphasize environmental impact, measurement, and resource trade-offs.
        If clarity_score is below 0.7, you MUST include 1 to 3 concise clarifying questions that remove the biggest uncertainties.
        If clarity_score is 0.7 or above, return an empty clarifying_questions array.
        The JSON must contain exactly:
        - clarity_score: float between 0.0 and 1.0
        - needs_clarification: boolean
        - clarifying_questions: array of short, useful questions (required and non-empty when clarity_score < 0.7)
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
        If clarity_score is still below 0.7, you MUST include 1 to 3 follow-up clarifying questions targeting the remaining gaps.
        If clarity_score is 0.7 or above, return an empty clarifying_questions array.
        The JSON must contain exactly:
        - clarity_score: float between 0.0 and 1.0
        - needs_clarification: boolean
        - clarifying_questions: array of short, high-value follow-up questions (required and non-empty when clarity_score < 0.7)
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
        Tailor the goals to the category: for technology, emphasize architecture validation, core feature delivery, reliability, and deployment readiness; for social media, emphasize audience growth, engagement quality, content pipeline setup, and community management; for business, emphasize customer traction, revenue logic, operations readiness, and market validation; for education, emphasize learning impact, curriculum fit, accessibility, and adoption; for health, emphasize safety, trust, compliance, and workflow usefulness; for finance, emphasize trust, risk control, compliance, and user confidence; for creative arts, emphasize audience resonance, production quality, and distribution; for community, emphasize participation, moderation, retention, and inclusion; for productivity, emphasize efficiency, adoption, and workflow fit; for sustainability, emphasize measurable environmental benefit, efficiency, and long-term resilience.
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
        The plan must be completed within the number of days given by the "complete_in" field in the input payload. All step dates must fit inside that window starting from today.
        Tailor the plan to the category: for technology, include architecture decisions, prototyping, testing, deployment, and iteration planning; for social media, include positioning, content planning, launch sequence, community engagement, and analytics review; for business, include market validation, ops setup, customer acquisition, and revenue model validation; for education, include curriculum design, learning flow, accessibility review, assessment setup, and rollout; for health, include safety review, privacy review, workflow validation, testing, and compliance checkpoints; for finance, include trust controls, regulatory checks, security review, financial logic validation, and auditability; for creative arts, include concept development, production planning, review cycles, and distribution; for community, include onboarding, moderation setup, feedback loops, and member retention plans; for productivity, include workflow mapping, usability testing, integration setup, and adoption tracking; for sustainability, include impact measurement, resource planning, stakeholder engagement, and long-term monitoring.
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
        Tailor the task focus to the category when relevant: for technology, emphasize technical setup, validation, integration, testing, or deployment work; for social media, emphasize content creation, campaign setup, analytics review, moderation, or community engagement work; for business, emphasize market research, operations setup, customer outreach, pricing logic, or compliance checks; for education, emphasize curriculum drafting, learner feedback, accessibility review, assessment design, or onboarding; for health, emphasize safety review, privacy controls, workflow validation, content accuracy, or compliance; for finance, emphasize calculation checks, risk controls, auditability, fraud prevention, and documentation; for creative arts, emphasize concept development, asset creation, review cycles, and distribution planning; for community, emphasize onboarding, engagement tactics, feedback handling, and moderation; for productivity, emphasize workflow mapping, usability improvements, automation, and adoption support; for sustainability, emphasize impact measurement, resource planning, stakeholder coordination, and process improvement.
        The JSON must contain an array named tasks where each item has exactly:
        - title: short action-oriented label
        - detail: clear explanation of what to do and why it matters
        """,
        body.model_dump(mode="json"),
    )


def _build_plain_prompt(task: str, payload: dict) -> str:
    return dedent(
        f"""
        You are the Zero to One planning assistant.
        {task}

        Rules:
        - Respond in clear, concise plain text. Use markdown for structure (bold, lists) when helpful.
        - Do not wrap your response in JSON or code fences.
        - Do not invent facts that are not supported by the input payload.
        - If a value is uncertain, ask a short clarifying question rather than guessing.

        Input payload:
        {json.dumps(payload, indent=2, sort_keys=True)}
        """
    ).strip()


def build_chat_prompt(body: ChatRequest) -> str:
    return _build_plain_prompt(
        """
        You are helping the user continue work on their project.
        Use the supplied project context, current step, chat history, and the latest user message to respond helpfully.
        Keep the answer practical, concise, and grounded in the plan.
        Prefer specific next actions over generic advice.
        Tailor recommendations to the project domain when possible: for technology, focus on architecture, implementation, validation, and rollout; for social media, focus on audience growth, content rhythm, engagement, and community management; for business, focus on market fit, customer acquisition, revenue logic, and operations; for education, focus on instruction quality, accessibility, progression, and assessment; for health, focus on safety, privacy, trust, and workflow fit; for finance, focus on trust, compliance, risk control, and transparency; for creative arts, focus on ideation, iteration, production quality, and distribution; for community, focus on participation, moderation, trust, and retention; for productivity, focus on efficiency, friction reduction, workflow design, and adoption; for sustainability, focus on measurable impact, resource efficiency, and long-term resilience.
        If the user is asking something that cannot be answered safely from the context, ask a short clarifying question instead of guessing.
        Do not invent facts that are not present in the context.
        """,
        body.model_dump(mode="json"),
    )
