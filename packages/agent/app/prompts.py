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
def _build_prompt(task: str, payload: dict) -> str:
    return dedent(
        f"""
        You are the Zero to One planning assistant.
        {task}

        Return valid JSON only.

        Input payload:
        {json.dumps(payload, indent=2, sort_keys=True)}
        """
    ).strip()


def build_clarity_prompt(body: ClarityRequest) -> str:
    return _build_prompt(
        """
        Evaluate how clear the project idea is for execution.
        Score clarity from 0.0 to 1.0.
        If the idea is vague, ask up to 3 concise clarifying questions.
        If the idea is already clear, ask for none.
        The JSON must contain:
        - clarity_score
        - needs_clarification
        - clarifying_questions
        """,
        body.model_dump(mode="json"),
    )


def build_clarity_answers_prompt(
    body: ClarityAnswersRequest,
    enriched_idea: str,
) -> str:
    return _build_prompt(
        """
        Re-score the idea after the user answered the clarifying questions.
        Use the original idea plus the answers to produce a better clarity assessment.
        The JSON must contain:
        - clarity_score
        - needs_clarification
        - clarifying_questions
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
        Each goal should be scoped by ambition (small, medium, large).
        The JSON must contain an array named goals where each item has:
        - title
        - description
        - complete_in
        """,
        body.model_dump(mode="json"),
    )


def build_plan_prompt(body: PlanRequest) -> str:
    return _build_prompt(
        """
        Turn the idea and selected goal into a project plan.
        Generate a realistic sequence of steps and milestones.
        Use dates in YYYY-MM-DD format.
        The JSON must contain:
        - steps: each step has title, description, order_index, intended_start, intended_end, depends_on
        - milestones: each milestone has title and after_step_index
        """,
        body.model_dump(mode="json"),
    )


def build_tasks_prompt(body: GenerateTasksRequest) -> str:
    return _build_prompt(
        """
        Break the given step into a practical task list.
        Generate 3 to 7 actionable tasks.
        The JSON must contain an array named tasks where each item has:
        - title
        - detail
        """,
        body.model_dump(mode="json"),
    )


def build_chat_prompt(body: ChatRequest) -> str:
    return _build_prompt(
        """
        You are helping the user continue work on their project.
        Use the supplied project context, current step, and chat history to answer the latest message.
        Keep the answer practical, concise, and grounded in the plan.
        Do not invent facts that are not present in the context.
        """,
        body.model_dump(mode="json"),
    )
