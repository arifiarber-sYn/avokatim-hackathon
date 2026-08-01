# AvokatIM Gjermani — prezantimi për investitorin (avokat)

> Statusi: draft, përgatitur më 2026-08-01. Pa çmime — me qëllim.
> Përshtat fushat [emri], [kontakti] para dërgimit.

---

**Lënda: AvokatIM — platforma që i jep një avokati kapacitetin e një zyre të tërë, tani edhe për tregun gjerman**

I nderuar koleg,

Ju shkruaj për t'ju prezantuar një projekt që besoj se e vlerësoni më mirë se kushdo: si avokat, ju e njihni nga brenda peshën e administratës mbi një zyrë ligjore — dhe si investitor, e dalloni momentin kur një treg i madh është gati të lëvizë. Gjermania sot është pikërisht në atë moment.

## Momenti i tregut

Në Gjermani ushtrojnë profesionin rreth 165 mijë avokatë, dhe shumica dërrmuese e zyrave janë të vogla — një deri në pesë avokatë. Këto zyra po përballen njëkohësisht me tri valë detyrimesh e ndryshimesh:

1. **Digjitalizimi i detyruar i komunikimit me gjykatat** — beA (postëkutia elektronike e avokatit) është prej vitesh e detyrueshme për çdo avokat.
2. **E-Rechnung e detyrueshme** — nga 1 janari 2027 (dhe nga 2028 për të gjithë) faturat B2B duhet të lëshohen në format të strukturuar elektronik (XRechnung/ZUGFeRD, standardi EN 16931). Shumica e zyrave të vogla nuk janë gati.
3. **Vala e AI-së** — klientët tashmë presin përgjigje të menjëhershme dhe punë më të shpejtë; avokatët që s'e përdorin AI-në konkurrohen nga ata që e përdorin.

Softueri që mbizotëron tregun është ndërtuar në epokën e Windows-it: i fuqishëm, por i rëndë, i lidhur me instalime lokale dhe i shtrenjtë në mirëmbajtje. Pikërisht ky kombinim — detyrime të reja ligjore mbi infrastrukturë të vjetër — hap derën për një platformë të re.

## Çfarë është AvokatIM

AvokatIM është platformë e plotë e menaxhimit të praktikës ligjore, e ndërtuar sipas standardeve të legal-tech 2026, që mbulon gjithë ciklin e punës së një zyre — nga pranimi i rastit deri te pagesa:

- **e-Akte (dosja digjitale e lëndës)**: palët, dokumentet me enkriptim e versionim, shënimet, detyrat, historia e plotë me audit log.
- **Motori i afateve procedurale** — kategoria ku ndodhin gabimet më të kushtueshme të profesionit. Afatet gjermane llogariten si rregulla të dhënash të verifikuara: ZPO, StPO, KSchG, VwGO, SGG, AO; muajt kalendarikë ekzaktë sipas §§ 187–188 BGB; fundjavat e festat sipas § 222 ZPO — përfshirë **festat e landit përkatës**, jo vetëm ato federale. Kjo saktësi është standardi që zyrat gjermane e presin nga softueri i tyre, dhe ne e kemi.
- **Kalkulatori i plotë RVG**: tabela § 13 RVG sipas gjendjes 2025 (KostBRÄG), pozicionet kryesore VV, Anrechnung-u i gebyrës së biznesit, Auslagenpauschale — me një klik rezultati kthehet në rreshta fature. Një version publik ("Was kostet ein Anwalt?") shërben edhe si vegël marketingu për platformën.
- **E-Rechnung e gatshme për 2027**: çdo faturë e një zyre gjermane del automatikisht si PDF hibrid ZUGFeRD/Factur-X (PDF/A-3b me XML EN 16931 të integruar), e validuar me veglat standarde të industrisë. Zyrat tona do ta presin detyrimin e ri të qeta — shumë konkurrentë të vegjël jo.
- **Eksporti DATEV**: kontabilisti i zyrës e merr periudhën me një klik në formatin EXTF që e njeh çdo Steuerberater gjerman.
- **Shabllonet e dokumenteve** të parambushura me të dhënat e lëndës — përfshirë Deckungsanfrage-n te siguruesi i mbrojtjes juridike.
- **Portali i klientit**: statusi i lëndës, mesazhet, dokumentet, nënshkrimi elektronik.
- **Shtatë gjuhë** të plota: gjermanisht, anglisht, turqisht, serbisht, boshnjakisht, shqip, kinezisht. Në një Gjermani ku miliona banorë e flasin gjermanishten si gjuhë të dytë, zyra që komunikon me klientin në gjuhën e tij fiton besim që të tjerët s'e ofrojnë dot.

## Ana që konkurrentët nuk e kanë: qytetari

Softueri klasik gjerman i shërben vetëm zyrës. AvokatIM ka që në themel edhe anën e qytetarit:

- **Ava, asistentja publike ligjore me AI** — përgjigjet në gjermanisht mbi një korpus real ligjor: 79 akte federale (BGB, ZPO, StGB, KSchG, të gjithë librat SGB relevantë për qytetarët, e deri te DSGVO në gjermanisht nga EUR-Lex) plus legjislacionin e landeve — nisur me NRW e Bavarinë — gjithsej afro 100 akte të indeksuara nen për nen. Përgjigjet vijnë **me citim të saktë të normës**, jo si tekst i përgjithshëm interneti.
- **Komunikimi me zë**: qytetari mund t'i flasë Ava-s dhe të dëgjojë përgjigjen — njohja e të folurit dhe zëri gjerman punojnë **lokalisht në serverin tonë**, me cilësi e shpejtësi që e kemi matur me tekst juridik real (transkriptim pothuajse perfekt në më pak se gjysmë sekonde).
- **Tregu i rasteve (marketplace)**: qytetari e përshkruan problemin — vetë ose në bisedë me Ava-n, e cila ia strukturon rastin — dhe avokatët e abonuar i shohin rastet e hapura të juridiksionit të tyre. Ava e pyet qytetarin edhe për **sigurimin e mbrojtjes juridike (Rechtsschutzversicherung)**; rasti i mbërrin avokatit me shenjën "Rechtsschutz vorhanden" — sinjali më i fortë që rasti paguhet.

Ky kombinim — vegël pune për avokatin + kanal i ri klientësh nga ana e qytetarit — nuk ekziston në asnjë prej platformave mbizotëruese gjermane.

## Krahasimi i hapur me standardet e sotme

Që ta keni pamjen të plotë, pa zbukurime:

| | Liderët e sotëm (RA-MICRO, AnNoText, Actaport) | AvokatIM DE sot |
|---|---|---|
| e-Akte, afate, RVG, DATEV, E-Rechnung | Po | **Po** — paritet i arritur dhe i testuar |
| beA e integruar | Po | **Ende jo** — procesi i regjistrimit te BRAK për qasje në ndërfaqen zyrtare (KSW) është përgatitur dhe nis tani; deri atëherë pozicionohemi si shtresë AI + marketplace mbi softuerin ekzistues |
| Asistent AI mbi ligje reale me citime | Pjesërisht (vegla teksti për avokatin, p.sh. anonimizim + verifikim citimesh) | **Po**, edhe për avokatin edhe publik për qytetarin |
| Ana e qytetarit / marketplace | Jo | **Po** |
| Komunikim me zë me asistentin | Jo (vetëm softuer diktimi për avokatët) | **Po**, lokalisht, në gjermanisht e 5 gjuhë të tjera |
| Shumëgjuhësia e plotë | Jo | **Po, 7 gjuhë** |
| Arkitektura | Windows/instalime lokale (gjenerata e vjetër) ose cloud pa AI të thellë | Cloud modern, një bazë kodi për shumë juridiksione |

beA është boshllëku ynë i vetëm funksional dhe njëkohësisht rreziku kryesor i afatit: qasja varet nga procesi i BRAK-ut, jo nga ne. Prandaj e kemi nisur regjistrimin që tani, paralelisht me gjithçka tjetër.

## Konfidencialiteti dhe përputhshmëria si produkt

Si avokat e dini: sekreti profesional (§ 203 StGB) dhe DSGVO nuk janë detaje marketingu, janë kushti i ekzistencës.

- Dokumentet e klientëve enkriptohen në disk dhe indeksohen me modele **lokale** — teksti i tyre nuk largohet asnjëherë nga serveri.
- Zëri (njohja e të folurit dhe sinteza) punon tërësisht lokalisht.
- **LLM lokal në përgatitje e sipër**: kemi validuar tashmë një model gjermanofolës në harduerin tonë (testuar me pyetje juridike reale mbi korpusin — citon normat saktë) dhe infrastruktura për ta aktivizuar është e gatshme e testuar. Para daljes publike në Gjermani, i gjithë komunikimi i qytetarëve gjermanë me AI do të përpunohet në serverin tonë — **asnjë e dhënë nuk do t'i dërgohet asnjë ofruesi të jashtëm AI**. Ky është diferencues që edhe liderët e tregut e zgjidhin vetëm pjesërisht (me anonimizim para dërgimit te ofruesit e jashtëm).
- Kufijtë ligjorë janë të ndërtuar në produkt, jo në premtime: Ava publike jep vetëm informacion ligjor, kurrë vlerësim rasti individual (§ 2 RDG); deklarimi "po flisni me AI" sipas EU AI Act Art. 50; modeli i abonimit pa asnjë përqindje nga honorarët, në përputhje me § 49b BRAO.

## Ku jemi sot

Platforma nuk është ide në letër — është softuer në prodhim:

- **Kosova**: platforma operon e plotë, me korpus ligjor real, avokatë e noterë të verifikuar, marketplace funksional dhe të gjitha modulet e mësipërme në punë të përditshme.
- **Gjermania**: hosti gjerman është funksional dhe i testuar nga fundi në fund — regjistrim zyre, konfigurim fiskal, kalkulim RVG, faturë ZUGFeRD, rast qytetari me sigurim juridik, eksport DATEV — gjithçka e verifikuar me teste të automatizuara dhe simulime të plota.
- **Një bazë kodi, dy vende**: rregullat e juridiksionit (afatet, festat, tarifat, shabllonet, korpusi) janë të dhëna, jo kod. Vendi i tretë kushton një pjesë të vogël të të parit.

Para daljes publike mbeten hapat operacionalë — dhe pikërisht këtu takohen interesat tona.

## Çfarë i propozoj një investitori që është vetë avokat

Kapitali është vetëm gjysma e asaj që kërkojmë; gjysma tjetër është autoriteti profesional që ju e keni:

1. **Rishikimi ligjor gjerman** — AGB, Datenschutzerklärung, Impressum dhe kufijtë e RDG-së të rishikuara nga një avokat gjerman janë kusht i portës sonë të lansimit. Partneri ynë ideal e bën ose e organizon vetë këtë.
2. **Infrastruktura evropiane** — kalimi i hostimit për qytetarët gjermanë në server në BE ("Serverstandort Deutschland/EU" është edhe argument shitjeje) dhe përfaqësuesi sipas GDPR Art. 27.
3. **Procesi beA** — mbështetje institucionale në komunikimin me BRAK-un si prodhues softueri zyrash.
4. **Zyrat e para pilote** — besueshmëria e një kolegu që e prezanton platformën te zyra të vogla vlen më shumë se çdo fushatë.

Në këmbim, ju hyni herët në një produkt që e ka kaluar fazën më të rrezikshme — është i ndërtuar, punon dhe e ka arritur paritetin funksional me standardet e tregut gjerman — pikërisht para hapave që e kthejnë në biznes: lansimi publik, zyrat e para, beA.

Do të më vinte mirë t'jua tregoj platformën drejtpërdrejt — një demonstrim praktik zgjat rreth 30 minuta: nga pyetja e një qytetari me zë në gjermanisht, te rasti i strukturuar me shenjën e sigurimit juridik, te fatura ZUGFeRD dhe eksporti DATEV. Besoj se do ta shihni menjëherë se ku qëndron vlera.

Me respekt,

[Emri juaj]
[Kontakti]

---

## Shënime për vete (mos i dërgo)

- **Pa çmime në asnjë version të kësaj shkrese** — as tonat, as të konkurrentëve. Diskutohen vetëm në takim, pasi vlera është e dukshme.
- Mos e fsheh beA-në — investitori-avokat e di rëndësinë; humbje besueshmërie po u duk se e anashkalojmë. Rreziku i afatit varet nga BRAK — thuaje hapur.
- LLM lokal: modeli është validuar dhe infrastruktura gati e testuar, por sot demo punon me ofrues të jashtëm për shpejtësi demonstrimi. Formulimi i saktë: "në përgatitje e sipër, aktivizohet para lansimit publik". Mos premto datë.
- Shifrat e tregut (165 mijë avokatë, detyrimi E-Rechnung 2027/28) janë të qëndrueshme; mos improvizo shifra të tjera pa burim.
- Demo-rrjedha për takim: pyetje me zë në gjermanisht te Ava → rasti i strukturuar me Rechtsschutz → pamja e avokatit me badge → kalkulimi RVG → fatura ZUGFeRD me XML → eksporti DATEV. Skripti teknik: `backend/scripts/de_simulation.py`; skenari i demos në `docs/pitch/skenari-demo.md`.
- Nëse pyet për pronësinë e kodit / ekskluzivitet: partneriteti formëson prioritetet e roadmap-it, jo pronësinë e produktit.
