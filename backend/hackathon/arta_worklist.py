#!/usr/bin/env python3
"""Gjeneron fletën e verifikimit: çka kthen sistemi vs çka është e saktë.

Nuk e shpall vetë "artë" — e paraqet kandidatin më të mirë që sistemi gjen, që njeriu
ta konfirmojë ose ta korrigjojë. Pa këtë hap, çdo matje e saktësisë do të ishte
matje e vetvetes.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from demo import MODEL, retrieve

QUESTIONS = [
    "Kur fillon afati i parashkrimit të kërkesave?",
    "Çfarë duhet të përmbajë kontrata e punës?",
    "Si ndahet pasuria e përbashkët e bashkëshortëve?",
    "Kur lirohet i pandehuri nga paraburgimi?",
    "Kush trashëgon pas vdekjes sipas ligjit?",
    "Cilat janë të drejtat e subjektit të të dhënave personale?",
    "Çfarë është shoqëria me përgjegjësi të kufizuar?",
    "Si mbrohet konkurrenca në treg?",
    "Cilat janë kushtet për lidhjen e martesës?",
    "Çfarë parashikon ligji për mbrojtjen e konsumatorit?",
]


def main() -> int:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(MODEL, cache_folder=str(Path.home() / ".cache" / "huggingface"))
    lines = ["# Fletë verifikimi — kandidatët e sistemit", "",
             "Për çdo pyetje: shëno në kolonën e fundit **PO** nëse dokumenti + neni janë",
             "përgjigjja e saktë, ose shkruaj dokumentin/nenin e saktë. Kjo fletë bëhet",
             "baza e matjes me përgjigje-arta.", ""]
    for i, q in enumerate(QUESTIONS, 1):
        hits, why = retrieve(q, model)
        lines.append(f"## {i}. {q}")
        if not hits:
            lines.append(f"- **sistem i**: s'e di — {why}")
            lines.append("- **i saktë**: \n")
            continue
        for rank, h in enumerate(hits[:3], 1):
            section = h.get("section") or "—"
            snippet = " ".join((h["snippet"] or "").split())[:120]
            lines.append(f"- **{rank}.** {h['title']} · {section} · sim {h['sim']:.3f}")
            lines.append(f"  - «{snippet}…»")
        lines.append("- **i saktë (plotëso)**: \n")
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "hackathon" / "arta-per-verifikim.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print("shkruar", out, len(lines), "rreshta")
    return 0


if __name__ == "__main__":
    sys.exit(main())

