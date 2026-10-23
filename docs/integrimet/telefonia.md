# Telefonia-KI me sipgate (D-059 F4)

Ava u përgjigjet thirrjeve telefonike 24/7: merr përshkrimin e rastit,
bën deri në 3 pyetje sipas fushës (të njëjtat si në web/WhatsApp), krijon
`CaseRequest` dhe njofton avokatët përkatës. Gjithë zëri (STT/TTS) mbetet
lokal në këtë makinë; vetëm klasifikimi kalon te LLM-ja (i pseudonimizuar).

## Arkitektura

```
Telefonuesi → sipgate (SIP trunk) → Asterisk (docker, profile "telephony")
    → AudioSocket TCP 127.0.0.1:4573 → phone_gateway.py (backend)
    → faster-whisper (STT) → makina e intake-ut → Piper (TTS) → Asterisk
```

- `infra/asterisk/` — pjsip-template + dialplan + entrypoint.
- `backend/app/services/phone_gateway.py` — serveri AudioSocket + dialogu.
- `GET /api/public/phone/link` — dialplan-i lidh numrin e thirrësit me
  UUID-in e thirrjes (vetëm loopback).
- Gjuha zgjidhet nga prefiksi i numrit (+49 → de, +383 → sq), si në WhatsApp.

## Veprimet e pronarit (një herë)

1. Hap llogari në [sipgate](https://www.sipgate.de) (basic/trunking) dhe
   bli një numër gjerman (~1–3 €/muaj + çmim për minutë).
2. Te sipgate: krijo pajisjen SIP (VoIP-Telefon / Trunk) dhe merr:
   - SIP-ID (user), SIP-Passwort, host (`sipgate.de`).
3. Në `backend/.env` shto:

   ```
   PHONE_GATEWAY_ENABLED=true
   SIPGATE_SIP_USER=<SIP-ID>
   SIPGATE_SIP_PASSWORD=<SIP-Passwort>
   ```

4. Nis Asterisk-un dhe ristarto stack-un:

   ```bash
   cd ~/BoraLaw
   set -a; source backend/.env; set +a
   docker compose --profile telephony up -d asterisk
   systemctl --user restart avokatim
   ```

5. Verifikimi: `docker logs avokatim-asterisk` duhet të tregojë regjistrim
   të suksesshëm te sipgate; `data/backend.log` duhet të ketë
   "Phone gateway (AudioSocket) listening". Pastaj thirr numrin real.
6. Vendos numrin te profili i vendit (`backend/app/jurisdictions.py`,
   fusha `phone_number` e profilit DE) që të shfaqet publikisht, dhe
   përditëso marketingun (pas verifikimit real — jo më parë).

## Shënime

- Pa kredenciale, kontejneri Asterisk refuzon të niset (entrypoint-i del
  me gabim) dhe backend-i nuk hap portën 4573 (`PHONE_GATEWAY_ENABLED`
  default `false`) — gjithçka e sigurt në gjendjen e paporositur.
- M1 (regjistrim + intake) dhe M2 (dialog me radhë me VAD energjie) janë
  të dyja në `phone_gateway.py`; pyetjet vijnë nga i njëjti seed si
  web/WhatsApp (`case_intake_questions.py`).
- Telefonuesit pa email regjistrohen me adresë placeholder
  (`tel-<numri>@phone.invalid`) — avokati i telefonon mbrapsht.
