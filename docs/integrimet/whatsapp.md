# Ava në WhatsApp — udhëzues aktivizimi

> Kodi është gati dhe i testuar si stub (2026-07-13). Për ta ndezur duhet
> vetëm një llogari Meta WhatsApp Business Cloud API dhe një numër biznesi.
> Pa kredenciale, webhook-u pranon mesazhe por vetëm i loggon — s'dërgon asgjë.

## Si funksionon

- Qytetari i shkruan numrit të biznesit në WhatsApp.
- Meta e dërgon mesazhin te `POST /api/public/whatsapp/webhook`.
- Backend-i e pyet Ava-n (RAG mbi korpusin ligjor XK, i njëjti tubacion si
  /ava në web) dhe përgjigjet përmes Graph API.
- Kufiri: 20 pyetje/ditë për numër telefoni (`whatsapp_daily_limit`).

## Hapat e aktivizimit (pronari)

1. **Llogaria Meta**: https://developers.facebook.com → krijo një App
   (tipi "Business") → shto produktin **WhatsApp**.
2. **Numri**: në WhatsApp → API Setup merr `Phone number ID` (test-numri
   funksionon menjëherë; për prodhim regjistro numrin e biznesit — duhet
   verifikim biznesi te Meta, zakonisht disa ditë).
3. **Token**: gjenero një **permanent access token** (System User me lejen
   `whatsapp_business_messaging`), jo token-in 24-orësh të testit.
4. **backend/.env** — shto:
   ```
   WHATSAPP_TOKEN=<permanent token>
   WHATSAPP_PHONE_ID=<phone number id>
   WHATSAPP_VERIFY_TOKEN=<çfarëdo stringu të rastësishëm — e zgjedh ti>
   ```
   dhe `systemctl --user restart avokatim`.
5. **Webhook** në panelin e Meta-s (WhatsApp → Configuration):
   - Callback URL: `https://avokatiim.ai/api/public/whatsapp/webhook`
   - Verify token: i njëjti si `WHATSAPP_VERIFY_TOKEN`
   - Subscribe në fushën **messages**.
   Meta bën `GET` me `hub.challenge` — backend-i e kthen automatikisht.
6. **Testi**: dërgo "A kam të drejtë në pushim vjetor?" nga një telefon —
   Ava duhet të përgjigjet brenda disa sekondash.

## Kufizime të njohura

- Meta lejon përgjigje falas vetëm brenda **24 orëve** nga mesazhi i fundit
  i përdoruesit (customer service window) — mjafton për pyetje-përgjigje.
- Mesazhet e para nga biznesi (jashtë dritares) kërkojnë template të
  aprovuara — nuk i përdorim fare.
- Çmimi: conversation-based pricing e Meta-s; pyetjet hyrëse + përgjigjet
  brenda dritares 24h janë kategoria "service" (falas deri në 1000/muaj).
