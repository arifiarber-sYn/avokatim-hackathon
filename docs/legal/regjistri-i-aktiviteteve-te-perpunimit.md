# Regjistri i Aktiviteteve të Përpunimit (RoPA)

*Sipas nenit 30 të Ligjit Nr. 06/L-082. Mbahet nga zyra ligjore si
kontrollues; përditësohet kur shtohen kategori të reja përpunimi.*

**Kontrolluesi:** [Emri i zyrës ligjore, adresa, kontakti]
**Përpunuesi kryesor:** Operatori i platformës AvokatIM (sipas DPA-së)

| # | Aktiviteti | Qëllimi | Kategoritë e subjekteve | Kategoritë e të dhënave | Baza ligjore | Marrësit | Transferim jashtë XK | Afati i ruajtjes | Masat e sigurisë |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Menaxhimi i lëndëve | Përfaqësim ligjor | Klientë, palë kundërshtare, dëshmitarë | Identifikuese, të lëndës, të ndjeshme kur relevante | Kontrata; detyrimi ligjor; interesi legjitim | Gjykatat, organet publike | Jo | Sipas cilësimit të retention-it (parazgjedhje 10 vjet pas mbylljes) | Enkriptim në disk, qasje me role, audit log |
| 2 | Faturimi dhe kontabiliteti | Detyrime fiskale | Klientë | Identifikuese, financiare | Detyrimi ligjor (ATK) | ATK, banka | Jo | 6+ vjet (ligji tatimor) | Enkriptim, audit log |
| 3 | Mjetet e klientit (trust) | Menaxhim fondesh të klientit | Klientë | Financiare, burimi i fondeve | Kontrata; detyrimi ligjor (AML 05/L-096) | NjIF-K (vetëm me raport) | Jo | 5+ vjet (AML neni 27) | Enkriptim, bilanc i pandashëm negativ, audit |
| 4 | KYC / AML | Identifikimi i klientit | Klientë, pronarë përfitues | Dokument identifikimi, PEP, rrezik | Detyrimi ligjor (05/L-096) | NjIF-K sipas ligjit | Jo | 5 vjet pas përfundimit të marrëdhënies | Enkriptim, qasje e kufizuar |
| 5 | Portali i klientit | Komunikim dhe nënshkrime | Klientë | Identifikuese, mesazhe, nënshkrime | Pëlqimi (i regjistruar) | — | Jo | Sa lënda | TLS, JWT, pëlqim i regjistruar |
| 6 | Kujtesa email/SMS | Njoftim për afate | Klientë | Kontakt, data e seancës | Pëlqimi (SMS); interesi legjitim (email) | Ofruesi SMTP/SMS | Sipas ofruesit (shih DPA Aneksi A) | Sa lënda | Pëlqim i regjistruar, dedup |
| 7 | Asistenti AI i jashtëm (opsional) | Ndihmë kërkimore | Klientë (indirekt) | Fragmente pyetjesh/konteksti | Interesi legjitim + cilësimi i zyrës | DeepSeek (Kinë) | **Po — kërkon vlerësim/autorizim AIP** | Nuk ruhet lokalisht përtej bisedës | I çaktivizueshëm; alternativa lokale |
| 8 | Pagesa me kartelë (opsional) | Arkëtim faturash | Klientë | Emër, email, shumë | Kontrata | Stripe | Po (SHBA/BE, SCC) | Sipas Stripe | Vetëm link pagese, pa ruajtje kartele |
| 9 | Regjistri i veprimeve (audit) | Siguria, etika profesionale | Përdoruesit, klientët | Veprimet në sistem, IP | Interesi legjitim; detyrimi profesional | — | Jo | Sa llogaria | Vetëm-lexim, qasje admin |
