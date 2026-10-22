# AvokatIM — deck (skeleton, 10 slide)

> Numrat këtu vijnë nga setet e matjes: i akorduar (20), held-out (13), blind (13).
> Rregull: në deck shfaqet numri i held-out/blind, jo ai i akorduar.

## 1. Problemi
1.8 milionë shqiptarë; dokumentet juridike ekzistojnë, por nuk janë të kërkueshme
në gjuhën e tyre. Avokati i parë është kërkimi në Google — dhe ai nuk citon.

## 2. Pse tani
Korpusi është i pranishëm: 3 086 dokumente shqipe (ligje, kode), 353 442 copëza të
indeksuara, 350 612 me vektor. Modeli multilingual punon lokalisht, pa cloud.

## 3. Demo në një pamje
Pyetje në shqip → përgjigje me burim → klik mbi citim → dokumenti, faqja, fragmenti.

## 4. Arkitektura
Orchestrator (plan → query → verify) mbi core-in e AvokatIM:
- Zetaris adapter — burime të fragmentuara (SQL federativ)
- Meterless adapter — model lokal + matje kostoje
- Meta Model adapter — modelet e Meta-s (track-u Meta)

## 5. Zetaris
Statusi: platforma lokale live (api :8888, ui :3011, driver, postgres).
Adapteri u provua me SELECT 1 → 200 [['1']]. Kufizim i njohur: DDL/CTAS nuk
materializohen në këtë build; federimi i vërtetë kërkon regjistrimin e datasource.

## 6. Meterless
Statusi: Nightshift nuk ka build për Linux x86_64 (vetëm Mac/Windows/DGX arm64).
Kërkesa për build/API u dërgua te partnerships@meterless.ai. Alternativa e punës:
model lokal + matje e kostos në usage.jsonl.

## 7. Citimet e verifikueshme
Çdo pohim lidhet me dokument + faqe + fragment. Pa bazë → «s'e di», me arsyen.

## 8. Matjet (të paprekura)
| Seti | Brenda | Jashtë |
|---|---|---|
| Held-out (13) | 9/10 | 3/3 |
| Blind (13) | 10/10 | 3/3 |

Shënim metodologjik: matja «brenda» kontrollon praninë e termit juridik në fragment,
jo ende saktësinë e dokumentit të parë. Matja e artefaktit të artë është hapi tjetër.

## 9. Çka vjen më pas
Meta Global AI Developer Hackathon (26.10–04.11), indie track: i njëjti core, modelet
e Meta-s, tregimi «Build for Your World».

## 10. Ekipi
Arber Arifi — solo builder; AvokatIM live në avokatiim.ai.

