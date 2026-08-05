# OUTREACH-SENDER-SETUP — dërguesi i dedikuar për cold outreach (D-069)

> STATUS: **LIVE (2026-08-05).** Domain `mail.avokatiim.ai` i krijuar në Resend,
> DKIM+SPF+DMARC në Cloudflare, i verifikuar; fushatat në mode `resend`.
> Çelësat: `OUTREACH_RESEND_KEY`/`OUTREACH_FROM` te `infrastructure.env`;
> Cloudflare token te `~/.cloudflared/cert.pem` (vegla `~/scripts/cloudflare_dns.py`).
> Hapat e mëposhtëm mbahen për referencë/rollback ose për një domain të ri.


**Pse:** auditimi 2026-08-05 gjeti ~930 cold-emaila të dërguar nga Gmail-i
personal (`arifi.arber@gmail.com`) — i njëjti që mban verify-links të
platformës, bankën, git. Një bllokim/blacklist do t'i thyente të gjitha
njëherësh. Zgjidhja: outreach-i dërgohet nga `mail.avokatiim.ai` përmes
Resend; përgjigjet vijnë prapë te Gmail-i (Reply-To), kështu triage +
opt-out (STOP → `data/de_suppress.txt`) punojnë PA ndryshim.

**Gjendja teknike (gati në kod):**
- `backend/scripts/outreach_sender.py` — moduli i përbashkët (Resend + fallback
  Gmail SMTP). Të dy fushatat (`oak_outreach_campaign.py`,
  `de_outreach_campaign.py`) e përdorin që tani; deri sa Resend të aktivizohet
  dërgojnë si më parë (mode `smtp`).
- Warm-up i integruar: java 1 → 10/ditë, java 2 → 20/ditë, pastaj 25/ditë.

## Hapat manualë (Kllosha, ~10 min)

1. **Resend — çelës i ri full-access:**
   - Hyr te https://resend.com (llogaria ekzistuese — OpsHub e përdor tashmë).
   - API Keys → Create → *Full access*. (Çelësi aktual `RESEND_API_KEY` te
     `infrastructure.env` është I PAVLEFSHËM — provuar 2026-08-05; ai i
     OpsHub-it është send-only dhe s'menaxhon dot domain-e.)
   - Shtoje te `~/.openclaw/workspace/secrets/infrastructure.env`:
     ```
     OUTREACH_RESEND_KEY=re_...
     ```

2. **Krijo domain-in në Resend** (Halimi mund ta bëjë sapo të ketë çelësin):
   ```
   cd ~/AvokatIM/backend && .venv/bin/python scripts/outreach_sender.py --setup mail.avokatiim.ai
   ```
   Kjo printon rekordet DNS (SPF TXT + DKIM + MX bounce).

3. **Cloudflare — shto rekordet DNS** (zona `avokatiim.ai` është në
   Cloudflare; s'kemi API token, prandaj dashboard):
   - dash.cloudflare.com → avokatiim.ai → DNS → shto rekordet nga hapi 2,
     të gjitha **DNS only** (re portokalli OFF).
   - (Rekomandim) shto edhe DMARC:
     `TXT _dmarc.mail.avokatiim.ai` → `v=DMARC1; p=quarantine; rua=mailto:arifi.arber@gmail.com`

4. **Verifiko + aktivizo:**
   ```
   .venv/bin/python scripts/outreach_sender.py --status     # prit status=verified
   ```
   Pastaj te `infrastructure.env` shto:
   ```
   OUTREACH_FROM=Arbër Arifi <arber@mail.avokatiim.ai>
   OUTREACH_WARMUP_START=<data e sotme YYYY-MM-DD>
   ```
   Testo: `.venv/bin/python scripts/outreach_sender.py --test arifi.arber@gmail.com`

5. **Gati.** Run-i i ardhshëm i `avokatim-outreach.timer` kalon vetvetiu në
   mode `resend` me warm-up cap. Asgjë tjetër s'ka nevojë të ndryshohet.

## Verifikim pas kalimit
- `oak_outreach_campaign.py --dry-run` duhet të tregojë `mode: resend`.
- Java e parë: kontrollo bounce-t në Resend dashboard (Emails → statuset).
  Bounce rate > 5% → NDALO fushatën (`halim_guard.py halt "bounce spike"`).
