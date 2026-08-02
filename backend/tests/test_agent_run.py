"""Ava Agent planning (D-054 F2): plan parsing and route registration."""

from app.api.assistant import router
from app.services.agent_run import AGENT_TOOLS, MAX_STEPS, _parse_plan


def test_parse_plan_filters_unknown_tools():
    text = """Here is the plan:
    [{"tool": "research", "arg": "afati i ankesës", "label": "Hulumto afatin"},
     {"tool": "rm -rf", "arg": "x", "label": "bad"},
     {"tool": "draft_document", "arg": "ankesë", "label": "Drafto ankesën"}]"""
    steps = _parse_plan(text)
    assert [s["tool"] for s in steps] == ["research", "draft_document"]


def test_parse_plan_caps_steps():
    items = ",".join(
        '{"tool": "research", "arg": "q", "label": "l"}' for _ in range(10)
    )
    steps = _parse_plan(f"[{items}]")
    assert len(steps) == MAX_STEPS


def test_parse_plan_garbage_returns_empty():
    assert _parse_plan("nuk ka plan këtu") == []
    assert _parse_plan("[not json]") == []


def test_tool_catalog_has_write_gates():
    # The two write-intent tools must exist — the UI relies on their
    # approval events (D-044/D-053 human-in-the-loop)
    assert "extract_deadlines" in AGENT_TOOLS
    assert "draft_document" in AGENT_TOOLS


def test_agent_run_route_registered():
    assert "/assistant/agent-run" in {r.path for r in router.routes}
