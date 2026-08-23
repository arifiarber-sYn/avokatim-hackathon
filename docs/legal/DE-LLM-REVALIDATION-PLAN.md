# DE LLM re-validation plan — launch-gate item 3 (D-082)

> **Status: EKZEKUTUAR 2026-08-23 — VERDIKT: FAIL (item 3 mbetet i hapur).**
> Rezultatet: `backend/scripts/eval_de_quality.py` + `backend/data/eval_de_quality_2026-08-23.json`.
> Kriteret e cilësisë (a) kaluan; latenca (p95 19.3s vs ≤5s) dhe madhësia e kontekstit
> (max 15.3K vs ≤13.1K tokena me ctx 16384) dështuan; `qwen3.8:27b-agent` (ctx 98K)
> jopraktik në këtë makinë (VRAM → CPU offload). DE qëndron në DeepSeek.
> Hapat e nevojshëm para ri-validimi: rregullimi i chunk-ing-ut të korpusit DE
> (paragrafë gjigantë), zgjidhja e latencës (GPU e lirë ose kriter i rishikuar).
> Detaje: docs/agents/JOURNAL.md 2026-08-23, docs/legal/DE-LAUNCH-GATE.md item 3.
> **Target:** `PROFILES["DE"].llm_provider` → `"local"` (tani `None` = DeepSeek,
> përkohësisht, kërkesë e pronarit 2026-08-01). Para lansimit publik DE, item 3
> i DE-LAUNCH-GATE.md kërkon ri-validim formal të modelit lokal të ri
> `qwen3.8:27b` (D-082: gemma3:27b u fshi në konsolidimin fleet-wide).

## Konteksti

- Modeli i ri lokal: `qwen3.8:27b` (`backend/.env: LOCAL_LLM_MODEL=qwen3.8:27b`);
  `backend/app/llm/local.py` shton `reasoning_effort=low` (qwen3.8 është model
  "thinking" — low e mban latencën e parashikueshme pa prishur cilësinë RAG).
- Validim informal i mëparshëm (D-081 shootout): pa përgjigje boshe, dallim i
  saktë Mieter/Vermieter § 573c BGB, citim i saktë "Art. 17 DSGVO", latencë
  1.7–3.5s. Tani kërkohet **validim formal me RAG real**.
- RAG: `backend/app/services/rag.py` `search_corpus` — hybrid (dense + FTS +
  rare-word), `limit=6`, maksimum 2 gjykime. Chunks ~CHUNK_SIZE chars.

## Tre pjesët e ri-validimit (sipas DE-LAUNCH-GATE.md)

### (a) Cilësia gjermanishte e `qwen3.8:27b` me RAG real

Set testesh: **20 pyetje juridike gjermane** (14 NL-të e `eval_de_recherche.py`
+ 6 citime-§; secila me ref+§ të pritur). Për secilën: RAG real mbi korpusin DE
(`search_corpus`) → kontekst → `LocalProvider.chat` me `qwen3.8:27b`.

Kriteret e kalimit (të gjitha):
1. **Pa përgjigje boshe:** 20/20 jo-bosh (0 tolerohet).
2. **Citim i saktë:** ≥ 85% (17/20) e përgjigjeve përmbajnë ref+§ të pritur
   (krahasim i normalizuar si në `eval_de_recherche.py`).
3. **Gjermanishte e pastër:** 20/20 pa anglishte/zhurmë në përgjigje.
4. **Pa halucinim statute:** 0 statute të shpikura (kontroll: § i cituar duhet
   të ekzistojë në korpusin DE — verifikim automatik kundrejt DB).
5. **Latencë:** p95 ≤ 5s (baseline D-081: 1.7–3.5s; kufiri i sipërm i liruar
   për ngarkesë të ndryshme).

### (b) Madhësia e kontekstit — num_ctx

Problemi i njohur: endpoint-i OpenAI-compat i Ollama-s **NUK pranon `num_ctx`
në body**. Nëse RAG-u kalon ~4K tokena, duhet variant Modelfile me `num_ctx`
më të madh (p.sh. `qwen3.8:27b-agent`, ctx 40K — ekziston tashmë në ollama).

Matje (gjatë ekzekutimit të (a)):
- Për secilën pyetje, regjistro `prompt_tokens` nga `usage` i përgjigjes.
- **Kriter:** prompt_i gjatë (RAG 6 chunks + sistem + histori) ≤ 80% e
  kontekstit të shërbyer. Nëse tejkalon → ri-xhiro me `LOCAL_LLM_MODEL=
  qwen3.8:27b-agent` (ctx 40K) dhe ri-mato; dokumento dallimin.
- Verifiko me `ollama show` se cili `num_ctx` shërbehet realisht për
  `qwen3.8:27b` (default i Ollama-s mund të jetë < max i modelit).

### (c) Kalimi në `local`

VETËM pasi (a)+(b) kalojnë:
1. `git checkout` i pastër; ndrysho `PROFILES["DE"].llm_provider = "local"`
   te `backend/app/jurisdictions.py`.
2. Regression: `backend/scripts/de_simulation.py` (15 kontrolle E2E).
3. Commit + përditëso DE-LAUNCH-GATE.md item 3 → "mbyllur" me datë + numra.
4. Rollback (nëse diçka dështon): `git revert` i jurisdictions.py — DeepSeek
   rikthehet; asnjë e dhënë nuk humbet.

## Seti i testeve (referencë)

- Retrieval: `backend/scripts/eval_de_recherche.py` — **baseline i matur
  2026-08-18: NL 9/14 (64%), citime 3/6 (50%)** (nuk ndryshon me swap-in e LLM —
  embeddings/FTS të pandryshuara; mbahet si gate regresioni, jo kriter kalimi).
- Cilësi përgjigjesh: skript i ri `eval_de_quality.py` (i ngjashëm me
  eval_de_recherche, por me `LocalProvider.chat` në vend të retrieval-it të
  vetëm) — të 20 pyetjet, me output tabelë + përmbledhje kundrejt kritereve.

## Hapat e ekzekutimit (kur të miratohet)

1. Shkruaj `backend/scripts/eval_de_quality.py` (RAG + LocalProvider, matje
   tokens, verifikim statute-sh kundrejt DB).
2. Xhiro kundrejt `qwen3.8:27b`; mblidh numrat kundrejt kritereve (a)+(b).
3. Nëse >4K tokena RAG → ri-xhiro me `qwen3.8:27b-agent`; krahaso.
4. Nëse kalon: (c) flip + de_simulation + commit + mbyll item 3.
5. Raporto numrat te JOURNAL + STATE; njofto pronarin.

## Rreziku / siguria

- Asnjë shkrim në Gmail/DB/data të AvokatIM gjatë (a)/(b) — vetëm lexim + thirrje
  LLM lokale.
- (c) është ndryshim konfigurimi i kthyeshëm (git revert); DE është demo e
  mbyllur, jo publike.
- Nëse qwen3.8:27b dështon kriteret → mbetet DeepSeek, item 3 i hapur,
  alternativat (qwen3.8:27b-agent, tuning prompt) dokumentohen.
