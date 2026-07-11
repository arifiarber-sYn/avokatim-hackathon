# AvokatIM

Platformë moderne për menaxhimin e praktikës ligjore — e ndërtuar që një avokat i vetëm
të punojë me kapacitetin e një zyre të tërë: nga pranimi i lëndës deri te përgatitja për seancë.

## Modulet

| Moduli | Çfarë bën |
|---|---|
| **Pranimi (Intake)** | Regjistrim i rasteve të reja, kontroll automatik i konfliktit të interesit, klasifikim me AI |
| **Dosjet (Matters)** | Dosja digjitale e lëndës: palët, dokumentet, afatet, shënimet, historia |
| **Afatet** | Motor afatesh me rregullat procedurale të Kosovës (LPK, KPPRK, LKA...) — llogaritje automatike me festa zyrtare |
| **Dokumentet** | Ruajtje e enkriptuar, versionim, nxjerrje teksti + OCR, indeksim për kërkim semantik |
| **Shabllonet** | Padi, ankesa, autorizime — plotësohen automatikisht me të dhënat e lëndës |
| **Asistentja Ava** | AI me RAG mbi legjislacionin dhe dokumentet e lëndës: përmbledhje, hulumtim me citime, përgatitje për seancë |
| **Portali i klientit** | Klienti sheh statusin e lëndës dhe seancat e ardhshme |
| **Faturimi** | Orët e punës, fatura automatike nga orët e pafaturuara |
| **Paneli** | Ngarkesa, afatet e javës, financat |

## Arkitektura

- **Backend**: Python / FastAPI, SQLAlchemy (async), Alembic — `backend/`
- **Databaza**: PostgreSQL 17 + pgvector (kërkim semantik), Redis — në Docker
- **Frontend**: Next.js + TypeScript + Tailwind, 3 gjuhë (shqip / anglisht / kinezisht) — `frontend/`
- **AI**: shtresë abstraksioni LLM — DeepSeek V4 (API) sot, LLM lokal (Ollama/vLLM) si opsion
- **Embeddings**: lokale (sentence-transformers, multilingual) — teksti i dokumenteve NUK del nga ky kompjuter për indeksim
- **Qasja nga jashtë**: Caddy me HTTPS në portin 8443
- **Siguria**: 2FA (TOTP), JWT, enkriptim i dokumenteve në disk, audit log i plotë

Multi-juridiksional që nga themeli: rregullat e afateve, festat, shabllonet dhe korpusi ligjor
janë **të dhëna për juridiksion** (XK aktiv; GB, CN, INTL të përgatitura), jo kod.

## Nisja

```bash
./start.sh
```

Hap `http://127.0.0.1:3000` — hera e parë të kërkon të krijosh llogarinë e avokatit.

Nga rrjeti / jashtë: `https://<IP-e-këtij-kompjuteri>:8443` (certifikatë lokale — prano
paralajmërimin e shfletuesit; me domen publik Caddy merr certifikatë të vërtetë vetë).

Ndalja: `./stop.sh`

## Konfigurimi

Sekretet janë te `backend/.env` (çelësi DeepSeek, çelësi i enkriptimit të dokumenteve,
fjalëkalimi i DB). **Mos e vendos kurrë në git.**

Opsionale:

```bash
# Embeddings lokale + OCR (të instaluara tashmë në .venv)
backend/.venv/bin/pip install -r backend/requirements-ai.txt
# OCR kërkon edhe binarin e sistemit:
sudo dnf install tesseract tesseract-langpack-sqi tesseract-langpack-eng tesseract-langpack-chi_sim
```

LLM lokal (faza 2): vendos te `backend/.env`:

```
LOCAL_LLM_BASE_URL=http://127.0.0.1:11434/v1   # Ollama
LOCAL_LLM_MODEL=emri-i-modelit
```

dhe zgjidhe "Lokal" te Asistentja në aplikacion.

## Korpusi ligjor

Te **Cilësimet → Baza ligjore** ngarko tekstet e ligjeve (nga Gazeta Zyrtare).
Ndahen automatikisht për nen ("Neni X"), indeksohen me embeddings, dhe Ava i citon
me saktësi në përgjigjet e saj.

## Testet

```bash
cd backend && .venv/bin/python -m pytest tests/ -q
```

## Struktura

```
AvokatIM/
├── backend/            # FastAPI API
│   ├── app/
│   │   ├── models/     # SQLAlchemy (multi-tenant + multi-juridiksional)
│   │   ├── api/        # REST endpoints
│   │   ├── services/   # afatet, konflikti, RAG, asistentja, storage
│   │   ├── llm/        # abstraksioni i ofruesve LLM (deepseek | local)
│   │   └── seeds/      # rregullat e afateve + festat + shabllonet e Kosovës
│   ├── alembic/        # migrimet e DB
│   └── tests/
├── frontend/           # Next.js UI (sq / en / zh)
├── data/documents/     # dokumentet e enkriptuara (jashtë git)
├── docker-compose.yml  # Postgres + Redis + Caddy
├── Caddyfile           # HTTPS reverse proxy
└── start.sh / stop.sh
```
