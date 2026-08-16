# test_react_step4.py
#
# Manual verification script, NOT pytest (same convention as test_tools.py /
# test_react.py) — makes real Gemini calls against the full Step 4 agent
# (all four tools, RunContext-scoped deps, tool_calls_limit cap) to check
# tool selection and cap behavior, which isn't something a mock can test.
#
# Requires the backend running locally against sqlite with a seeded project:
#   cd packages/backend
#   rm -f app.db && DATABASE_URL="sqlite:///./app.db" .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000
# and BACKEND_URL=http://localhost:8000 set in root .env.
#
# Run: python test_react_step4.py

import asyncio

from app.react import build_agent, run_chat, ChatDeps, _to_pydantic_history
from app.schemas import ChatMessage

SYSTEM_INSTRUCTION = """
You are the Zero to One planning assistant.
Project context:
{
  "idea": "A mobile app that helps students find study groups",
  "goal": "Ship an MVP in 4 weeks",
  "steps": [{"title": "Build matching algorithm", "status": "in_progress"}]
}
Use the supplied project context and available tools to answer helpfully.
""".strip()

DEPS = ChatDeps(project_id="1")

CASES = [
    ("What are the milestones for this project?", "expect: retrieve_milestones called"),
    ("Give me the details and tasks for step 1.", "expect: retrieve_step called with step_id='1'"),
    ("Have we made any past decisions about which database to use?", "expect: query_decisions called (empty result expected on sqlite)"),
    ("What is 9 * 6?", "expect: no tool call"),
    (
        "Call retrieve_milestones, then retrieve_step for step 1, then query_decisions for 'database', "
        "then retrieve_milestones again, then retrieve_step for step 1 again, then query_decisions again, "
        "then retrieve_milestones a third time.",
        "expect: cap hit (tool_calls_limit=6), fallback message returned",
    ),
]


async def run_case(agent, question: str, note: str):
    print(f"Q: {question}")
    print(f"   {note}")
    output = await run_chat(
        agent,
        question,
        deps=DEPS,
        message_history=_to_pydantic_history([]),
    )
    print(f"   answer: {output[:250]}")
    print()


async def main():
    for question, note in CASES:
        agent = build_agent(SYSTEM_INSTRUCTION)
        await run_case(agent, question, note)
        await asyncio.sleep(13)  # stay under free-tier 5 req/min


if __name__ == "__main__":
    asyncio.run(main())
