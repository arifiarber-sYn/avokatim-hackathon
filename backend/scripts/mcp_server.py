"""AvokatIM MCP server (audit 2026-09-18, advancement #8 — the Eudia
pattern: open agentic tools over the platform).

Talks to the RUNNING AvokatIM API over loopback HTTP with a personal API
token, so tenant scoping, permissions and the read-only token contract are
enforced by the same code paths as every other client. All tools are
read-only except `drafto_memo`, which saves a clearly-labelled draft note on
the matter for the lawyer to review (approval-by-review, D-044) — it
requires a `read_write` token; with a `read` token the API rejects it.

Setup:
  1. Create an API token in AvokatIM (Settings → API tokens).
  2. Register in ~/.cursor/mcp.json (or any MCP client):
     {"mcpServers": {"avokatim": {
        "command": "/home/kllosha/AvokatIM/backend/.venv/bin/python",
        "args": ["/home/kllosha/AvokatIM/backend/scripts/mcp_server.py"],
        "env": {"AVOKATIM_API_TOKEN": "avk_..."}}}}
"""
import os

import httpx
from mcp.server.mcpserver import MCPServer

BASE = os.environ.get("AVOKATIM_API_BASE", "http://127.0.0.1:8000/api")
TOKEN = os.environ.get("AVOKATIM_API_TOKEN", "")

server = MCPServer(
    "avokatim",
    instructions=(
        "AvokatIM legal practice tools: search the Kosovo/German legal corpus, "
        "read matters, deadlines and documents of the authenticated lawyer's "
        "office. Everything is read-only except drafto_memo, which saves a "
        "draft note the lawyer reviews. Cite laws as 'neni X i <ligji>' / '§ X <Gesetz>'."
    ),
)


def _client() -> httpx.Client:
    if not TOKEN:
        raise RuntimeError("AVOKATIM_API_TOKEN is not set")
    return httpx.Client(
        base_url=BASE, headers={"Authorization": f"Bearer {TOKEN}"}, timeout=30
    )


@server.tool()
def kerko_korpusin(query: str, jurisdiction_code: str | None = None, limit: int = 8) -> str:
    """Hybrid (full-text + semantic) search over the legal corpus — laws and
    court decisions. jurisdiction_code: XK (Kosovo) or DE (Germany); default
    is the office's jurisdiction."""
    with _client() as c:
        params: dict = {"q": query, "limit": limit}
        if jurisdiction_code:
            params["jurisdiction_code"] = jurisdiction_code
        r = c.get("/corpus/search", params=params)
        r.raise_for_status()
        hits = r.json()
    if not hits:
        return "Asnjë rezultat."
    return "\n\n".join(
        f"[{h['doc_title']}"
        + (f", {h['section']}" if h.get("section") else "")
        + (f" ({h['reference']})" if h.get("reference") else "")
        + f"]\n{h['text'][:900]}"
        for h in hits
    )


@server.tool()
def lexo_lenden(matter_id: str) -> str:
    """Read one matter of the office: status, parties, notes. matter_id is
    the UUID from lista_e_lendeve or the AvokatIM UI URL."""
    with _client() as c:
        r = c.get(f"/matters/{matter_id}")
        r.raise_for_status()
        m = r.json()
        notes = c.get(f"/matters/{matter_id}/notes")
        notes_j = notes.json() if notes.status_code == 200 else []
    out = [
        f"{m.get('reference')} — {m.get('title')}",
        f"Statusi: {m.get('status')} | Fusha: {m.get('practice_area')}",
        f"Klienti: {(m.get('client') or {}).get('display_name', '—')}",
        f"Përshkrimi: {m.get('description') or '—'}",
    ]
    for n in notes_j[:5]:
        out.append(f"— Shënim ({n.get('created_at', '')[:10]}): {n.get('body', '')[:400]}")
    return "\n".join(out)


@server.tool()
def lista_e_lendeve(status: str = "open") -> str:
    """List the office's matters (id, reference, title). status: open|closed|all."""
    with _client() as c:
        r = c.get("/matters")
        r.raise_for_status()
        matters = r.json()
    rows = [
        f"{m['id']} | {m.get('reference')} | {m.get('title')} | {m.get('status')}"
        for m in matters
        if status == "all" or m.get("status") == status
    ]
    return "\n".join(rows[:100]) or "Asnjë lëndë."


@server.tool()
def afatet_e_lendes(matter_id: str) -> str:
    """The matter's deadlines and hearings (from the deadline engine)."""
    with _client() as c:
        r = c.get(f"/matters/{matter_id}/deadlines")
        r.raise_for_status()
        items = r.json()
    if not items:
        return "Lënda s'ka afate të regjistruara."
    return "\n".join(
        f"- {d.get('due_at', '')[:16]} | {d.get('kind')} | {d.get('title')}"
        + (f" ({d['legal_basis']})" if d.get("legal_basis") else "")
        + f" | {d.get('status')}"
        for d in items
    )


@server.tool()
def kerko_dokumentet(query: str) -> str:
    """Global search across the office: matters, contacts, documents, notes."""
    with _client() as c:
        r = c.get("/search", params={"q": query})
        r.raise_for_status()
        res = r.json()
    lines = []
    for group, items in res.items():
        if not isinstance(items, list):
            continue
        for it in items[:8]:
            label = it.get("title") or it.get("filename") or it.get("display_name") or "?"
            lines.append(f"[{group}] {label}" + (f" (id {it['id']})" if it.get("id") else ""))
    return "\n".join(lines) or "Asnjë rezultat."


@server.tool()
def drafto_memo(matter_id: str, teksti: str) -> str:
    """Save a DRAFT memo as a note on the matter, for the lawyer's review.
    The only writing tool; requires a read_write API token. The note is
    clearly labelled as an externally-drafted memo."""
    body = f"[DRAFT MEMO — nga vegla MCP, kërkon shqyrtimin e avokatit]\n\n{teksti}"
    with _client() as c:
        r = c.post(f"/matters/{matter_id}/notes", json={"body": body})
        if r.status_code == 403:
            return ("Refuzuar: token-i është read-only. Krijo një token "
                    "read_write në Settings → API tokens për të ruajtur memo.")
        r.raise_for_status()
        n = r.json()
    return f"Memo u ruajt si shënim i lëndës (note id {n.get('id')}). Avokati e sheh te Shënimet."


if __name__ == "__main__":
    server.run()
