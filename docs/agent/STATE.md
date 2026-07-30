# STATE — what is LIVE right now (single source of truth)

> **This is the ONLY file that must change when the live setup changes.**
> History → `CHANGELOG.md`; settled decisions → `LESSONS.md`.

Last verified: **FILL: date** (FILL: how it was verified).

## Services

FILL: table of services / units / containers with ports, log locations and
the restart command. Include the machine-checked view (health endpoint,
status command) so any agent can verify instead of trusting this file.

## Configuration

FILL: where config lives (.env keys — names only, never values), which LLM
provider is active, feature flags.

## Watch items

FILL: things that are live but fragile / pending / untested — the first
things a fresh agent should know about.

## Git

FILL: repo root, branch, who commits here (list agents if more than one).
Before any change: `git log --oneline -5 && git status`.
