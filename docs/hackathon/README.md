# Open Agent Hackathon 2026 — dorëzimi

**Track:** Wildcard [Tinkerer] · **Projekti:** AvokatIM · **Afati:** 27.10.2026, 23:45 UTC

## Çka është

Platformë për praktikë ligjore që një avokat i vetëm ta mbajë me kapacitetin e një zyre:
intake, afate procedurale, dokumente, kërkim me citime, përgatitje seance.

**Teza:** jo përgjigje që tingëllojnë të sigurta — përgjigje që mund t'i kontrollosh.
Çdo pohim mban burimin: ligji, neni, dokumenti.

## Provat (të riprodhueshme)

| Matja | Vlera | Ku |
|---|---|---|
| Harness 20 pyetje — brenda domenit | **15/15** | `backend/hackathon/harness_v5.py` |
| `kw@5` / `hit@5` | **14** / **10** | `data/evidence/harness-v5-20261025T143201Z.json` |
| Jashtë domenit — refuzuar | **5/5** | i njëjti raport |
| Teste | **50 passed, 1 skipped** | `pytest` |
| Kontrata adapterësh | **5/5** | `backend/tests/test_adapters_contract.py` |

## Materialet

- **Video 36 s:** `docs/hackathon/video/demo-avokatim.mp4`
- **Deck 8 slide:** `docs/hackathon/deck/deck-avokatim.pdf`

## Arkitektura e shtresës së re

```
core (i paprekur)  ->  Evidence contract  ->  adaptera te jashtem
                        zetaris.py  |  meterless.py  |  meta_model.py
```

Asnjë SDK i sponsorit nuk futet në core; kur `hackathon_mode=False`, sjellja nuk ndryshon.

## Statusi i sponsoreve — i saktë, jo i zbukuruar

| Sponsori | Çka punon | Çka nuk punon |
|---|---|---|
| **Zetaris** | platformë lokale (4 kontejnerë), hyrje JWT 200, `SHOW CATALOGS` | planifikuesi i bundle-it: `NoClassDefFoundError: UnityCatalogTableNode` — me riprodhim |
| **Meterless** | ekzekutim lokal + `usage.jsonl` (një rresht për thirrje) | Nightshift në UI — pa integrim vizual |
| **Meta Model** | provë LIVE: Muse-Spark, 4.9s, 169 in / 468 out | — |

Riprodhimi i defektit të Zetaris-it:

```bash
python3 ~/oa-korpus/zet_query.py "SHOW CATALOGS"    # OK -> spark_catalog
python3 ~/oa-korpus/zet_query.py "SELECT 1"         # NoClassDefFoundError
```

## Çka nuk hyn

- Lidhje e plotë Zetaris me të dhëna reale (e bllokuar nga bundle-i).
- `hit@5` 10/15 — burimi i saktë nuk u gjet në 5 raste, edhe pse përmbajtja ishte relevante.
- Asnjë pretendim për përdorues realë: produkti është në zhvillim.

## Si riprodhohet

```bash
cd backend && pytest -q                       # 50 teste
python3 hackathon/harness_v5.py               # harness 20 pyetje
```
