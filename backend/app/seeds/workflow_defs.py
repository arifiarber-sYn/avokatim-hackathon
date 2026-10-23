"""Expert workflow definitions — DATA, not code (audit 2026-09-18, adv. #6;
the Vincent / AVOKATI W1–W5 pattern at AvokatIM scale).

A workflow is a fixed, named sequence of steps a litigator actually runs on a
matter file. Each step declares which context builders it needs (names are
resolved by services/workflows.py) and its prompt template. Adding a
jurisdiction or a workflow is an edit HERE, never in service code (hard rule
#4). Prompts are written in the jurisdiction's primary language; the answer
language follows the matter/UI locale via the {language_hint}.

Placeholders available in prompts:
  {matter_context}   — parties, status, practice area (build_matter_context)
  {documents}        — the matter's documents (full, budgeted)
  {deadline_rules}   — the jurisdiction's procedural deadline rules (seeded)
  {upcoming}         — the matter's own upcoming deadlines
  {language_hint}    — "Përgjigju në gjuhën ..." when locale != sq
"""

WORKFLOW_DEFS: dict[str, dict[str, dict]] = {
    # ------------------------------------------------------------------
    # W-Ankesa: appeal analysis — grounds, deadlines, prospects
    # ------------------------------------------------------------------
    "appeal": {
        "XK": {
            "name": "Analiza e ankesës",
            "steps": [
                {
                    "id": "grounds",
                    "label": "Bazat e ankesës",
                    "needs": ["matter_context", "documents", "language_hint"],
                    "prompt": (
                        "Ti je avokat me përvojë në procedurën civile e penale të "
                        "Kosovës. Nga dosja e mëposhtme identifiko BAZAT E MUNDSHME "
                        "TË ANKESËS: (a) shkelje thelbësore të dispozitave procedurale, "
                        "(b) vërtetim i gabuar ose jo i plotë i gjendjes faktike, "
                        "(c) zbatim i gabuar i së drejtës materiale (LPK neni 178; për "
                        "çështje penale KPP). Për çdo bazë: cito nenin përkatës, shpjego "
                        "shkurt pse qëndron në faktet e kësaj dosjeje, dhe vlerëso "
                        "forcën e saj (e fortë / mesatare / e dobët).{language_hint}\n\n"
                        "{matter_context}\n\nDOKUMENTET:\n{documents}"
                    ),
                },
                {
                    "id": "deadlines",
                    "label": "Afatet e ankesës",
                    "needs": ["matter_context", "deadline_rules", "upcoming", "language_hint"],
                    "prompt": (
                        "Nga rregullat procedurale të mëposhtme dhe gjendja e lëndës, "
                        "përcakto AFATET që vlejnë për ankesën në këtë lëndë: cilat "
                        "rregulla aplikohen, nga cila ngjarje nis afati, dhe çfarë "
                        "duhet regjistruar në kalendar. Shëno qartë çdo afat që rrezikon "
                        "të humbet.{language_hint}\n\n{matter_context}\n\n"
                        "RREGULLAT E AFATEVE ({jurisdiction}):\n{deadline_rules}\n\n"
                        "AFATET EKZISTUESE TË LËNDËS:\n{upcoming}"
                    ),
                },
                {
                    "id": "assessment",
                    "label": "Vlerësimi i perspektivës",
                    "needs": ["matter_context", "language_hint"],
                    "prompt": (
                        "Mbi bazën e analizës së deritanishme të kësaj bisede, jep një "
                        "VLERËSIM PËRMBYLLËS për ankesën: perspektiva e suksesit, "
                        "rreziqet (përfshirë shpenzimet), dhe rekomandimi konkret për "
                        "klientin (ankesë e plotë / e pjesshme / jo ankesë). Maksimumi "
                        "gjysmë faqeje.{language_hint}\n\n{matter_context}"
                    ),
                },
            ],
        },
    },
    # ------------------------------------------------------------------
    # W-Konformiteti: filing compliance check
    # ------------------------------------------------------------------
    "compliance": {
        "XK": {
            "name": "Kontrolli i parashtresës",
            "steps": [
                {
                    "id": "elements",
                    "label": "Elementet e detyrueshme",
                    "needs": ["matter_context", "documents", "language_hint"],
                    "prompt": (
                        "Ti je bashkëpunëtor profesional që kontrollon parashtresat para "
                        "dorëzimit. Kontrollo dokumentin/et e fundit të dosjes kundrejt "
                        "elementeve të detyrueshme të parashtresës sipas LPK neni 99 "
                        "(dhe neni 253 për padinë): gjykata, palët me adresa, objekti i "
                        "kontestit, vlera e kontestit, kërkesa (petitumi), faktet dhe "
                        "provat, nënshkrimi. Për çdo element: ✓ në rregull / ⚠ mangët / "
                        "✗ mungon, me referencën ligjore.{language_hint}\n\n"
                        "{matter_context}\n\nDOKUMENTET:\n{documents}"
                    ),
                },
                {
                    "id": "court_deadline",
                    "label": "Gjykata dhe afati",
                    "needs": ["matter_context", "deadline_rules", "upcoming", "language_hint"],
                    "prompt": (
                        "Për parashtresën e kontrolluar: (1) a i drejtohet gjykatës "
                        "kompetente (kompetenca lëndore dhe territoriale — arsyeto "
                        "shkurt), (2) cilat afate procedurale vlejnë për dorëzimin e "
                        "saj dhe a rrezikohen. Në fund jep listën përmbyllëse të "
                        "veprimeve para dorëzimit.{language_hint}\n\n{matter_context}\n\n"
                        "RREGULLAT E AFATEVE ({jurisdiction}):\n{deadline_rules}\n\n"
                        "AFATET EKZISTUESE TË LËNDËS:\n{upcoming}"
                    ),
                },
            ],
        },
    },
    # ------------------------------------------------------------------
    # W-Provat: evidence map — every claim → its supporting document
    # ------------------------------------------------------------------
    "evidence": {
        "XK": {
            "name": "Harta e provave",
            "steps": [
                {
                    "id": "claims",
                    "label": "Pretendimet dhe provat",
                    "needs": ["matter_context", "documents", "language_hint"],
                    "prompt": (
                        "Ti je avokat që përgatit lëndën për shqyrtim kryesor. Ndërto "
                        "HARTËN E PROVAVE të kësaj dosjeje si tabelë: | Pretendimi "
                        "faktik | Prova mbështetëse (dokumenti, pjesa përkatëse) | "
                        "Forca (e fortë/mesatare/e dobët) | Çfarë mungon |. Përfshi çdo "
                        "pretendim të palës sonë dhe pretendimet kryesore të palës "
                        "kundërshtare që duhen kundërshtuar (LPK neni 7 dhe 319: barra "
                        "e provës).{language_hint}\n\n{matter_context}\n\n"
                        "DOKUMENTET:\n{documents}"
                    ),
                },
                {
                    "id": "gaps",
                    "label": "Zbrazëtirat dhe hapat",
                    "needs": ["matter_context", "language_hint"],
                    "prompt": (
                        "Nga harta e provave e ndërtuar më sipër në këtë bisedë, listo "
                        "ZBRAZËTIRAT kryesore të provave dhe për secilën propozo hapin "
                        "konkret për ta mbyllur (dëshmitar, ekspertizë, sigurim prove "
                        "sipas LPK neni 356 e në vijim, kërkesë ndaj palës tjetër)."
                        "{language_hint}\n\n{matter_context}"
                    ),
                },
            ],
        },
    },
}


def get_workflow(kind: str, jurisdiction_code: str) -> dict | None:
    """The definition for (kind, jurisdiction), with XK as the fallback for
    jurisdictions that have no tailored definition yet."""
    by_jur = WORKFLOW_DEFS.get(kind) or {}
    return by_jur.get(jurisdiction_code) or by_jur.get("XK")
