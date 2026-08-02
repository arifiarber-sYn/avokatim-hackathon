"""Ava Agent (D-054 F2): goal-based multi-step execution — the lawyer
describes the outcome, Ava plans the steps and runs them one by one with
live progress. The Clio Vincent / Harvey pattern, with one hard rule kept
from D-044/D-053: no write ever happens here. Steps that would write
(deadlines, drafts) emit "approval" events; the client executes them through
the existing approval endpoints after the lawyer confirms.
"""
import json
import logging
import re
import uuid
from collections.abc import AsyncIterator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm import get_provider
from app.llm.base import ChatMessage
from app.models import Contact, Document, Matter, MatterParty
from app.services import assistant as assistant_svc
from app.services.conflicts import check_conflicts

logger = logging.getLogger(__name__)

MAX_STEPS = 5

# tool → short description shown to the planner LLM
AGENT_TOOLS: dict[str, str] = {
    "summarize_matter": "Përmbledh gjendjen e lëndës nga dosja (dokumente, afate, palë).",
    "research": "Hulumton një pyetje ligjore në korpus (ligje + praktikë gjyqësore) dhe kthen analizë me citime. arg = pyetja.",
    "extract_deadlines": "Lexon dokumentet e fundit të lëndës dhe propozon afate konkrete. Krijimi kërkon aprovimin e avokatit.",
    "draft_document": "Drafton një shkresë/parashtresë për lëndën. arg = çfarë të draftohet. Ruajtja kërkon aprovimin e avokatit.",
    "conflict_check": "Kontrollon konfliktet e interesit për palët e kësaj lënde në gjithë zyrën.",
    "hearing_prep": "Përgatitje e plotë për seancë: kronologji, argumente, dobësi, pyetje për dëshmitarë.",
}

PLAN_PROMPT = """Je Ava, asistentja ligjore. Avokati të jep një QËLLIM për një lëndë.
Zbërtheje në hapa konkretë duke përdorur VETËM veglat në katalog. Maksimumi {max_steps} hapa,
vetëm hapat që vërtet duhen për qëllimin (shpesh mjaftojnë 2-3).

KATALOGU I VEGLAVE:
{tools}

Kthe VETËM JSON të vlefshëm — një listë objektesh:
[{{"tool": "emri_i_veglës", "arg": "argumenti ose ''", "label": "përshkrim i shkurtër i hapit në gjuhën e qëllimit"}}]

QËLLIMI I AVOKATIT:
{goal}"""


def _parse_plan(text: str) -> list[dict]:
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return []
    try:
        parsed = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    steps = []
    for item in parsed:
        if not isinstance(item, dict) or item.get("tool") not in AGENT_TOOLS:
            continue
        steps.append(
            {
                "tool": item["tool"],
                "arg": str(item.get("arg") or ""),
                "label": str(item.get("label") or item["tool"])[:200],
            }
        )
    return steps[:MAX_STEPS]


async def _party_names(db: AsyncSession, matter: Matter) -> list[str]:
    names: list[str] = []
    if matter.client_id:
        client = await db.get(Contact, matter.client_id)
        if client:
            names.append(client.display_name)
    rows = (
        await db.execute(
            select(Contact.display_name)
            .join(MatterParty, MatterParty.contact_id == Contact.id)
            .where(MatterParty.matter_id == matter.id)
        )
    ).scalars().all()
    names.extend(rows)
    return list(dict.fromkeys(names))


async def _recent_doc_text(db: AsyncSession, matter_id: uuid.UUID) -> str:
    docs = (
        await db.execute(
            select(Document)
            .where(
                Document.matter_id == matter_id,
                Document.text_content.is_not(None),
                Document.is_latest.is_(True),
            )
            .order_by(Document.created_at.desc())
            .limit(3)
        )
    ).scalars().all()
    parts = [
        f"=== {d.filename} ===\n{(d.text_content or '')[:12000]}" for d in docs
    ]
    return "\n\n".join(parts)


async def agent_run_stream(
    db: AsyncSession,
    *,
    matter: Matter,
    goal: str,
    provider_name: str | None,
    language: str | None = None,
    region: str | None = None,
    style: str | None = None,
) -> AsyncIterator[dict]:
    """Yields: plan, step (running/done/failed), result, approval, done."""
    provider = get_provider(provider_name)

    # 1. Plan
    plan_msg = PLAN_PROMPT.format(
        max_steps=MAX_STEPS,
        tools="\n".join(f"- {k}: {v}" for k, v in AGENT_TOOLS.items()),
        goal=goal,
    )
    try:
        raw = await provider.chat([ChatMessage(role="user", content=plan_msg)])
        steps = _parse_plan(raw.content)
    except Exception as exc:
        logger.warning("Agent planning failed: %s", exc)
        steps = []
    if not steps:
        steps = [{"tool": "research", "arg": goal, "label": goal[:200]}]
    yield {"type": "plan", "steps": [{"tool": s["tool"], "label": s["label"]} for s in steps]}

    # 2. Execute sequentially
    for i, step in enumerate(steps):
        yield {"type": "step", "index": i, "status": "running"}
        try:
            async for event in _run_tool(
                db,
                matter=matter,
                tool=step["tool"],
                arg=step["arg"],
                goal=goal,
                provider_name=provider_name,
                language=language,
                region=region,
                style=style,
            ):
                event["index"] = i
                yield event
            yield {"type": "step", "index": i, "status": "done"}
        except Exception as exc:
            logger.warning("Agent step %s (%s) failed: %s", i, step["tool"], exc)
            yield {"type": "step", "index": i, "status": "failed", "detail": str(exc)[:200]}

    yield {"type": "done"}


async def _run_tool(
    db: AsyncSession,
    *,
    matter: Matter,
    tool: str,
    arg: str,
    goal: str,
    provider_name: str | None,
    language: str | None,
    region: str | None,
    style: str | None,
) -> AsyncIterator[dict]:
    if tool == "summarize_matter":
        answer, citations = await assistant_svc.ask_bora(
            db,
            question="Përmbledh gjendjen aktuale të kësaj lënde: faktet, ku ka mbetur procesi, "
            "afatet aktive, dhe 3 hapat e ardhshëm të rekomanduar.",
            matter_id=matter.id,
            jurisdiction_id=matter.jurisdiction_id,
            provider_name=provider_name,
            language=language,
            region=region,
            style=style,
        )
        yield {"type": "result", "content": answer, "citations": citations}

    elif tool == "research":
        answer, citations = await assistant_svc.ask_bora(
            db,
            question=arg or goal,
            matter_id=matter.id,
            jurisdiction_id=matter.jurisdiction_id,
            provider_name=provider_name,
            language=language,
            region=region,
            style=style,
        )
        yield {"type": "result", "content": answer, "citations": citations}

    elif tool == "hearing_prep":
        answer, citations = await assistant_svc.hearing_prep(
            db,
            matter_id=matter.id,
            jurisdiction_id=matter.jurisdiction_id,
            extra_instructions=arg or None,
            provider_name=provider_name,
            region=region,
        )
        yield {"type": "result", "content": answer, "citations": citations}

    elif tool == "conflict_check":
        names = await _party_names(db, matter)
        report = await check_conflicts(db, matter.tenant_id, names)
        lines = []
        for hit in report.get("hits", []):
            appearances = ", ".join(
                f"{a['matter']} ({a['role']}, {a['status']})" for a in hit["appears_in"]
            )
            lines.append(f"- {hit['contact_name']}: {appearances}")
        content = (
            "⚠ Konflikte të mundshme:\n" + "\n".join(lines)
            if report.get("has_conflicts")
            else f"✓ Asnjë konflikt interesi për palët: {', '.join(names) or '—'}."
        )
        yield {"type": "result", "content": content, "citations": []}

    elif tool == "extract_deadlines":
        text = await _recent_doc_text(db, matter.id)
        if not text:
            yield {"type": "result", "content": "S'ka dokumente me tekst në këtë lëndë.", "citations": []}
            return
        raw = await assistant_svc.extract_deadlines_from_text(text, provider_name)
        proposals = []
        for item in raw[:10]:
            if not isinstance(item, dict):
                continue
            proposals.append(
                {
                    "title": str(item.get("title") or "")[:200],
                    "kind": item.get("kind") or "deadline",
                    "due_date": item.get("date"),
                    "trigger_date": item.get("trigger_date"),
                    "legal_basis": item.get("legal_basis"),
                    "confidence": item.get("confidence") or "medium",
                }
            )
        yield {"type": "approval", "kind": "deadlines", "proposals": proposals}

    elif tool == "draft_document":
        answer, _citations = await assistant_svc.ask_bora(
            db,
            question=(
                "Drafto shkresën e mëposhtme për këtë lëndë, të plotë e të gatshme "
                f"për rishikim nga avokati (pa placeholder-a të panevojshëm): {arg or goal}"
            ),
            matter_id=matter.id,
            jurisdiction_id=matter.jurisdiction_id,
            provider_name=provider_name,
            language=language,
            region=region,
            style=style,
        )
        yield {
            "type": "approval",
            "kind": "draft",
            "title": (arg or goal)[:120],
            "content": answer,
        }
