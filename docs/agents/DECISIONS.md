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
