# Outlook add-in: "Ruaje emailin në lëndë" (D-059 F8)

Avokatët që jetojnë në Outlook (praktikisht çdo zyrë gjermane) e ruajnë
emailin + bashkëngjitjet direkt në lëndën përkatëse pa e lëshuar Outlook-un:

- Trupi i emailit bëhet **shënim** i lëndës (me subjekt/dërgues/datë).
- Bashkëngjitjet kalojnë përmes pipeline-it standard të dokumenteve
  (enkriptim → OCR → indeksim → skanimi i afateve), kategoria
  `correspondence`.
- Endpoint: `POST /api/matters/{id}/import-email` (i autentikuar, i audituar
  si `matter.import_email`).

## Përbërësit

| Pjesa | Vendi |
|---|---|
| Manifest | `frontend/public/outlook-manifest.xml` → `https://avokatiim.ai/outlook-manifest.xml` |
| Taskpane | `frontend/src/app/outlook/page.tsx` → `https://avokatiim.ai/outlook` |
| CSP | Përjashtim i shënjestruar vetëm për `/outlook` në `frontend/src/proxy.ts` (Office.js nga CDN-ja e Microsoft-it + frame-ancestors për Outlook) |
| Backend | `POST /matters/{id}/import-email` në `backend/app/api/documents.py` |

## Instalimi (sideload) — për çdo avokat/zyrë

**Outlook on the web / New Outlook:**
1. Hap një email → ⋯ (More actions) → **Get add-ins** → **My add-ins**.
2. Te *Custom Addins* → **Add a custom add-in** → **Add from URL…**
3. Vendos: `https://avokatiim.ai/outlook-manifest.xml` → Install.

**Outlook klasik (Windows):** File → Manage Add-ins (hap web-in) → si më lart.

Pas instalimit: hap një email → butoni **"Ruaje në lëndë"** → kyçu një herë
me llogarinë e AvokatIM → zgjidh lëndën → **Ruaje emailin**.

## Shënime

- Llogaritë me 2FA: kyçu një herë në aplikacionin normal në të njëjtin
  shfletues — taskpane-i e ndan token-in (localStorage i të njëjtit origin).
- Për zyrat gjermane përdoret i njëjti manifest; nëse duan brand-in
  "Ava Legal" në listën e add-in-eve, kopjo manifestin, zëvendëso
  `avokatiim.ai` me `de.avokatiim.ai` (AppDomains i ka të dyja) dhe
  etiketat gjermane janë tashmë në `<Override Locale="de-DE">`.
- Publikimi në AppSource (pa sideload) është hap i mëvonshëm — kërkon
  llogari partneri Microsoft dhe proces certifikimi.
