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
        "idea": idea["idea"]
    })
    data = res.json()
    print(json.dumps(data, indent=2))

    assert "goals" in data,        "missing goals"
    assert len(data["goals"]) >= 3, "expected at least 3 goals"
    for g in data["goals"]:
        assert "title" in g,       "goal missing title"
        assert "scope" in g,       "goal missing scope"
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

if __name__ == "__main__":
    fixture = sys.argv[1] if len(sys.argv) > 1 else "idea_clear.json"
    test_clarity(fixture)
    test_goals(fixture)
    test_plan(fixture)
    print("\n✓ all tools passed")