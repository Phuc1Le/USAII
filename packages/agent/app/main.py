# packages/agent/app/main.py

from fastapi import FastAPI
from app.schemas import (
    ClarityRequest, ClarityResponse,
    ClarityAnswersRequest,
    GoalsRequest, GoalsResponse,
    PlanRequest, PlanResponse,
    ChatRequest
)

app = FastAPI(title="Zero to One Agent API", version="0.1.0")

@app.post("/agent/clarity", response_model=ClarityResponse)
def assess_clarity(body: ClarityRequest):
    pass

@app.post("/agent/clarity/answers", response_model=ClarityResponse)
def reassess_clarity(body: ClarityAnswersRequest):
    pass

@app.post("/agent/goals", response_model=GoalsResponse)
def suggest_goals(body: GoalsRequest):
    pass

@app.post("/agent/plan", response_model=PlanResponse)
def generate_plan(body: PlanRequest):
    pass

@app.post("/agent/chat")
def chat(body: ChatRequest):
    pass   # SSE stream — no response_model
