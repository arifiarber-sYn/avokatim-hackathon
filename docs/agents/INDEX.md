# INDEX — Documentation router (read this, then load what your task needs)

Purpose: let **any LLM/agent** understand and safely change AvokatIM while
reading the minimum necessary. Entry point is always `AGENTS.md` (root) →
this index → the file(s) your task touches.

## The layer at a glance (who owns what — no duplication)

| File | Owns | Never put here |
|---|---|---|
| `AGENTS.md` (root) | Identity, hard rules, conventions, session protocol, architecture map | Live values, history |
| **`STATE.md`** | Current snapshot: what exists, what works, environment | History, settled debates |
| **`LESSONS.md`** | Settled operational lessons + incidents (check BEFORE proposing changes) | Architecture decisions |
| `DECISIONS.md` | Numbered architectural decisions (D-001…) + reasons | Day-to-day work |
| `JOURNAL.md` | Chronological work log (this project's changelog) | — |
| `COMMS.md` | Every automated email + Halim's correspondence protocol | — |
| `ROADMAP.md` | Vision, phases, backlog | Current state |
| `UPDATE-PROTOCOL.md` | The write-side procedure after any change | — |

## How to route

| If your task touches… | Read | Then the sources it names |
|---|---|---|
| What's running, services, env, known issues | `STATE.md` (search it — it is long) | — |
| Recent work / what changed | last 2–3 entries of `JOURNAL.md` + `git log` | — |
| Architecture / "why is X like this?" | `DECISIONS.md` (scan titles, read relevant D-numbers) | — |
| Proposing to remove/replace something | `LESSONS.md` first | — |
| Anything that emails users or notifies the operator | `COMMS.md` (mandatory) | `backend/app/i18n.py`, `services/notifications.py` |
| Frontend work | `frontend/AGENTS.md` (Next.js caveats) | `frontend/src/` |
| Deadlines/jurisdiction/legal data | `AGENTS.md` §Hard rules | `backend/app/seeds/` |
| Integrations (e-Kosova, e-notary, WhatsApp) | `../integrimet/` | — |
| Platform legal docs (ToS, privacy, AML) | `../legal/` | — |
| What to build next | `ROADMAP.md` | — |
| You changed ANYTHING | `UPDATE-PROTOCOL.md` | — |

Machine-checked live view: `curl http://127.0.0.1:8000/api/health` +
`systemctl --user status avokatim`.
