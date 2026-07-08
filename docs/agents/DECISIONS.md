# DECISIONS — architectural decision log

> Append-only. One numbered entry per decision. Never delete entries; if a
> decision is reversed, add a new entry that supersedes the old one.
> Format: context → decision → consequences.

## D-001: Web app, self-hosted on the owner's machine

- Context: owner wants full control, local data, and outside access for himself.
- Decision: web stack (FastAPI + Next.js) hosted on this computer; Caddy provides
  HTTPS on :8443 for LAN/external access.
- Consequences: no cloud costs or dependencies; machine must stay on; autostart
  handled by systemd user service.

## D-002: Multi-tenant and multi-jurisdiction from the foundation

- Context: solo lawyer today, law firms and more jurisdictions later; goal is a
  globally competitive product.
- Decision: tenancy models from day one; jurisdiction rules (deadlines, holidays,
  templates, corpus) are database *data* seeded per jurisdiction, never code.
- Consequences: adding a jurisdiction = writing seeds, not refactoring; Kosovo (XK)
  is the reference implementation.

## D-003: LLM-agnostic provider abstraction

- Context: LLM landscape changes fast; owner wants the option of a local model.
- Decision: all LLM calls go through `backend/app/llm/` (base interface + provider
  implementations + router). DeepSeek is the default; any OpenAI-compatible local
  endpoint (Ollama/vLLM) is a drop-in alternative, selectable per request.
- Consequences: swapping/adding an LLM touches one module only.

## D-004: Local embeddings; client documents never leave the machine

- Context: attorney–client privilege; documents are the most sensitive data.
- Decision: semantic indexing uses local sentence-transformers
  (multilingual MiniLM, 384 dims) + pgvector. Documents encrypted at rest (Fernet).
  Only assistant *prompts* (question + retrieved snippets) go to a remote LLM, and
  a local LLM removes even that.
- Consequences: indexing has no per-token cost; embedding model changes require
  reindexing the corpus.

## D-005: Deadline engine driven by named rules with holiday calendars

- Context: procedural deadlines are the highest-risk part of legal practice.
- Decision: deadline rules are seeded records (code, base event, period, unit,
  holiday handling) per jurisdiction, with official holiday calendars; the engine
  computes dates and is covered by unit tests.
- Consequences: legal changes are data updates; every rule change needs a test.

## D-006: Agent-agnostic project management via AGENTS.md + docs/agents/

- Context: owner switches between agents/LLMs; work continuity must not depend on
  any single tool's chat history.
- Decision: `AGENTS.md` is the universal entry point (with `CLAUDE.md` pointer);
  persistent memory lives in-repo: STATE (snapshot), JOURNAL (log),
  DECISIONS (this file), ROADMAP (direction). Session protocol in AGENTS.md §2.
- Consequences: every agent must follow the session protocol or the system decays.

## D-007: E-signature legal basis and the path to qualified signatures (2026-07-08)

- Context: BoraLaw's portal e-signature (typed name + SHA-256 + IP + timestamp)
  is a *simple* electronic signature. Kosovo's governing law is
  **Law No. 08/L-022 on Electronic Identification and Trust Services in
  Electronic Transactions** (in force 2022; earlier docs wrongly cited
  06/L-037). Art. 32 makes *qualified* e-signatures equivalent to handwritten;
  simple ones remain admissible under the non-discrimination principle.
- Decision: (1) ship a "Certificate of Completion" PDF (WeasyPrint,
  `GET /matters/{id}/signatures/{sig_id}/certificate`) documenting the evidence
  chain of the simple signature; (2) for qualified signatures, integrate later
  with a Ministry of Economy-licensed QTSP — as of 2026 the recognized
  providers are **Evrotrust Technologies JSC & IT Vision** (decisions
  no. 6269/15.12.2023 and 5404/16.08.2024) and **rTrust (PBC)**, both
  eIDAS-recognized in the EU. Integration would follow the same abstraction
  pattern as `app/llm/` (provider interface, swappable).
- Consequences: current signatures are legally usable evidence but not
  handwritten-equivalent; contracts requiring written form still need wet ink
  or a QTSP integration (planned, next phase; likely per-signature cost).
