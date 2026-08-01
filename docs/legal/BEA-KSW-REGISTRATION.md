# beA / KSW-Schnittstelle — regjistrimi te BRAK (D-037 Faza 6)

> Dokument pune për pronarin. Regjistrimi është veprim i jashtëm (email +
> shkëmbim me BRAK) dhe s'varet nga kodi. Ky dokument përmban gjithçka që
> duhet për ta nisur SOT: procesin, kontaktet dhe draft-kërkesën në
> gjermanisht, gati për dërgim.

## Pse na duhet

**beA** (besonderes elektronisches Anwaltspostfach) është kutia postare
elektronike e detyrueshme e çdo avokati gjerman (§ 31a BRAO) — komunikimi
me gjykatat kalon aty. Pa integrim beA, AvokatIM DE mbetet "shtresë AI +
marketplace mbi softuerin ekzistues"; me beA bëhet zëvendësim i plotë i
RA-MICRO/Actaport për zyra të vogla.

**KSW-Schnittstelle** (Kanzleisoftware-Schnittstelle) është rruga zyrtare:
BRAK u ofron prodhuesve të softuerit të zyrave një webservice SOAP + një
toolkit opsional në Java, me të cilin softueri ynë lexon/dërgon mesazhe beA
direkt nga e-Akte.

## Çfarë dihet për procesin (verifikuar 2026-08-01)

- Qasja jepet **pas një verifikimi të "berechtigtes Interesse"** (interesit
  legjitim si prodhues softueri zyrash) **dhe një regjistrimi** te BRAK, ku
  shkëmbehen informacionet e prodhuesit për pjesëmarrje në ERV
  (elektronischer Rechtsverkehr).
- Teknikisht: webservice **SOAP** i siguruar me TLS + **SSL-Client-
  Authentifizierung** — certifikata e klientit konfigurohet në shkëmbim
  direkt mes beA-Betrieb dhe prodhuesit.
- Dokumentacioni që merret pas regjistrimit: online-help + manual integrimi
  + use cases, **WSDL e komentuar**, **KSW-Toolkit (librari Java) me
  Javadoc dhe kod burimor**, si dhe një **testsuite** me raste standarde.
- Ekziston **KSW-Support** i dedikuar për prodhuesit (zhvillim + operim).
- Prodhuesit e regjistruar detyrohen të mbulojnë vetë suportin e
  përdoruesve të tyre (ne e bëjmë tashmë).

## Kontaktet

| Kanal | Vlera |
|---|---|
| Faqja për prodhuesit | https://bea.brak.de/ksw-schnittstelle/ (histrorikisht; nëse s'hapet, nis nga portal.beasupport.de) |
| Portali i suportit beA | https://portal.beasupport.de (Supportwegweiser → KSW) |
| Servicedesk beA | servicedesk@beasupport.de · +49 30 21787017 (Hë–Pr 8–20) |
| BRAK Büro Berlin | Littenstraße 9, 10179 Berlin · +49 30 284939-0 |

## Hapat për pronarin (nis menjëherë)

1. Dërgo draft-emailin më poshtë te **servicedesk@beasupport.de** (me CC
   opsionale te zyra e BRAK) — kërko rrugën formale të regjistrimit si
   KSW-Hersteller dhe qasjen në mjedisin e testit.
2. Kur BRAK të kthejë formularët: plotëso të dhënat e prodhuesit
   (emri i kompanisë, adresa, kontakti teknik, produkti "AvokatIM").
3. Shkëmbimi teknik: gjenerojmë CSR për certifikatën SSL-client
   (e bëjmë ne në kod kur të arrijë ky hap).
4. Pas qasjes në testumgebung nis zhvillimi i modulit (shih më poshtë).

## Draft-emaili (gjermanisht, gati për dërgim)

> **An:** servicedesk@beasupport.de
> **Betreff:** Registrierung als Kanzleisoftware-Hersteller — Zugang zur KSW-Schnittstelle
>
> Sehr geehrte Damen und Herren,
>
> wir entwickeln die Kanzleisoftware **AvokatIM** (https://de.avokatiim.ai) —
> eine cloudbasierte Praxisverwaltung mit elektronischer Akte,
> Fristenberechnung, RVG-Vergütungsrechner, E-Rechnung (ZUGFeRD/XRechnung)
> und DATEV-Export, gerichtet an kleine Kanzleien und Einzelanwälte in
> Deutschland.
>
> Wir möchten das besondere elektronische Anwaltspostfach (beA) über die
> Kanzleisoftware-Schnittstelle (KSW-Schnittstelle) in unser Produkt
> integrieren, damit unsere Nutzerinnen und Nutzer ihre beA-Nachrichten
> direkt aus der elektronischen Akte empfangen und versenden können.
>
> Wir bitten Sie daher um Informationen zum Registrierungsverfahren als
> Kanzleisoftware-Hersteller, insbesondere:
>
> 1. die erforderlichen Unterlagen bzw. Formulare für die Registrierung
>    und die Prüfung des berechtigten Interesses,
> 2. den Zugang zur Schnittstellendokumentation (WSDL, KSW-Toolkit,
>    Testsuite) und
> 3. den Zugang zur Testumgebung sowie das Verfahren zur Einrichtung der
>    SSL-Client-Authentifizierung.
>
> Technischer Ansprechpartner: [EMRI I PRONARIT], [EMAIL], [TELEFON].
>
> Vielen Dank im Voraus und mit freundlichen Grüßen
>
> [EMRI]
> [KOMPANIA / ADRESA]

## Arkitektura e planifikuar e modulit (pas qasjes)

- `backend/app/services/bea/` — klient i KSW-Webservice. Meqë toolkit-i
  zyrtar është **librari Java** (mbulon kriptografinë e mesazheve, që s'ka
  kuptim të riimplementohet në Python), arkitektura e synuar:
  **sidecar i vogël Java** që mbështjell KSW-Toolkit dhe ekspozon REST të
  brendshëm (vetëm localhost) → shërbimi Python e thërret atë.
- Sinkronizimi: inbox/outbox i beA lidhen me lëndët në e-Akte (ruajtje e
  enkriptuar në `data/`, shënim në audit log si çdo veprim tjetër).
- Rrjedha e nënshkrimit (qeS/Fernsignatur) dhe UI e inbox-it te lënda vijnë
  pas MVP-së së leximit/dërgimit.
- Deri atëherë pozicionimi DE mbetet: shtresë AI + marketplace mbi
  softuerin ekzistues të zyrës.

## Statusi

- [ ] Emaili i regjistrimit i dërguar te BRAK/beA-Servicedesk — **pronari**
- [ ] Formularët e regjistrimit të plotësuar e kthyer — **pronari**
- [ ] Qasja në dokumentacion + testumgebung e marrë
- [ ] CSR / SSL-client-cert i konfiguruar me beA-Betrieb
- [ ] Zhvillimi i modulit `services/bea/` (fillon pas qasjes)
