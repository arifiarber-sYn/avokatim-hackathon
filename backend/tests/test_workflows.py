"""Expert workflows (audit 2026-09-18, advancement #6): definitions are
jurisdiction data, prompts are well-formed, the route is registered."""

from app.api.matters import router
from app.seeds.workflow_defs import WORKFLOW_DEFS, get_workflow
from app.services.workflows import WORKFLOW_KINDS

# Placeholders the service can resolve (must stay in sync with ctx())
_KNOWN_NEEDS = {
    "matter_context", "documents", "deadline_rules", "upcoming", "language_hint",
}


def test_all_kinds_have_xk_definitions():
    for kind in WORKFLOW_KINDS:
        defn = get_workflow(kind, "XK")
        assert defn, kind
        assert defn["name"]
        assert len(defn["steps"]) >= 2


def test_unknown_jurisdiction_falls_back_to_xk():
    assert get_workflow("appeal", "DE") == get_workflow("appeal", "XK")
    assert get_workflow("nope", "XK") is None


def test_step_needs_are_resolvable_and_prompts_format():
    for kind, by_jur in WORKFLOW_DEFS.items():
        for jur, defn in by_jur.items():
            for step in defn["steps"]:
                unknown = set(step["needs"]) - _KNOWN_NEEDS
                assert not unknown, f"{kind}/{jur}/{step['id']}: {unknown}"
                fmt = {name: "X" for name in step["needs"]}
                fmt["jurisdiction"] = jur
                # raises KeyError if the template references a missing name
                rendered = step["prompt"].format(**fmt)
                assert len(rendered) > 50


def test_workflow_route_registered():
    assert "/matters/{matter_id}/workflows/{kind}" in {r.path for r in router.routes}
