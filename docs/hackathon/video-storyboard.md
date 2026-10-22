# Video 3 min — storyboard dhe skenar

Formati: 1920x1080, 30 fps, H.264. Zëri: narration shqip (ose titra + muzikë e lehtë).
Rregull: çdo pohim në video duhet të shihet në ekran; asnjë numër që s'është në raport.

## Skena 1 — Problemi (0:00-0:25)
Ekran: faqja e AvokatIM, kursor mbi fushën e pyetjes.
Narration: "1.8 milionë shqiptarë. Ligjet ekzistojnë. Ajo që mungon është përgjigjja
në gjuhën tënde — me burimin ku mund ta kontrollosh."
Titull i shkurtër: AvokatIM — agjenti që shpjegon pse.

## Skena 2 — Pyetja reale (0:25-0:45)
Ekran: demo.py me pyetjen "Kur fillon afati i parashkrimit të kërkesave?"
Narration: "Një pyetje që çdo avokat e dëgjon çdo ditë."
Prit derisa të shfaqen dëshmitë.

## Skena 3 — Dëshmitë (0:45-1:15)
Ekran: lista [1]..[5] me tituj, nen dhe ngjashmëri.
Narration: "Agjenti nuk kërkon në Google. Ai kërkon në korpusin juridik — 3 086
dokumente shqipe, 353 mijë fragmente — dhe kthen pesë dëshmi, secila me dokument
dhe nen."
Thekso: [1] burim primar (ligj) para vendimeve.

## Skena 4 — Cilimi (1:15-1:45)
Ekran: hap dokumentin/Nenin 373 ose 87; kursor mbi tekstin e fragmentit.
Narration: "Klikon dhe e sheh vetë. Kjo është diferenca mes 'besomë' dhe 'verifikoje'."

## Skena 5 — "s'e di" (1:45-2:10)
Ekran: demo.py me "Sa është TVSH-ja në Norvegji?"
Narration: "Dhe kur përgjigjja nuk është në korpus, agjenti nuk shpik. Thotë 's'e di'
dhe jep arsyen: pyetja nuk i përket domenit juridik."

## Skena 6 — Matjet (2:10-2:40)
Ekran: tabela e raportit (held-out 9/10, blind 10/10, refuzim 3/3).
Narration: "Nuk e themi ne — e matim. Tri sete pyetjesh, dy prej tyre të paprekura
gjatë zhvillimit. Dhe e themi hapur çka matet: prania e termit juridik në fragment,
jo ende saktësia e dokumentit të parë."

## Skena 7 — Arkitektura dhe mbyllja (2:40-3:00)
Ekran: diagrami (core + Zetaris + Meterless + Meta).
Narration: "Një core, tre adaptera. E njëjta bazë shkon nesër në Meta track.
AvokatIM — përgjigje që mund t'i kontrollosh."

## Regjistrimi (teknik)
- Terminal me font 16+, sfond i errët, pa histori personale në prompt.
- Regjistro vetëm dritaren: ffmpeg -f x11grab -video_size 1600x900 -framerate 30 -i :0.0+X,Y
- Zëri: Piper (shqip) ose regjistrim i Klloshës; sinkronizim me skenat.
- Montazh: ffmpeg concat; pa efekte që fshehin tekstin.
