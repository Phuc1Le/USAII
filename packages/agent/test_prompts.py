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
    StepContext,
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
            category="productivity",
            idea="An app for tracking habits",
            previous_score=0.45,
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
            category="productivity",
            description="Build a productivity app",
            idea="An app for tracking habits",
            goal="MVP",
            complete_in=14,
        )
    )
    assert plan_prompt.strip()
    assert "steps" in plan_prompt
    assert "milestones" in plan_prompt
    # the category must reach the prompt — a generic plan is what happens when it doesn't
    assert "workflow mapping" in plan_prompt, "category-specific step guidance is missing"
    assert '"category": "productivity"' in plan_prompt

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
            project_id="1",
            scope_type="project",
            scope_step_title=None,
            project_context=ProjectContext(
                idea="An app for tracking habits",
                goal="MVP",
                steps=[
                    StepContext(
                        title="Plan",
                        description="Decide what to build",
                        status="done",
                        intended_start="2026-08-01",
                        intended_end="2026-08-03",
                    ),
                    StepContext(
                        title="Build",
                        description="Implement the core flow",
                        status="todo",
                        intended_start="2026-08-04",
                        intended_end="2026-08-14",
                    ),
                ],
            ),
            history=[
                ChatMessage(role="user", content="Hi"),
                ChatMessage(role="assistant", content="Hello"),
            ],
            new_message="What should I do next?",
        )
    )
    # build_chat_prompt is the one builder that does not return a flat string: the
    # fixed rules and project context go to system_instruction, and each real message
    # becomes its own role-tagged turn in contents
    assert chat_prompt.system_instruction.strip()
    assert "project context" in chat_prompt.system_instruction.lower()
    # history (2) + the new message
    assert len(chat_prompt.contents) == 3
    # "assistant" is mapped to Gemini's own "model" role at this boundary only
    assert [c.role for c in chat_prompt.contents] == ["user", "model", "user"]
    assert chat_prompt.contents[-1].parts[0].text == "What should I do next?"
