# packages/agent/test_tools.py

import json
import httpx       # pip install httpx
import sys

BASE = "http://localhost:8001"

def load(fixture_name):
    with open(f"fixtures/{fixture_name}") as f:
        return json.load(f)

def test_clarity(fixture_name):
    print(f"\n── assess_clarity ({fixture_name}) ──")
    idea = load(fixture_name)
    res = httpx.post(f"{BASE}/agent/clarity", json=idea)
    data = res.json()
    print(json.dumps(data, indent=2))

    # check shape
    assert "clarity_score" in data,        "missing clarity_score"
    assert "needs_clarification" in data,  "missing needs_clarification"
    assert "clarifying_questions" in data, "missing clarifying_questions"
    assert 0 <= data["clarity_score"] <= 1, "clarity_score out of range"
    print("✓ shape OK")

def test_goals(fixture_name):
    print(f"\n── suggest_goals ({fixture_name}) ──")
    idea = load(fixture_name)
    res = httpx.post(f"{BASE}/agent/goals", json={
        "category": idea["category"],
        "description": idea["description"],
        "idea": idea["idea"]
    })
    data = res.json()
    print(json.dumps(data, indent=2))

    assert "goals" in data,        "missing goals"
    assert len(data["goals"]) >= 3, "expected at least 3 goals"
    for g in data["goals"]:
        assert "title" in g,          "goal missing title"
        assert "description" in g,    "goal missing description"
        assert "complete_in" in g,    "goal missing complete_in"
        assert isinstance(g["complete_in"], int), "complete_in should be int"
    print("✓ shape OK")

def test_plan(fixture_name):
    print(f"\n── generate_plan ({fixture_name}) ──")
    idea = load(fixture_name)
    res = httpx.post(f"{BASE}/agent/plan", json={
        "category": idea["category"],
        "description": idea["description"],
        "idea": idea["idea"],
        "goal": "MVP"
    })
    data = res.json()
    print(json.dumps(data, indent=2))

    assert "steps" in data,      "missing steps"
    assert "milestones" in data, "missing milestones"
    assert len(data["steps"]) >= 3, "expected at least 3 steps"
    for s in data["steps"]:
        assert "title" in s,        "step missing title"
        assert "order_index" in s,  "step missing order_index"
        assert "intended_start" in s
        assert "intended_end" in s
    print("✓ shape OK")

def test_clarity_answers(fixture_name):
    print(f"\n── reassess_clarity ({fixture_name}) ──")
    idea = load(fixture_name)
    res = httpx.post(f"{BASE}/agent/clarity/answers", json={
        "idea": idea["idea"],
        "answers": [
            {
                "question": "Who is the primary user?",
                "answer": "Independent builders trying to ship a focused first version."
            },
            {
                "question": "What is the definition of done?",
                "answer": "A working demo with the core workflow and clear next steps."
            }
        ]
    })
    data = res.json()
    print(json.dumps(data, indent=2))

    assert "clarity_score" in data,        "missing clarity_score"
    assert "needs_clarification" in data,  "missing needs_clarification"
    assert "clarifying_questions" in data, "missing clarifying_questions"
    assert "enriched_idea" in data,        "missing enriched_idea"
    assert data["enriched_idea"],          "expected enriched_idea"
    assert 0 <= data["clarity_score"] <= 1, "clarity_score out of range"
    print("✓ shape OK")

def test_tasks(fixture_name):
    print(f"\n── generate_tasks ({fixture_name}) ──")
    idea = load(fixture_name)
    res = httpx.post(f"{BASE}/agent/tasks", json={
        "step_title": "Build the MVP workflow",
        "step_description": "Implement the smallest useful end-to-end flow.",
        "project_idea": idea["idea"]
    })
    data = res.json()
    print(json.dumps(data, indent=2))

    assert "tasks" in data,        "missing tasks"
    assert len(data["tasks"]) >= 3, "expected at least 3 tasks"
    for task in data["tasks"]:
        assert "title" in task,  "task missing title"
        assert "detail" in task, "task missing detail"
    print("✓ shape OK")

def test_chat(fixture_name):
    print(f"\n── chat ({fixture_name}) ──")
    idea = load(fixture_name)
    payload = {
        "session_id": "test-session",
        "scope_type": "project",
        "scope_step_title": None,
        "project_context": {
            "idea": idea["idea"],
            "goal": "MVP",
            "steps": ["Define requirements", "Build the MVP workflow"],
            "decisions": []
        },
        "history": [],
        "new_message": "What should I do next?"
    }

    saw_data = False
    with httpx.stream("POST", f"{BASE}/agent/chat", json=payload, timeout=60) as res:
        for line in res.iter_lines():
            if not line:
                continue
            print(line)
            assert line.startswith("data: "), "chat stream line should be SSE data"
            json.loads(line.removeprefix("data: "))
            saw_data = True
            break

    assert saw_data, "expected at least one SSE data line"
    print("✓ shape OK")

if __name__ == "__main__":
    fixture = sys.argv[1] if len(sys.argv) > 1 else "idea_clear.json"
    test_clarity(fixture)
    test_clarity_answers(fixture)
    test_goals(fixture)
    test_plan(fixture)
    test_tasks(fixture)
    test_chat(fixture)
    print("\n✓ all tools passed")