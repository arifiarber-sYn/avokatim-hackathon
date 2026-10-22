# Submission — Open Agent Hackathon 2026

Track: Wildcard [Tinkerer]
Deadline: 27.10.2026, 23:45 UTC
Repo: github.com/<llogaria>/AvokatIM (dega hackathon/open-agent-2026)

## Titulli
AvokatIM — agjenti që shpjegon pse

## Përshkrim i shkurtër (fushë platforme)
Një agjent ligjor për shqipen që nuk jep përgjigje pa burim: çdo pohim vjen me dokument,
nen dhe fragment të klikueshëm, dhe kur baza mungon thotë "s'e di" me arsye.

## Përshkrim i gjatë
AvokatIM është produkt live për tregun kosovar. Për këtë garë u ndërtua shtresa që e bën
përgjigjen të verifikueshme dhe të matshme:

1. Kërkim vektor mbi 353 442 fragmente (350 612 me embeddings 384-dim), i kufizuar
   automatikisht në gjuhën e pyetjes — pa këtë, korpusi gjerman (16 906 dokumente)
   dominon mbi atë shqip (3 086).
2. Rirenditje hibride: 50 kandidatë vektor + bonus për termat juridikë + preferencë
   për burime primare (ligj/kod) ndaj vendimeve.
3. Portë domeni: pyetjet jashtë juridik refuzohen me arsye, në vend që të kthejnë
   fragmente të rastësishme.
4. Matje e përsëritshme: tri sete pyetjesh (20 + 13 + 13), dy prej tyre të paprekura
   gjatë zhvillimit.

## Si u integrua Zetaris
Adapteri (backend/app/adapters/zetaris.py) flet me REST SQL editor të platformës lokale:
POST /api/v1.0/sql-editor/sqls/run me Bearer + X-Org-ID + X-Request-ID dhe body
{queryId, sql, source, limit}. Provuar live: SELECT 1 -> 200, data [['1']];
SELECT current_database() -> [['default']].

Kufizim i deklaruar: në këtë build DDL/CTAS nuk materializohen (CREATE TABLE kthehet
spektër, SELECT pastaj "Not exist"), prandaj federimi i korpusit kërkon regjistrimin e
datasource përmes UI-së së platformës. Puna e re është kontrata e adapterit dhe rruga e
pyetjes; lidhja e burimit mbetet hapi i radhës dhe nuk pretendohet si e kryer.

## Si u integrua Meterless
Adapteri (backend/app/adapters/meterless.py) dërgon kërkesat te një hotspot lokal dhe
shkruan një rresht për çdo thirrje në usage.jsonl (job_id, model, tokens_in, tokens_out,
ms, ok, ts), që UI-ja të tregojë koston e përgjigjes.

Kufizim i deklaruar: Nightshift-i nativ ekziston vetëm për Mac, Windows dhe DGX Spark
(arm64); kjo makinë është x86_64 dhe skripti zyrtar e refuzon. Kërkesë për build ose
endpoint API u dërgua te partnerships@meterless.ai më 22.10. Deri atëherë adapteri mbetet
kontratë e provuar me teste, jo pretendim i integrimit të plotë.

## Ku hyn Cursor
Cursor u përdor nga pronari i projektit si mjet zhvillimi gjatë punës; nuk është pjesë e
runtime-it dhe as e dorëzimit. Nuk pretendohet si veçori e produktit.

## Ku hyn NVIDIA
Inferenca bëhet lokalisht në makinën e zhvilluesit; nuk përdoret SDK specifik i NVIDIA në
kodin e dorëzuar. Nëse kjo ndryshon (p.sh. Nemotron përmes partnerit), do të deklarohet.

## Stack
Python 3.14, Postgres + pgvector, sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2),
FastAPI (core-i i AvokatIM), ffmpeg + Piper (video demo), httpx (adapterat).

## Përputhja me vlerësimin (100)
- Impact 30: 1.8M folës, akses juridik në gjuhën amtare; produkt live.
- Technical 20: vektor + hibrid + portë domeni + adaptera me kontratë + 8 teste.
- Innovation 15: "s'e di" e matur si veçori, jo si defekt.
- Demo 15: video 58 s me output real, pa pamje të inskenuara.
- Product & UX 10: citim i klikueshëm, kosto e dukshme, refuzim i qartë.
- Sponsor tech 10: Zetaris live (SELECT 1) + adapter; Meterless adapter + matje.

## Asetet
| Aseti | Rruga | Statusi |
|---|---|---|
| Video | docs/hackathon/video/demo-full.mp4 | 58 s, 1080p |
| Deck | docs/hackathon/deck-open-agent.md | skeleton + numrat |
| README | docs/hackathon/README-dorëzimi.md | gati |
| Fletë verifikimi | docs/hackathon/arta-per-verifikim.md | pret PO-të |
| Harness | backend/hackathon/harness_v5.py | 3 sete |
| Adaptera | backend/app/adapters/* | 8 teste |

## Para se të dorëzohet
- [ ] Video të zgjerohet në 90-120 s (kërkesa 1-4 min)
- [ ] Deck-u të kthehet në PDF/PPTX
- [ ] Repo publik ose i ndarë me jurinë
- [ ] Përgjigjet-arta të verifikohen
- [ ] Datasource i Zetaris (nëse arrihet para afatit)
