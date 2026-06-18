from app.schemas import (
    ChatRequest,
    ClarityAnswersRequest,
    ClarityRequest,
    GenerateTasksRequest,
    GoalsRequest,
    PlanRequest,
)


def build_clarity_prompt(body: ClarityRequest) -> str:
    raise NotImplementedError("build_clarity_prompt is intentionally empty for later build")


def build_clarity_answers_prompt(
    body: ClarityAnswersRequest,
    enriched_idea: str,
) -> str:
    raise NotImplementedError(
        "build_clarity_answers_prompt is intentionally empty for later build"
    )


def build_goals_prompt(body: GoalsRequest) -> str:
    raise NotImplementedError("build_goals_prompt is intentionally empty for later build")


def build_plan_prompt(body: PlanRequest) -> str:
    raise NotImplementedError("build_plan_prompt is intentionally empty for later build")


def build_tasks_prompt(body: GenerateTasksRequest) -> str:
    raise NotImplementedError("build_tasks_prompt is intentionally empty for later build")


def build_chat_prompt(body: ChatRequest) -> str:
    raise NotImplementedError("build_chat_prompt is intentionally empty for later build")
