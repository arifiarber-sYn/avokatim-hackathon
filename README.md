# AvokatIM — the agent that explains why

Submission for **Open Agent Hackathon 2026**, track **Wildcard [Tinkerer]**.

A legal agent for the Albanian language that **never answers without a source**: every claim
comes with a document, an article and a fragment, and when the corpus has no answer it says
*"I don't know"* with a reason instead of inventing one.

## What is in this repository

| Path | What |
|---|---|
| docs/hackathon/submission.md | submission write-up |
| docs/hackathon/deck.pdf | 10 slides |
| docs/hackathon/video/demo-full.mp4 | 90 s demo, recorded on the live product |
| docs/hackathon/video/demo-2min.mp4 | 1:56 version with the before/after numbers |
| docs/hackathon/arta-verifikuar.md | verification of 10 gold answers, round by round |
| backend/hackathon/ | retrieval harness (3 question sets) + demo CLI |
| backend/app/adapters/ | Zetaris, Meterless and Meta Model adapters with contract tests |

## Numbers (measured, not claimed)

**Retrieval** — blind set, 13 questions: 10/10 answered inside the corpus, 3/3 out-of-domain
questions refused with a reason.

**Answers** — 10 gold questions, checked against the article title and full article text:

| Metric | Value |
|---|---|
| Correct law at rank 1 | 10/10 |
| Exact and complete article | 2/10 |
| Correct article within top-3 | 7/10 |
| Wrong source at rank 1 | 0/10 |

Stated limit: the system finds the right law almost always, but does not always pick the
article that answers. We measure it and print it instead of hiding it behind an average.

## Verify in two minutes

    git clone https://github.com/arifiarber-sYn/avokatim-hackathon.git
    cd avokatim-hackathon
    # the harness needs PostgreSQL + pgvector with the legal corpus (not distributed)
    export AVOKATIM_DSN="postgresql://user:***@127.0.0.1:5433/avokatim"
    python backend/hackathon/harness_v5.py

Without the corpus the harness still documents the method and the scoring rules.

## Sponsors

- **Zetaris** — adapter verified against the local REST SQL editor (SELECT 1 → 200 on 22.10).
  Status 22.10 17:10: the platform runs (4 containers healthy, UI 200) but the stored API token
  is rejected ("Api token is not allowed"), so the path is not live until a new token is issued.
- **Meterless** — adapter plus usage.jsonl for cost and tokens. The native Nightshift build
  exists only for macOS, Windows and DGX Spark (arm64); a build/API request was sent.
  Partial integration is declared, not overstated.

## License

Code in this submission: MIT. The legal corpus and client data are not included.

## Run it in 60 seconds — no database, no dependencies

    git clone https://github.com/arifiarber-sYn/avokatim-hackathon.git
    cd avokatim-hackathon/backend/hackathon
    python3 demo_sample.py "Çfarë duhet të përmbajë kontrata e punës?"

This runs against a 555-article sample of real Kosovo law (8 statutes, laws only — no court
decisions, no personal data) with pure Python and no installs. It shows the same behaviour as
production: document + article + fragment, and *"I don't know"* for questions outside the corpus.

The full system (`demo.py`, `harness_v5.py`) needs PostgreSQL + pgvector with the 353k-chunk
corpus, which is not distributed.
