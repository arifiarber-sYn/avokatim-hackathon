# Pagesat me kartelë përmes Raiffeisen Bank Kosovo

> Udhëzues për pronarin. Pjesa teknike në kod është gati (skeleti i adapterit
> në `backend/app/services/payments.py`); mbetet vetëm aplikimi në bankë dhe
> plotësimi i kredencialeve në `backend/.env`.

## Pse Raiffeisen

Stripe **nuk** i pranon bizneset e regjistruara në Kosovë. Rruga reale për
pranimin e kartelave (Visa/Mastercard, Apple Pay, Google Pay) është një
gateway lokal — Raiffeisen Bank Kosovo (RBKO) e ofron shërbimin e-commerce
më të përdorur, alternativa është TEB.

Deri atëherë sistemi punon me dy rrugë që funksionojnë **që sot**:

1. **Transfer bankar** — detajet e llogarisë printohen në email-in e faturës
   (`platform_bank_details` në `.env`).
2. **Link manual pagese** — çdo avokat me llogari biznesi që ka Pay-By-Link
   nga banka e vet mund ta ngjisë URL-në direkt te fatura
   (butoni "Ngjit link pagese" në faqen e faturimit).

## Hapat e aplikimit (i kryen pronari, jo agjenti)

1. **Llogari biznesi në RBKO** — nëse s'ka, hapet me certifikatën e biznesit
   (ARBK), ID dhe kontratën e qirasë/adresën e zyrës.
2. **Aplikimi për e-commerce merchant** — në degë ose te menaxheri i biznesit
   kërkohet "shërbimi e-commerce / virtual POS". Dokumentet e zakonshme:
   certifikata e biznesit, numri fiskal, përshkrimi i shërbimit
   (platformë SaaS për shërbime ligjore), URL-ja `https://avokatiim.ai`.
3. **Kontrata & tarifat** — banka kthen ofertën me komisionin për transaksion
   (zakonisht 1.5–2.5% + tarifë fikse). Nënshkruhet kontrata.
4. **Kredencialet teknike** — pas aktivizimit banka dërgon dokumentacionin e
   API-së të gateway-t dhe kredencialet: merchant ID, API key/secret dhe
   URL-në bazë të API-së (test + prodhim).

## Konfigurimi teknik (pasi vijnë kredencialet)

Në `backend/.env`:

```
PAYMENTS_PROVIDER=raiffeisen
RAIFFEISEN_API_BASE=https://...     # nga dokumentacioni i bankës
RAIFFEISEN_MERCHANT_ID=...
RAIFFEISEN_API_KEY=...
RAIFFEISEN_CALLBACK_SECRET=...      # sekreti i callback-ut (nëse ofrohet)
```

Pastaj:

1. Krahasohen emrat e fushave në `_raiffeisen_payment_link()` me
   dokumentacionin real të bankës dhe përshtaten (është funksioni i vetëm
   që preket).
2. Konfigurohet URL-ja e callback-ut te banka:
   `https://avokatiim.ai/api/public/stripe/webhook` do të zëvendësohet me
   një endpoint të dedikuar raiffeisen — kërkohet nga agjenti kur të vijë
   dokumentacioni.
3. Testohet në ambientin test të bankës me kartelat testuese që i jep banka.
4. Kalohet në prodhim (`RAIFFEISEN_API_BASE` e prodhimit).

## Çfarë ndodh automatikisht pas aktivizimit

- Butoni "Krijo link pagese" në faturim rishfaqet vetë (UI e lexon
  `GET /billing/payments-config`).
- Faturat e abonimeve të platformës dhe rezervimet e konsultave përdorin të
  njëjtin abstraksion — të gjitha marrin pagesa me kartelë pa asnjë ndryshim
  tjetër në kod.
