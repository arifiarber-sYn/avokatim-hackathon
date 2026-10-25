## 2026-10-25 — C1: Meta Model API adapter — provë me pyetje reale

- Done: `app/adapters/meta_model.py` (tashmë ekzistonte nga A2) u verifikua LIVE:
  `MetaModelAdapter(base_url=api.together.xyz/v1, model=meta-models/Muse-Spark-Open-816B-A42B-promo)`
  përgjigjet me pyetje reale («Shkruaj një fjali përshkruese për një aplikacion drejtësie
  në gjuhën shqipe») → 4.9 s, 169 token in / 468 out, tekst në shqip i saktë.
- Key-ja: `~/.securevault/secrets/together-api.key` (0600, emri `halim-gara-2026-10-16`);
  s'është e hardkoduar — adapteri e merr nga `settings.meta_model_base_url/api_key` ose nga
  constructor-i. Pa key `available() == False` dhe thirrësit degradojnë (StubModel për demo).
- Verified: `pytest tests/test_adapters_contract.py -q` → 5 passed; thirrja live pa gabime.
- Left open / next: C5 (submission para 23:45 UTC) dhe D1 (degë meta/indie me adapter Meta).

## 2026-10-23 — B2: Meterless adapter, usage.jsonl, kosto në UI

- Done: `app/adapters/meterless.py` tani mban kontabilitet të plotë: `cost_of()`
  (USD për 1M token, çmime nga `settings.meterless_price_*_per_mtok`, parazgjedhur 0
  = model lokal), `Usage.cost_usd` në çdo rresht të `data/evidence/usage.jsonl`, dhe
  `summarize()` që agregon thirrjet/token-at/koston/kohën dhe i reziston rreshtave
  të korruptuar (i numëron, nuk dështon).
- API: `GET /api/hackathon/usage?last=N` (`app/api/hackathon.py`, vetëm lexim, auth
  normal) — pa DB, pa thirrje provideri; regjistruar në `main.py`.
- UI: `components/meterless-cost.tsx` në faqen `/assistant` — shfaq «Meterless · N
  thirrje · X token · kosto $0.0000 · dokumentet nuk dolën nga makina»; fshihet vetë
  kur log-u është bosh (prod i paprekur).
- Demo: `backend/hackathon/demo_integrated.py` shtyp `ms`, token-at, koston dhe
  rrugën e `usage.jsonl` (më parë lexonte `latency_ms` që s'ekzistonte → «?»).
- Verified: `PYTHONPATH=. pytest tests/test_meterless_usage.py tests/test_adapters_contract.py -q`
  → 11 passed; `py_compile` OK për adapterin, API-n dhe demoin. `app.main` nuk
  importohet në këtë makinë pa `pgvector` (mungon në python-in e sistemit) — provë
  e API-së mbetet për mjedisin e backend-it.
- Left open / next: B3 (gjurmë arsyetimi në UI) dhe B5 (≥15 teste); Nightshift
  ende i pa instaluar, ndaj çdo kosto reale është $0 dhe log-u mbushet kur hotspot-i
  ngrihet.
