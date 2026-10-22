# HACKATHON — Open Agent 2026 (Wildcard [Tinkerer])

Statusi: aktiv · Dega: hackathon/open-agent-2026 · Worktree: /home/kllosha/AvokatIM-hack
Afati i dorëzimit: 27.10.2026, 23:45 UTC

## Pse
Open Agent Hackathon ka një track të vetëm që pranon projekt ekzistues: **Wildcard
[Tinkerer]**. Rregullat e tij kërkojnë integrim të **Zetaris** dhe **Meterless** dhe
vlerësojnë vetëm punën e re. AvokatIM është projekti ynë ekzistues; puna e re është
shtresa e adapterave.

## Çfarë u shtua (Faza A, 22.10.2026)
- backend/app/adapters/base.py — kontrata Evidence / QuerySpec / SourceAdapter / dedupe
- backend/app/adapters/zetaris.py — adapter live (HTTP) + FixtureAdapter (mock i deklaruar)
- backend/app/adapters/meterless.py — ekzekutim lokal + usage.jsonl (një rresht për thirrje)
- backend/app/config.py — hackathon_mode (default false), zetaris_*, meterless_*,
  hackathon_usage_log
- backend/tests/test_adapters_contract.py — 5 teste, pa rrjet/DB

## Parimi
Asnjë SDK i sponsorit nuk futet në core. Gjithçka e jashtme vjen si Evidence përmes
adapterit, prandaj kodi ekzistues nuk ndryshon sjellje kur hackathon_mode=False.

## Hapat pasardhës
1. Zetaris: llogari + lidhja e tri burimeve (ligje / praktikë / regjistra).
2. Meterless: Nightshift lokal + matje në UI.
3. Harness 20 pyetje-etalon mbi korpusin real (bazë para ndryshimeve).
4. Video 1–4 min + slide deck + README dorëzimi.

## Lidhje
- Plani i plotë: ~/.openclaw/workspace/memory/plans/2026-10-22-dy-garat-plani-i-plote.md
- Faqja e eventit: https://hackathon.genai.works/event/open-agent-hackathon-2026
\n## Zetaris — kontrata reale (verifikuar 22.10.2026)\n\nPlatforma lokale (docker, \) ekspozon REST SQL editor:\n\n    POST http://127.0.0.1:8888/api/v1.0/sql-editor/sqls/run\n    Authorization: Bearer <zeta-*-key>\n    X-Org-ID: 1\n    X-Request-ID: <uuid>\n    {"queryId": "<uuid>", "sql": "SELECT 1", "source": "SqlEditor", "limit": 1}\n\nProvat e kryera:\n\n- \ → **200**, \ (kërkesa e smoke_test.py të guide-it).\n- \ → \.\n- \ → 400 TABLE_OR_VIEW_NOT_FOUND (motor Spark-like).\n- \ → kërkon \; \ të thjeshta janë çaktivizuar.\n\nPasoja për adapterin: \ është rruga e vetme; \ do të\nsynojë tabelën e korpusit kur ajo të krijohet, ndryshe ngre \ (fail-closed,\npa gënjeshtra). Çelësi lexohet nga \ (0600) dhe\nnuk shfaqet në log.\n

## Harness etalon — matjet (22.10.2026)

20 pyetje: 15 brenda korpusit (ligje/kode shqip), 5 jashtë (duhet refuzim).

| Varianti | Brenda (ok/15) | Jashtë (refuzuar/5) | Gjithsej |
|---|---|---|---|
| v1 plainto_tsquery | 9 | 2 | 11/20 |
| v2 OR + prag | 10 | 1 | 11/20 |
| v2 + portë domeni | 9 | 4 | 13/20 |
| v2 + portë + fjalor i zgjeruar | 10 | 4 | 14/20 |

Porta e domenit (LEGAL_HINTS) është ajo që e bën agjentin të thotë "s'e di": pa të,
pyetjet jashtë korpusit (TVSH në Norvegji, zgjedhjet në Brazil) merrnin fragmente të
rastësishme nga ligjet. Me të, 4/5 refuzohen saktë.

Raportet: data/evidence/harness-*.json (v1) dhe harness-v2-*.json (v2).
Ekzekutimi: AVOKATIM_DSN=<dsn> python hackathon/harness_v2.py


## Harness v3 — kërkim vektor (22.10.2026)

Modeli paraphrase-multilingual-MiniLM-L12-v2 (384 dim) nga cache lokale; pgvector
mbi 350 612 chunks. Asnjë tekst nuk del nga makina.

| Varianti | Brenda (ok/15) | Jashtë (refuzuar/5) | Gjithsej |
|---|---|---|---|
| v1 leksikor | 9 | 2 | 11/20 |
| v2 + portë domeni | 10 | 4 | 14/20 |
| v3 vektor + portë | 12 | 4 | 16/20 |

hit@5 u ngjit nga 6 në 7, keyword@5 nga 8 në 10. Mbeten: q02 (parashkrim),
q17 (punë), q18 (ekzekutim) — kërkim vektor gjen tekstin e duhur por jo titullin
e pritur; q15 (Tokio) kalon portën sepse "regjistrim" është term juridik.

Raporti: data/evidence/harness-v3-*.json
Ekzekutimi: AVOKATIM_DSN=<dsn> python hackathon/harness_v3.py


## Meta Model API adapter (22.10.2026)

backend/app/adapters/meta_model.py — klient OpenAI-compatible për modelet e Meta-s
(Muse/SAM). base_url, api_key dhe modeli vijnë nga konfigurimi; pa to adapteri
raporton available() == False dhe ngre AdapterError (fail-closed, pa thirrje të rreme).

- MetaModelAdapter.complete(prompt, system) -> Completion(text, model, tokens_in, tokens_out, ms)
- StubModel — zëvendësues determinist për teste/demo offline, i etiketuar si stub.

Testet: tests/test_adapters_meta.py (3 teste) + tests/test_adapters_contract.py (5 teste)
— 8 passed, pa rrjet.


## Harness v4 — filtër gjuhe (22.10.2026)

Defekti i v3: 16 906 dokumente gjermane vs 3 086 shqipe; kërkimi vektor pa filtër
tërhiqte BGH/Arbeitsgerichtsgesetz për pyetje shqipe.

Ndryshimi: kur pyetja është shqipe (markerë ë/ç ose fjalë funksionale), kërkohet vetëm
brenda d.language = 'sq'. Porta e domenit u ngushtua në terma të fortë juridikë.

| Varianti | Brenda (ok/15) | Jashtë (refuzuar/5) | Gjithsej |
|---|---|---|---|
| v1 leksikor | 9 | 2 | 11/20 |
| v2 + portë | 10 | 4 | 14/20 |
| v3 vektor | 12 | 4 | 16/20 |
| v4 vektor + gjuhë | 14 | 5 | 19/20 |

hit@5 8/15, keyword@5 13/15. Mbetet q02 (parashkrimi) — retrieval kthen marrëveshje
kredie, jo LMD.

Raporti: data/evidence/harness-v4-*.json
Ekzekutimi: AVOKATIM_DSN=<dsn> python hackathon/harness_v4.py


## Harness v5 + held-out (22.10.2026)

v5 = vektor + filtër gjuhe + rirenditje hibride (50 kandidatë, bonus 0.12 për termat
juridikë që shfaqen në tekst).

| Seti | Brenda | Jashtë | Shënim |
|---|---|---|---|
| I akorduar (20 pyetje) | 15/15 | 5/5 | i ngopur — rrezik overfitting |
| Held-out (13 pyetje të reja) | 9/10 | 3/3 | h08 u refuzua: "hetim" mungonte në portë |

Mësimi: 20/20 mbi setin tim nuk është provë; seti i dytë i paprekur është ai që flet.
Prandaj çdo shifër në deck duhet të vijë nga seti held-out, jo nga ai i akorduar.

Raportet: data/evidence/harness-v5-*.json dhe harness-v5-heldout-*.json


## Seti i verbër + porta e zgjeruar (22.10.2026)

Pas held-out, porta u zgjerua me termat që mungonin (hetim, ankes, shitës, pushim,
fëmij, kontrollues, mashtrim, reklam, shoqër) dhe u ndërtua një SET I TRETË që s'ishte
parë kurrë gjatë akordimit (questions-blind.json, 13 pyetje).

| Seti | Brenda | Jashtë |
|---|---|---|
| I akorduar | 15/15 | 5/5 |
| Held-out | 9/10 | 3/3 |
| Blind | 10/10 | 3/3 |

KUFIZIM METODOLOGJIK: metrika "brenda" kontrollon praninë e termit juridik në
fragmentin e kthyer, jo korrektësinë e dokumentit të parë (hit@5 është 0 në këto dy
sete sepse pritja e dokumentit u la bosh qëllimisht). Pra 10/10 nuk do të thotë
"saktësi 100%"; do të thotë "nuk refuzon gabimisht dhe kthen fragmentin me termin e duhur".
Matja me përgjigje-arta është hapi pasardhës dhe duhet bërë me sy njeriu.

Deck: docs/hackathon/deck-open-agent.md


## Demo CLI (22.10.2026)

backend/hackathon/demo.py — pyetje -> dëshmi -> përgjigje me citime, ose "s'e di" me arsye.
Pa LLM në këtë hap: teksti i përgjigjes ndërtohet vetëm nga dëshmitë e kthyera, që të
tregojë saktësisht çka do të citohej. Kur lidhet modeli (lokal ose Meta), ndryshon vetëm
formulimi — citimet vijnë nga i njëjti burim.

Shembull (pyetja për parashkrimin): [1] vendim i Dhomës së Posaçme 0.679, [2] Ligji i Punës
Neni 87 0.660, [4] LMD Neni 373 0.638 — pra vendimi del mbi ligjin, dhe kjo duhet rregulluar
me një preferencë për burimet primare (ligj/kod) ndaj vendimeve.

Ekzekutimi: AVOKATIM_DSN=<dsn> python hackathon/demo.py "pyetja"


## Preferenca për burime primare (22.10.2026)

Demo-ja nxori një defekt: për pyetjen për parashkrimin, një vendim gjykate (0.679)
dilte mbi ligjin (LMD Neni 373, 0.638). U shtua bonus +0.05 për doc_type law/code.
Seti blind u ri-mat: 10/10 brenda, 3/3 jashtë — pa regresion.
Dokumentim dorëzimi: docs/hackathon/README-dorëzimi.md


## Video — draft i narratuar (22.10.2026)

docs/hackathon/video/demo-full.mp4 — 44 s, 1920x1080, H.264, zë shqip (Piper edon).
Skenat: titull → pyetje → dëshmi (ligji i pari, vendimet poshtë) → refuzim → matje →
arkitekturë. Të gjitha kartat janë renderim i output-it real të demo.py, jo pamje të
inskenuara. Konsole nuk hap dritare në këtë sesion, prandaj u zgjodh rruga e kartave.

Rregullim: "Përgjigjja" -> "Përgjigja" në demo.py.


## Video 58 s (22.10.2026)

U shtuan dy skena me substancë, jo me zë: "para/pas" e renditjes (vendim mbi ligj ->
ligj i pari) dhe "citimi" (dokument + nen + fragment). Gjithsej 58.4 s, 1.6 MB.
Skenat: titull, pyetje, deshmi, klik, para/pas, citim, refuzim, matje, arkitekture.


## Fletë verifikimi për përgjigje-arta (22.10.2026)

docs/hackathon/arta-per-verifikim.md — 10 pyetje, për secilën 3 kandidatët më të mirë
(titull, nen, ngjashmëri, fragment) dhe një fushë "i saktë (plotëso)".

Qëllimi: njeriu konfirmon/korrigjon, pastaj matet saktësia e vërtetë ndaj atyre
përgjigjeve. Pa këtë hap, "saktësia" do të ishte matje e sistemit me vetveten.

Vëzhgim i parë që del nga fleta: për "Kur fillon afati i parashkrimit të kërkesave?"
kandidati kryesor është Ligji i Punës Neni 87 (parashkrim i kërkesave nga marrëdhënia
e punës), jo LMD Neni 373 (parashkrim i përgjithshëm civil). Kjo tregon se pyetja
duhet të jetë më e ngushtë ose renditja duhet të marrë parasysh domenin e pyetjes.


## Deck PDF + paketa e dorëzimit (22.10.2026)

- docs/hackathon/deck.html dhe deck.pdf — 10 slide, 16:9, 10 faqe, nga deck-open-agent.md.
- docs/hackathon/submission.md — tekstet e platformës, deklarata e ndershme për Zetaris
  dhe Meterless, harta e vlerësimit (Impact 30, Technical 20, Innovation 15, Demo 15,
  Product & UX 10, Sponsor tech 10), tabela e aseteve dhe checklist-i para dorëzimit.

Vlerësimi i garës u lexua nga faqja zyrtare; çmimet për Wildcard [Tinkerer]:
1000/600/400 USD.


## Video 81 s — skenat e sponsorëve (22.10.2026)

U shtuan: "pse jo chatbot" (krahasim citimi/refuzimi/privatësie) dhe "statusi i sponsorëve"
(Zetaris live SELECT 1 + datasource i papërfunduar; Meterless adapter + matje, pa build
x86_64). Gjithsej 81.2 s, 2.0 MB — brenda kufirit 1-4 min të garës.


## Video 90 s — pamja e produktit live (22.10.2026)

U shtua skena me ekranin real të AvokatIM-it lokal (127.0.0.1:3000): pyetja
"Punëdhënësi s'ma ka paguar pagën — çfarë të bëj?" dhe përgjigjja me citime
(Ligji i Punës Neni 55, Dhoma e Posaçme, Gjykata Supreme), e kapur nga produkti
që punon — jo mockup. Gjithsej 90.3 s, 2.2 MB, brenda kufirit 1-4 min.

Regjistrimi me x11grab u ndal dy herë nga konflikte procesesh; u zgjidh me skript
të veçantë dhe pastrim të x11grab para nisjes. Mësim: kur nis regjistrim në sfond,
kontrollo pgrep -f x11grab para se ta nisësh përsëri.


## Zgjerim konteksti + preferencë për kod (22.10.2026, 16:20)

- backend/hackathon/context_expand.py — kur neni referon "nenin X", sillet edhe ai nen
  nga i njëjti dokument; në pyetjet procedurale (paraburgim, afat, ankim, lirim) kodi
  merr +0.08 ndaj vendimeve.
- demo.py i përdor të dyja.

Efekti i matur mbi 5 pyetjet e verifikuara:
  nen i saktë 0/5 -> 1/5 (rasti "përmbajtja e kontratës së punës": Neni 10 + Neni 11),
  ligj i saktë me nen të afërt 4/5 -> 3/5,
  burim i gabuar 1/5 -> 1/5 (KPP Neni 164 është "arrestimi gjatë hetimit", jo lirimi).

Kufizim: zgjerimi lexon vetëm 280 shkronjat e para të fragmentit.
Detajet: docs/hackathon/arta-verifikuar.md


## Indeks i titujve të neneve (22.10.2026, 16:25)

- context_expand.heading_search() — kërkon në 120 shkronjat e para të fragmentit
  (titulli i nenit), vetëm për doc_type law/code. Synimi: të goditet neni, jo dokumenti.
- heading_bonus() — titujt që përmbajnë termat e pyetjes marrin +0.09, vetëm për ligj/kod.

Gjendja: indeksi gjen nene ligjore, por ende nuk rendit saktë brenda kodit (p.sh. për
"kur lirohet nga paraburgimi" del KPP Neni 164 'Arrestimi gjatë fazës së hetimit' dhe jo
Neni 185 'Paraburgimi'). Hapi tjetër: renditje sipas përputhjes së titullit, jo sipas
gjatësisë së fragmentit.


## Titulli i nenit — kufizim i struktures (22.10.2026, 16:30)

Provova tre variante të renditjes së titujve:
1. ORDER BY length(text) — doli nen i shkurtër i një kodi tjetër.
2. Përputhje termash në 120 shkronjat e para — barazim, rend arbitrar.
3. Peshim 3x për 60 shkronjat e para — të gjithë kandidatët dolën me të njëjtin skor (4),
   sepse shumë ligje e kanë "paraburgim" në titullin e nenit.

Shkaku: korpusi NUK ka kolonë titulli; titulli është brenda tekstit me formatim të
ndryshueshëm ("Neni 185\nParaburgimi\n1. ..."). Pa fushë titulli, renditja në nivel neni
nuk është e besueshme.

Zgjidhja e propozuar: tabelë derivative hackathon_article_titles(doc_id, section, title)
e ndërtuar një herë për dokumentet shqipe, pastaj renditje mbi të. Nuk prek skemën e
prodhimit; shtohet vetëm në degën e garës.


## Tabelë derivative e titujve (22.10.2026, 16:35)

U ndërtua në bazën e AvokatIM (vetëm dega e garës e përdor):

    hackathon_article_titles(doc_id uuid, section text, title text, PK(doc_id, section))

24 924 rreshta për dokumentet shqipe; titulli nxirret nga rreshti pas "Neni X".
Prova: Kodi Nr. 04/L-123, Neni 185 -> "Paraburgimi". Kërkimi mbi këtë tabelë kthen
Neni 182/366 ("Paraburgimi") të kodeve të procedurës, jo ligje të rastësishme.

GJENDJA E INTEGRIMIT: heading_search() punon i vetëm (12 rezultate, Neni 182 në krye,
skor 6). Por në demo.retrieve() rezultatet e titullit NUK shfaqen në top-5 — një defekt
lidhjeje që ende s'është gjetur. Hapi tjetër: trace i retrieve() hap pas hapi (sa kandidatë
hyjnë, sa dalin pas rerank), jo më provë-e-gabim.
