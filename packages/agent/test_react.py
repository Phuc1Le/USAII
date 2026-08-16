# test_react.py
#
# Manual verification script, NOT pytest (same convention as test_tools.py) —
# it makes real Gemini calls (and possibly real SerpApi calls) to check the
# model's tool-selection judgment, which isn't something a mock can test.
# Run: python test_react.py

import asyncio

from app.react import build_agent, _to_pydantic_history
from app.schemas import ChatMessage

SYSTEM_INSTRUCTION = """
You are the Zero to One planning assistant.
Project context:
{
  "idea": "A mobile app that helps students find study groups",
  "goal": "Ship an MVP in 4 weeks",
  "steps": [
    {"title": "Set up auth", "status": "done"},
    {"title": "Build matching algorithm", "status": "in_progress"}
  ]
}
""".strip()

FABRICATED_HISTORY = [
    ChatMessage(role="user", content="My project uses FastAPI and React."),
    ChatMessage(role="assistant", content="Got it, noted that you're using FastAPI and React."),
]

CASES = [
    ("Find me a good library for real-time matching algorithms in Python.", "expect: tool call (clearly needs external info)"),
    ("What framework did I say my project uses?", "expect: no tool call (answerable from history)"),
    ("What's the status of the auth step?", "expect: no tool call (answerable from system_instruction context)"),
    ("What is 12 * 7?", "expect: no tool call (general knowledge, not search-shaped)"),
    ("What's the latest stable version of FastAPI?", "expect: uncertain — interesting case, model may or may not choose to search"),
]


async def run_case(question: str, note: str):
    agent = build_agent(SYSTEM_INSTRUCTION)
    result = await agent.run(question, message_history=_to_pydantic_history(FABRICATED_HISTORY))

    tool_called = any(
        type(part).__name__ == "ToolCallPart"
        for m in result.all_messages()
        for part in m.parts
    )

    print(f"Q: {question}")
    print(f"   {note}")
    print(f"   tool_called={tool_called}")
    print(f"   answer: {result.output[:200]}")
    print()


async def main():
    for question, note in CASES:
        await run_case(question, note)


if __name__ == "__main__":
    asyncio.run(main())
