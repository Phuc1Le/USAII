import json

from fastapi import FastAPI
from fastapi.responses import StreamingResponse

from app.config import CLARITY_THRESHOLD
from app.llm import json_call, stream_text
from app.prompts import (
    build_chat_prompt,
    build_clarity_answers_prompt,
    build_clarity_prompt,
    build_goals_prompt,
    build_plan_prompt,
    build_tasks_prompt,
)
from app.schemas import (
    ChatRequest,
    ClarityAnswersRequest,
    ClarityRequest,
    ClarityResponse,
    ClarifyingQuestion,
    GenerateTasksRequest,
    GenerateTasksResponse,
    GoalsRequest,
    GoalsResponse,
    PlanRequest,
    PlanResponse,
)

app = FastAPI(title="Zero to One Agent API", version="0.1.0")


def _normalize_clarity(
    response: ClarityResponse,
    *,
    enriched_idea: str | None,
) -> ClarityResponse:
    clarity_score = min(1.0, max(0.0, response.clarity_score))
    needs = clarity_score < CLARITY_THRESHOLD
    questions = response.clarifying_questions[:3]
    # If the score is low but the model returned no questions, add a fallback
    if needs and not questions:
        questions = [ClarifyingQuestion(question="Could you describe your target users and the core problem you're solving?")]
    return response.model_copy(
        update={
            "clarity_score": clarity_score,
            "needs_clarification": needs,
            "clarifying_questions": questions,
            "enriched_idea": enriched_idea,
        }
    )


@app.post("/agent/clarity", response_model=ClarityResponse)
def assess_clarity(body: ClarityRequest):
    response = json_call(
        build_clarity_prompt(body),
        ClarityResponse,
    )
    return _normalize_clarity(response, enriched_idea=None)

@app.post("/agent/clarity/answers", response_model=ClarityResponse)
def reassess_clarity(body: ClarityAnswersRequest):
    qa_lines = "\n".join(f"{pair.question} {pair.answer}" for pair in body.answers)
    enriched_idea = f"{body.idea}\n{qa_lines}"
    response = json_call(
        build_clarity_answers_prompt(body, enriched_idea),
        ClarityResponse,
    )
    return _normalize_clarity(response, enriched_idea=enriched_idea)

@app.post("/agent/goals", response_model=GoalsResponse)
def suggest_goals(body: GoalsRequest):
    return json_call(build_goals_prompt(body), GoalsResponse)

@app.post("/agent/plan", response_model=PlanResponse)
def generate_plan(body: PlanRequest):
    return json_call(build_plan_prompt(body), PlanResponse)


@app.post("/agent/tasks", response_model=GenerateTasksResponse)
def generate_tasks(body: GenerateTasksRequest):
    return json_call(build_tasks_prompt(body), GenerateTasksResponse)

@app.post("/agent/chat")
def chat(body: ChatRequest):
    def event_generator():
        for chunk in stream_text(build_chat_prompt(body)):
            payload = json.dumps({"role": "assistant", "content": chunk})
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
