# Procedura e Njoftimit të Shkeljes së të Dhënave

*Sipas neneve 33–34 të Ligjit Nr. 06/L-082 për Mbrojtjen e të Dhënave
Personale. Dokument i brendshëm operativ i zyrës ligjore.*

## 1. Çfarë është shkelje

Çdo incident sigurie që çon në shkatërrim, humbje, ndryshim, shpalosje ose
qasje të paautorizuar në të dhëna personale — p.sh. vjedhje e laptopit,
kompromentim i llogarisë, qasje e paautorizuar në server, humbje e backup-it
të paenkriptuar.

## 2. Afatet kritike

| Hapi | Afati |
|---|---|
| Regjistrimi i incidentit brenda zyrës | menjëherë |
| Njoftimi i **AIP-së** (kur ka rrezik për të drejtat e subjekteve) | **brenda 72 orëve** nga marrja dijeni |
| Njoftimi i subjekteve të prekur (kur rreziku është i lartë) | pa vonesa të panevojshme |
| Dokumentimi i plotë i incidentit dhe masave | e vazhdueshme |

## 3. Hapat operativë

1. **Kufizo** — izolo sistemin e prekur (shkëput nga rrjeti, ndrysho
   fjalëkalimet, revoko sesionet).
2. **Vlerëso** — çfarë të dhënash u prekën, sa subjekte, a ishin të
   enkriptuara (dokumentet në AvokatIM janë të enkriptuara në disk — nëse
   çelësi nuk është kompromentuar, rreziku real mund të jetë i ulët).
3. **Regjistro** — koha e zbulimit, si u zbulua, sistemi/dosjet e prekura,
   vlerësimi i rrezikut (përdor regjistrin e veprimeve të AvokatIM si provë).
4. **Njofto AIP-në brenda 72 orëve** kur ka gjasa rreziku:
   Agjencia për Informim dhe Privatësi — https://aip.rks-gov.net.
   Përmbajtja: natyra e shkeljes, kategoritë/numri i subjekteve, pasojat e
   mundshme, masat e marra, kontakti.
5. **Njofto subjektet** kur rreziku për ta është i lartë (gjuhë e thjeshtë,
   në gjuhën e komunikimit të klientit).
6. **Analizo dhe përmirëso** — shkaku rrënjësor, masat parandaluese,
   përditësimi i kësaj procedure.

## 4. Regjistri i incidenteve

Çdo incident (edhe pa detyrim njoftimi) regjistrohet me: datën, përshkrimin,
vlerësimin e rrezikut, vendimin për njoftim (po/jo + arsyeja), masat e marra.
Regjistri mbahet në `docs/legal/` ose në sistemin e dosjeve të zyrës.
