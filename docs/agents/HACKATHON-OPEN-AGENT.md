# HACKATHON — Open Agent 2026 (Wildcard [Tinkerer])

Statusi: aktiv · Dega: hackathon/open-agent-2026 · Worktree: /home/kllosha/AvokatIM-hack
Afati i dorëzimit: 27.10.2026, 23:45 UTC

## Pse
Open Agent Hackathon ka një track të vetëm që pranon projekt ekzistues: **Wildcard
[Tinkerer]**. Rregullat e tij kërkojnë integrim të **Zetaris** dhe **Meterless** dhe
vlerësojnë vetëm punën e re. AvokatIM është projekti ynë ekzistues; puna e re është
shtresa e adapterave.

## Çfarë u shtua (Faza A, 22.10.2026)
- backend/app/adapters/base.py — kontrata Evidence / QuerySpec / SourceAdapter / dedupe
- backend/app/adapters/zetaris.py — adapter live (HTTP) + FixtureAdapter (mock i deklaruar)
- backend/app/adapters/meterless.py — ekzekutim lokal + usage.jsonl (një rresht për thirrje)
- backend/app/config.py — hackathon_mode (default false), zetaris_*, meterless_*,
  hackathon_usage_log
- backend/tests/test_adapters_contract.py — 5 teste, pa rrjet/DB

## Parimi
Asnjë SDK i sponsorit nuk futet në core. Gjithçka e jashtme vjen si Evidence përmes
adapterit, prandaj kodi ekzistues nuk ndryshon sjellje kur hackathon_mode=False.

## Hapat pasardhës
1. Zetaris: llogari + lidhja e tri burimeve (ligje / praktikë / regjistra).
2. Meterless: Nightshift lokal + matje në UI.
3. Harness 20 pyetje-etalon mbi korpusin real (bazë para ndryshimeve).
4. Video 1–4 min + slide deck + README dorëzimi.

## Lidhje
- Plani i plotë: ~/.openclaw/workspace/memory/plans/2026-10-22-dy-garat-plani-i-plote.md
- Faqja e eventit: https://hackathon.genai.works/event/open-agent-hackathon-2026
\n## Zetaris — kontrata reale (verifikuar 22.10.2026)\n\nPlatforma lokale (docker, \) ekspozon REST SQL editor:\n\n    POST http://127.0.0.1:8888/api/v1.0/sql-editor/sqls/run\n    Authorization: Bearer <zeta-*-key>\n    X-Org-ID: 1\n    X-Request-ID: <uuid>\n    {"queryId": "<uuid>", "sql": "SELECT 1", "source": "SqlEditor", "limit": 1}\n\nProvat e kryera:\n\n- \ → **200**, \ (kërkesa e smoke_test.py të guide-it).\n- \ → \.\n- \ → 400 TABLE_OR_VIEW_NOT_FOUND (motor Spark-like).\n- \ → kërkon \; \ të thjeshta janë çaktivizuar.\n\nPasoja për adapterin: \ është rruga e vetme; \ do të\nsynojë tabelën e korpusit kur ajo të krijohet, ndryshe ngre \ (fail-closed,\npa gënjeshtra). Çelësi lexohet nga \ (0600) dhe\nnuk shfaqet në log.\n

## Harness etalon — matjet (22.10.2026)

20 pyetje: 15 brenda korpusit (ligje/kode shqip), 5 jashtë (duhet refuzim).

| Varianti | Brenda (ok/15) | Jashtë (refuzuar/5) | Gjithsej |
|---|---|---|---|
| v1 plainto_tsquery | 9 | 2 | 11/20 |
| v2 OR + prag | 10 | 1 | 11/20 |
| v2 + portë domeni | 9 | 4 | 13/20 |
| v2 + portë + fjalor i zgjeruar | 10 | 4 | 14/20 |

Porta e domenit (LEGAL_HINTS) është ajo që e bën agjentin të thotë "s'e di": pa të,
pyetjet jashtë korpusit (TVSH në Norvegji, zgjedhjet në Brazil) merrnin fragmente të
rastësishme nga ligjet. Me të, 4/5 refuzohen saktë.

Raportet: data/evidence/harness-*.json (v1) dhe harness-v2-*.json (v2).
Ekzekutimi: AVOKATIM_DSN=<dsn> python hackathon/harness_v2.py


## Harness v3 — kërkim vektor (22.10.2026)

Modeli paraphrase-multilingual-MiniLM-L12-v2 (384 dim) nga cache lokale; pgvector
mbi 350 612 chunks. Asnjë tekst nuk del nga makina.

| Varianti | Brenda (ok/15) | Jashtë (refuzuar/5) | Gjithsej |
|---|---|---|---|
| v1 leksikor | 9 | 2 | 11/20 |
| v2 + portë domeni | 10 | 4 | 14/20 |
| v3 vektor + portë | 12 | 4 | 16/20 |

hit@5 u ngjit nga 6 në 7, keyword@5 nga 8 në 10. Mbeten: q02 (parashkrim),
q17 (punë), q18 (ekzekutim) — kërkim vektor gjen tekstin e duhur por jo titullin
e pritur; q15 (Tokio) kalon portën sepse "regjistrim" është term juridik.

Raporti: data/evidence/harness-v3-*.json
Ekzekutimi: AVOKATIM_DSN=<dsn> python hackathon/harness_v3.py


## Meta Model API adapter (22.10.2026)

backend/app/adapters/meta_model.py — klient OpenAI-compatible për modelet e Meta-s
(Muse/SAM). base_url, api_key dhe modeli vijnë nga konfigurimi; pa to adapteri
raporton available() == False dhe ngre AdapterError (fail-closed, pa thirrje të rreme).

- MetaModelAdapter.complete(prompt, system) -> Completion(text, model, tokens_in, tokens_out, ms)
- StubModel — zëvendësues determinist për teste/demo offline, i etiketuar si stub.

Testet: tests/test_adapters_meta.py (3 teste) + tests/test_adapters_contract.py (5 teste)
— 8 passed, pa rrjet.
