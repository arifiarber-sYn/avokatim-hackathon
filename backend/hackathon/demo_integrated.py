#!/usr/bin/env python3
"""Demo i integruar: Zetaris (retrieval) + Meterless (model lokal) + korpusi vendas.

Rendi i provave, i deklaruar hapur:
  1) Zetaris   - SQL federativ mbi burimet e regjistruara
  2) Korpusi   - demo_corpus.py mbi korpusin e ngrire
  3) Meterless - model lokal + usage log

Perdorimi:  python hackathon/demo_integrated.py "pyetja"
"""
from __future__ import annotations

import asyncio
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from app.adapters.base import QuerySpec  # noqa: E402
from app.adapters.zetaris import ZetarisAdapter  # noqa: E402
from app.adapters.meterless import MeterlessAdapter  # noqa: E402
import demo_corpus  # noqa: E402

KEY = pathlib.Path.home() / ".securevault" / "secrets" / "zetaris-api.key"


async def try_zetaris(question: str) -> list:
    key = KEY.read_text(encoding="utf-8").strip() if KEY.exists() else ""
    ad = ZetarisAdapter(base_url="http://127.0.0.1:8888/api/v1.0", api_key=key, org_id="1", sources=[])
    if not ad.available():
        print("ZETARIS: i pakonfiguruar")
        return []
    try:
        rows = await ad.sql("SELECT 1 AS ok", limit=1)
        print("ZETARIS: lidhja OK, SELECT 1 ->", rows)
    except Exception as e:
        print("ZETARIS: lidhja deshtoi ->", str(e)[:100])
        return []
    if not ad.sources:
        print("ZETARIS: 0 datasource te regjistruar - kaloj te korpusi vendas")
        return []
    try:
        ev = await ad.query(QuerySpec(text=question, sources=[], limit=5))
        print("ZETARIS: %d deshmi" % len(ev))
        return ev
    except Exception as e:
        print("ZETARIS: query deshtoi ->", str(e)[:100])
        return []


async def try_meterless(prompt: str):
    ad = MeterlessAdapter()
    if not ad.available():
        print("METERLESS: hotspot lokal i padisponueshem")
        return None
    try:
        text, usage = await ad.chat(prompt)
        print("METERLESS: %s | kohe=%sms" % (getattr(usage, "model", "?"), getattr(usage, "latency_ms", "?")))
        return text
    except Exception as e:
        print("METERLESS: deshtoi ->", str(e)[:100])
        return None


async def main() -> int:
    q = sys.argv[1] if len(sys.argv) > 1 else "Kush u ankua per dezinsektimin e Prizrenit?"
    print("PYETJA:", q)
    print("-" * 60)
    await try_zetaris(q)
    r = demo_corpus.answer(q)
    print("-" * 60)
    if not r.get("ok"):
        print("PERGJIGJA: s'e di -", r.get("reason"))
        return 0
    print("BURIMI 1 (vendim):", r["skedari"])
    print("  citat:", r["citat"][:220])
    if r.get("numer"):
        print("BURIMI 2 (regjister):", r["regjistri"], "|", r["numer"], "|", r["vlera"], r["monedha"])
    print("BURIMI 3 (ligj): neni", ", ".join(str(x) for x in r["nene"]))
    print("-" * 60)
    ans = await try_meterless("Pergjigju shkurt ne shqip, vetem nga ky citat:\n" + r["citat"])
    print("PERGJIGJA:", (ans or ("Nga korpusi: " + r["citat"]))[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
