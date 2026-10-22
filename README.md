# AvokatIM — agjenti që shpjegon pse

Dorezim për **Open Agent Hackathon 2026**, track **Wildcard [Tinkerer]**.

Një agjent ligjor për gjuhën shqipe që **nuk jep përgjigje pa burim**: çdo pohim vjen me
dokument, nen dhe fragment, dhe kur baza mungon thotë *"s'e di"* me arsye — në vend që të
sajojë.

## Çka është brenda

| Dosja | Çka |
|---|---|
| docs/hackathon/submission.md | përshkrimi i dorezimit |
| docs/hackathon/deck.pdf | 10 slide |
| docs/hackathon/video/demo-full.mp4 | demo 90 s mbi produktin real |
| docs/hackathon/arta-verifikuar.md | verifikimi i 10 përgjigjeve, raund pas raundi |
| backend/hackathon/ | harness 3 sete + demo CLI |
| backend/app/adapters/ | Zetaris, Meterless, Meta Model — kontrata + teste |

## Numrat (të matur, jo të pretenduar)

**Kërkimi** — set blind 13 pyetje: 10/10 brenda korpusit, 3/3 refuzuar jashtë domenit.

**Përgjigjja** — 10 pyetje-etalon, verifikim mbi titullin dhe tekstin e nenit:

| Matja | Numri |
|---|---|
| Ligji i saktë në vendin e parë | 10/10 |
| Nen i saktë dhe i plotë | 2/10 |
| Neni i duhur brenda top-3 | 7/10 |
| Burim i gabuar në krye | 0/10 |

Kufiri i deklaruar hapur: sistemi gjen ligjin e duhur pothuajse gjithmonë, por nuk zgjedh
gjithmonë nenin që përgjigjet. Kjo matet dhe shkruhet, nuk fshihet pas një mesatareje.

## Si ekzekutohet

Kërkon PostgreSQL me pgvector dhe korpusin ligjor (nuk shpërndahet — përmban të dhëna
reale). Pa korpusin, harness-i shërben si kontratë dhe si dokumentim i metodës.

    export AVOKATIM_DSN="postgresql://user:pass@127.0.0.1:5433/avokatim"
    python backend/hackathon/harness_v5.py
    python backend/hackathon/demo.py "Çfarë duhet të përmbajë kontrata e punës?"

## Sponsoret

- **Zetaris** — adapter live ndaj REST SQL editor; SELECT 1 → 200. Federimi i korpusit
  kërkon regjistrim datasource në UI; deklarohet si hap i mbetur, jo si i kryer.
- **Meterless** — adapter + usage.jsonl për kosto/tokens. Nightshift-i nativ nuk ka build
  për Linux x86_64; kërkesa për build/API është dërguar. Nuk pretendohet integrim i plotë.

## Licenca

Kodi i këtij dorezimi: MIT. Korpusi ligjor dhe të dhënat e klientëve nuk përfshihen.
