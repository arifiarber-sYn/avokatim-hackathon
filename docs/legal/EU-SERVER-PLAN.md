# Plani i serverit në BE + përfaqësuesi Art. 27 (porta DE, itemet 1–2)

> ⛔ **PAUZË (2026-09-24, urdhër i Klloshës):** traka DE e AvokatIM u pauzua —
> vazhdon vetëm XK. **MOS blej / MOS provizionoj asgjë nga ky plan** pa PO të ri
> të Klloshës. Plani + numrat mbeten të vlefshëm për rifillim (rekomandimi i
> Halimit 23.09 qëndron i regjistruar). Detajet: `DE-LAUNCH-GATE.md` §PAUZË.

> Dokument vendimmarrës për pronarin, i përgatitur 2026-09-01 (çmimet e
> verifikuara në ueb po atë ditë, pa TVSH). Zbatimin teknik e kryen agjenti
> sapo të vendosësh; këtu s'ka asgjë të nisur.

## Pse tani

- **Porta DE item 1**: të dhënat e qytetarëve gjermanë duhen në server BE
  (GDPR Art. 3(2)); "Serverstandort Deutschland" është edhe argument shitjeje.
- **Porta DE item 2**: si ofrues jashtë BE-së na duhet përfaqësues Art. 27
  pavarësisht se ku është serveri.
- **Lidhja me item 3 (latenca e LLM-së lokale)**: matja e re me streaming
  (2026-09-01, `scripts/eval_de_ttft.py`, 20 pyetje, me warmup) dha
  **TTFT p50 = 2.47s, p95 = 6.64s** (17/20 nën 5s) kundrejt 12.71s të
  metrikës së vjetër "përgjigje e plotë". Outliers-at (11.5s, 6.4s) vijnë
  nga GPU e përbashkët e kësaj makine (Ollama + embeddings + gjithçka
  tjetër). **Në një server GPU të dedikuar item 3 pritet të mbyllet vetiu**
  — pra itemet 1 dhe 3 zgjidhen me të njëjtin blerje.

## Opsioni A (rekomandimi): Hetzner GEX44 — 184 €/muaj

| | GEX44 | GEX130 | GEX131 |
|---|---|---|---|
| GPU | RTX 4000 SFF Ada, **20 GB** | RTX 6000 Ada, **48 GB** | Blackwell Max-Q, **96 GB** |
| CPU / RAM | i5-13500 / 64 GB | Xeon 5412U / 128 GB ECC | Xeon 5412U / 256 GB ECC |
| Disk | 2×1.92 TB NVMe RAID1 | 2×1.92 TB NVMe RAID1 | 2×960 GB NVMe RAID1 |
| Çmimi/muaj | **184 €** | 838 € | 889 € |
| Setup (një herë) | 79 € | 79 € | 79 € |
| Lokacioni | Falkenstein/Nürnberg (DE) | DE | DE/FI |

- Modeli aktual DE (`qwen3-abliterated:30b-a3b`, Q4, 18 GB pesha) servohet
  sot me ctx 40960 → 22.5 GB VRAM. **Në GEX44 (20 GB) futet me ctx 16384**
  — mjafton bollshëm: pas riindeksimit (2026-08-26) prompt-i maksimal i
  eval-it është ~1.850 tokena, buxheti 80% i ctx 16K = 13.1K.
  GEX130 jep hapësirë për modele më të mëdha + embeddings në GPU, por 4.5×
  çmimi — merret më vonë po u desh, migrimi Hetzner→Hetzner është trivial.
- Hetzner: gjermane, ISO 27001, trafik i pakufizuar 1 Gbit/s, IPMI,
  rrymë e gjelbër — kutia e duhur për "Serverstandort Deutschland".
- Alternativat e shqyrtuara: OVH/Scaleway (FR, GPU me orë, më shtrenjtë
  për 24/7), AWS g5.xlarge (~734 $/muaj — 4× GEX44), Hostline (LT,
  360 €/muaj) — asnjëra s'e rrah GEX44 për çmim/performancë në DE.

## Përfaqësuesi Art. 27 (item 2)

| Ofruesi | Çmimi | Shënim |
|---|---|---|
| **Prighter (AT) — rekomandimi** | **35 €/muaj (420 €/vit)** tier "Growth" | çmim publik, onboarding vetëshërbyes, PoA e thjeshtë, i njohur në treg |
| Engage Compliance (NL) | nga 59 €/muaj | standalone |
| rep4eu | nga 29 €/muaj | më i lirë, më pak i njohur |
| DataRep (IE) | tier-e sipas vëllimit | mbulon edhe UK/CH po u deshën |

- Emri + adresa e përfaqësuesit shtohet te Datenschutzerklärung dhe
  Impressum (bashkohet me rishikimin e item 4).

## Plani i migrimit (кur të japësh PO)

1. **Provizionimi** (dita 1): porosit GEX44, Ubuntu LTS, hardening
   (ufw, fail2ban, ssh-key-only), Docker + docker-compose, Ollama me
   `OLLAMA_KEEP_ALIVE=-1` (pa cold-start) + `num_ctx=16384`.
2. **Ngritja e stack-ut** (dita 1–2): klonimi i repo-s, `backend/.env` i ri
   (çelësa të rinj DB/enkriptimi), containers (Postgres+pgvector, Redis,
   Caddy, LiveKit, Umami), modeli LLM + embeddings lokalë.
3. **Prova e restore-it** (dita 2): backup-i i enkriptuar ditor
   (`~/AvokatIMBackups`) restaurohet në serverin e ri — kjo është njëherësh
   edhe testi i planit të backup-it. Të dhënat e dokumenteve (`data/`)
   sinkronizohen me rsync mbi ssh.
4. **Vlerësimi** (dita 2): `eval_de_quality.py` + `eval_de_ttft.py` në
   serverin e ri — pritet p95 TTFT ≪ 5s pa outliers të GPU-së së ndarë;
   nëse kalon, **item 3 mbyllet** dhe `PROFILES["DE"].llm_provider="local"`
   rikthehet.
5. **Cutover** (< 1 orë, natën): sinkronizim final DB + `data/`, tuneli
   Cloudflare i ri në serverin e ri (fillimisht vetëm `de.avokatiim.ai`;
   `avokatiim.ai` mund të ndjekë më vonë ose të qëndrojë këtu — të dyja
   opsionet i mban arkitektura, por më e thjeshta operacionalisht është
   gjithçka në një vend). Makina aktuale mbetet dev + backup i dytë.
6. **Rollback**: tuneli kthehet te makina e vjetër me një ndryshim
   konfigurimi; deri në fshirjen e të dhënave nga serveri i vjetër (pas
   2 javësh stabilitet) rikthimi është i plotë.

## Kostoja totale e re

- GEX44 184 € + Prighter 35 € = **219 €/muaj** (+ 79 € setup një herë).
- Me GEX130: 873 €/muaj. Rekomandimi: nis me GEX44, upgrade vetëm po
  u ngushtua VRAM-i realisht.

## Çfarë pres nga ti

1. **PO/JO për GEX44 + Prighter Growth** (ose zgjedhje tjetër nga tabelat).
2. Pas PO-së: krijon llogarinë Hetzner (kërkon kartë/identitet — s'e bëj
   dot unë) dhe ma jep qasjen; onboarding-un e Prighter e nis ti me PoA.
3. Pjesa tjetër (hapat 1–6 më lart) kryhet nga agjenti dhe raportohet.
