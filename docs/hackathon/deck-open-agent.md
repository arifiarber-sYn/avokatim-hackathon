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

## 8. Matjet — dy lloje, të dyja të paprekura

**Kërkimi** (seti blind, 13 pyetje): 10/10 brenda korpusit · 3/3 refuzuar.

**Përgjigjja** (10 pyetje, verifikim mbi titullin dhe tekstin e nenit):

| Matja | Numri |
|---|---|
| Ligji i saktë në vendin e parë | **10/10** |
| Nen i saktë dhe i plotë | 2/10 |
| Neni i duhur brenda top-3 | 7/10 |
| Burim i gabuar në krye | **0/10** |

Dallimi është thelbi: agjenti gjen ligjin e duhur pothuajse gjithmonë, por nuk zgjedh
gjithmonë nenin që përgjigjet. Këtë e themi hapur — dhe e matim, në vend që ta fshehim
pas një mesatareje.

## 9. Çka vjen më pas
Meta Global AI Developer Hackathon (26.10–04.11), indie track: i njëjti core, modelet
e Meta-s, tregimi «Build for Your World».

## 10. Ekipi
Arber Arifi — solo builder; AvokatIM live në avokatiim.ai.

