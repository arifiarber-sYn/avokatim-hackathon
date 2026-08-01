# LESSONS — settled decisions and incidents (check BEFORE proposing changes)

> Append-only, numbered. Each entry: **symptom → cause → rule**. If an idea
> here was tried and failed, do not re-litigate it without new evidence.
> A lesson that repeats (same class, second incident) MUST become a
> deterministic check (script / hook / lint), not just prose — AgentStandard §6.

## #1 — Most German Länder law portals cannot be scraped with curl (2026-08-01)

- **Symptom**: landesrecht-bw.de and gesetze.berlin.de return a ~5 KB HTML
  shell with one JS bundle; no law text in the response.
- **Cause**: 14 of 16 Länder host on juris single-page apps whose content
  comes from a token-authenticated internal API ("mylex", refresh-token
  flow) — plain HTTP fetching gets no document bodies. Only NRW
  (recht.nrw.de, server-rendered Drupal) and Bayern (gesetze-bayern.de,
  `/Content/Document/{slug}/true`) serve full acts as HTML.
- **Rule**: for Landesrecht beyond NRW/BY, do not burn time on curl-based
  adapters — it needs a headless browser (or a juris data agreement).
  Amtliche Werke are § 5 UrhG copyright-free, so the obstacle is purely
  technical, not legal. See `scripts/import_de_landesrecht.py` for the
  two working adapters.
