# INDEX — Documentation router (read this, then load ONE topic)

Purpose: let **any LLM/agent** understand and safely change AvokatIM
while reading the minimum necessary. Entry point is always `AGENTS.md` (root)
→ this index → one topic.

## The layer at a glance (who owns what — no duplication)

| File | Owns | Never put here |
|---|---|---|
| `AGENTS.md` (root) | Identity, hard rules, conventions, session protocol | Live values, history |
| **`STATE.md`** | What is LIVE now: services, ports, config, watch items | History, settled debates |
| **`LESSONS.md`** | Settled decisions + incidents (check BEFORE proposing changes) | Live values |
| `DECISIONS.md` | Numbered architectural decisions + reasons | Day-to-day work |
| `CHANGELOG.md` | Dated trail of changes, newest on top | — |
| `UPDATE-PROTOCOL.md` | The write-side procedure after any change | — |

## How to route

| If your task touches… | Read | Then the sources it names |
|---|---|---|
| What's running now, ports, keys, restart/logs | `STATE.md` | — |
| Why is X like this? / proposing a change | `LESSONS.md` first | — |
| Architecture / structure | `DECISIONS.md` | FILL: architecture doc |
| FILL: area (e.g. backend API) | FILL: topic file | FILL: source dirs |
| You changed ANYTHING | `UPDATE-PROTOCOL.md` | — |

As the project grows, add numbered topic files (`01-architecture.md`,
`02-data-model.md`, ...) and route to them here — one topic per task.
