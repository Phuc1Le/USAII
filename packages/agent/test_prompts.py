from app.prompts import (
    build_chat_prompt,
    build_clarity_answers_prompt,
    build_clarity_prompt,
    build_goals_prompt,
    build_plan_prompt,
    build_tasks_prompt,
)
from app.schemas import (
    ChatMessage,
    ChatRequest,
    ClarityAnswersRequest,
    ClarityRequest,
    GenerateTasksRequest,
    GoalsRequest,
    PlanRequest,
    ProjectContext,
    QAPair,
)


def test_all_prompt_builders_return_non_empty_strings():
    clarity_prompt = build_clarity_prompt(
        ClarityRequest(
            category="app",
            description="Build a productivity app",
            idea="An app for tracking habits",
        )
    )
    assert clarity_prompt.strip()
    assert "clarity_score" in clarity_prompt

    answers_prompt = build_clarity_answers_prompt(
        ClarityAnswersRequest(
            idea="An app for tracking habits",
            answers=[
                QAPair(question="Who is it for?", answer="students"),
            ],
        ),
        enriched_idea="An app for tracking habits for students",
    )
    assert answers_prompt.strip()
    assert "enriched_idea" in answers_prompt

    goals_prompt = build_goals_prompt(
        GoalsRequest(
            category="app",
            description="Build a productivity app",
            idea="An app for tracking habits",
        )
    )
    assert goals_prompt.strip()
    assert "goals" in goals_prompt

    plan_prompt = build_plan_prompt(
        PlanRequest(
            category="app",
            description="Build a productivity app",
            idea="An app for tracking habits",
            goal="MVP",
        )
    )
    assert plan_prompt.strip()
    assert "steps" in plan_prompt
    assert "milestones" in plan_prompt

    tasks_prompt = build_tasks_prompt(
        GenerateTasksRequest(
            step_title="Set up backend",
            step_description="Create the API",
            project_idea="An app for tracking habits",
        )
    )
    assert tasks_prompt.strip()
    assert "tasks" in tasks_prompt

    chat_prompt = build_chat_prompt(
        ChatRequest(
            session_id="session-1",
            scope_type="project",
            scope_step_title=None,
            project_context=ProjectContext(
                idea="An app for tracking habits",
                goal="MVP",
                steps=["Plan", "Build"],
                decisions=["Use FastAPI"],
            ),
            history=[
                ChatMessage(role="user", content="Hi"),
                ChatMessage(role="assistant", content="Hello"),
            ],
            new_message="What should I do next?",
        )
    )
    assert chat_prompt.strip()
    assert "project context" in chat_prompt.lower()
