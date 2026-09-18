"""Golden-set citation eval gate (audit 2026-09-18, advancement #5).

Runs the golden question sets (eval/golden_xk.jsonl, eval/golden_de.jsonl)
through the PRODUCTION answer path (ask_bora: hybrid RAG + provider + prompt
assembly) and verifies every citation in every answer with the v2 verifier
(citation_check.verify_citations, quote-level).

GATE: (verified + approx) / total citations >= 95% per jurisdiction.
Run this before ANY model or prompt change ships (AGENTS.md §4 playbook).

    cd backend && .venv/bin/python scripts/eval_citations.py             # both
    cd backend && .venv/bin/python scripts/eval_citations.py --jur XK
    cd backend && .venv/bin/python scripts/eval_citations.py --jur DE --provider local
    cd backend && .venv/bin/python scripts/eval_citations.py --repair   # also measure repair latency

Exit code 0 = gate passed for every jurisdiction run; 1 = below threshold.
Full JSON: data/eval_citations_<date>.json (git-ignored runtime data).
"""
import argparse
import asyncio
import json
import sys
import time
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models import Jurisdiction  # noqa: E402
from app.services.assistant import ask_bora  # noqa: E402
from app.services.citation_check import repair_citations, verify_citations  # noqa: E402

GATE = 0.95
EVAL_DIR = Path(__file__).resolve().parents[1] / "eval"
LANG = {"XK": "sq", "DE": "de"}


def _load(code: str) -> list[dict]:
    path = EVAL_DIR / f"golden_{code.lower()}.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


async def _run_jurisdiction(
    code: str, provider: str | None, with_repair: bool
) -> dict:
    async with SessionLocal() as db:
        jur = (
            await db.execute(select(Jurisdiction).where(Jurisdiction.code == code))
        ).scalar_one()
    jur_id = jur.id
    rows = []
    for case in _load(code):
        t0 = time.monotonic()
        # Fresh session per case: one poisoned/killed connection (e.g. a DB
        # restart mid-run) must not cascade into every remaining case.
        try:
            async with SessionLocal() as db:
                answer, _rag_citations = await ask_bora(
                    db,
                    question=case["question"],
                    matter_id=None,
                    jurisdiction_id=jur_id,
                    provider_name=provider,
                    language=LANG[code],
                )
                answer_s = time.monotonic() - t0
                checks = await verify_citations(db, jur_id, answer)
                repair_s = None
                if with_repair and any(
                    c["status"] == "unverified" for c in checks
                ):
                    t1 = time.monotonic()
                    fixed = await repair_citations(
                        db, jur_id, answer, checks, provider
                    )
                    repair_s = time.monotonic() - t1
                    if fixed:
                        answer, checks = fixed
        except Exception as exc:  # a dead provider must fail the gate loudly
            rows.append({"id": case["id"], "error": str(exc), "checks": []})
            print(f"  [{code} #{case['id']:>2}] ERROR: {exc}")
            continue
        n = {"verified": 0, "approx": 0, "law_found": 0, "unverified": 0}
        for c in checks:
            n[c["status"]] += 1
        rows.append({
            "id": case["id"], "question": case["question"], "answer": answer,
            "checks": checks, "counts": n, "answer_s": round(answer_s, 1),
            "repair_s": round(repair_s, 1) if repair_s is not None else None,
        })
        bad = "" if not n["unverified"] else f"  UNVERIFIED: " + ", ".join(
            c["cite"] for c in checks if c["status"] == "unverified"
        )
        print(
            f"  [{code} #{case['id']:>2}] {len(checks)} citime: "
            f"{n['verified']}✓ {n['approx']}≈ {n['law_found']}§ "
            f"{n['unverified']}? ({answer_s:.0f}s)"
            + (f" riparim {repair_s:.0f}s" if repair_s is not None else "")
            + bad
        )

    total = sum(len(r["checks"]) for r in rows)
    good = sum(
        1 for r in rows for c in r["checks"] if c["status"] in ("verified", "approx")
    )
    law_found = sum(1 for r in rows for c in r["checks"] if c["status"] == "law_found")
    rate = good / total if total else 0.0
    errors = [r for r in rows if r.get("error")]
    return {
        "jurisdiction": code, "cases": len(rows), "errors": len(errors),
        "citations": total, "verified_or_approx": good, "law_found": law_found,
        "pass_rate": round(rate, 4), "gate": GATE,
        "passed": rate >= GATE and not errors, "rows": rows,
    }


async def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jur", choices=["XK", "DE", "both"], default="both")
    ap.add_argument("--provider", default=None,
                    help="LLM provider name (default: config default)")
    ap.add_argument("--repair", action="store_true",
                    help="also run+time the repair round on failures")
    args = ap.parse_args()
    codes = ["XK", "DE"] if args.jur == "both" else [args.jur]

    summaries = []
    for code in codes:
        print(f"== {code} (provider={args.provider or 'default'}) ==")
        summaries.append(
            await _run_jurisdiction(code, args.provider, args.repair)
        )

    out = Path(__file__).resolve().parents[2] / "data" / (
        f"eval_citations_{date.today().isoformat()}.json"
    )
    out.write_text(json.dumps(summaries, ensure_ascii=False, indent=1, default=str))
    all_pass = True
    for s in summaries:
        verdict = "PASS" if s["passed"] else "FAIL"
        all_pass &= s["passed"]
        print(
            f"{verdict}  {s['jurisdiction']}: {s['verified_or_approx']}/{s['citations']} "
            f"(verified+approx) = {s['pass_rate']:.1%} (gate {GATE:.0%}); "
            f"law_found={s['law_found']}, errors={s['errors']}"
        )
    print(f"raporti: {out}")
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    asyncio.run(main())
