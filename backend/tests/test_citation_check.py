"""Citation verification (D-059 F6): extraction of German and Kosovar legal
citations from LLM answers, and the verification logic against the corpus
(DB faked — the query behavior itself is exercised in production)."""

import uuid

import pytest

from app.services.citation_check import (
    MAX_CITATIONS,
    _attribute_quotes,
    _quote_coverage,
    extract_citations,
    verify_citations,
)

# ---------- extraction: German ----------


def test_extracts_german_statutes():
    text = (
        "Nach § 573 Abs. 2 BGB kann der Vermieter kündigen. "
        "Siehe auch § 543 BGB und Art. 14 GG."
    )
    cites = {c["cite"]: c for c in extract_citations(text)}
    assert "§ 573 Abs. 2 BGB" in cites
    assert cites["§ 573 Abs. 2 BGB"]["section"] == "573"
    assert cites["§ 573 Abs. 2 BGB"]["code"] == "BGB"
    assert "§ 543 BGB" in cites
    assert "Art. 14 GG" in cites


def test_extracts_german_case_numbers():
    text = "Der BGH hat entschieden (VIII ZR 285/18); vgl. auch 2 BvR 1444/00."
    cites = [c for c in extract_citations(text) if c["kind"] == "case"]
    assert {c["cite"] for c in cites} == {"VIII ZR 285/18", "2 BvR 1444/00"}


def test_statute_with_numbered_code_book():
    cites = extract_citations("Der Anspruch folgt aus § 43 SGB V.")
    assert cites[0]["code"] == "SGB V"


# ---------- extraction: Kosovo ----------


def test_extracts_albanian_articles():
    text = (
        "Sipas nenit 176 të LPK-së ankesa paraqitet brenda 15 ditësh. "
        "Shih edhe neni 322 LMD."
    )
    cites = {c["cite"].lower(): c for c in extract_citations(text)}
    assert any("176" in k and "lpk" in k for k in cites)
    assert any("322" in k and "lmd" in k for k in cites)


def test_inflected_ligjit_is_not_a_code():
    """Eval finding 2026-09-18: 'neni 34 të Ligjit për Familjen' must not
    yield the useless code 'Ligjit' — it resolves to the title fragment."""
    cites = extract_citations("Sipas nenit 34 të Ligjit për Familjen e Kosovës…")
    assert cites, "named-law citation must be extracted"
    assert cites[0]["code"].lower().startswith("për familjen")
    # and a lone inflected 'ligjit' with no name resolves to nothing at all
    assert all(
        c["code"].lower() != "ligjit"
        for c in extract_citations("Kjo rregullohet me nenin 5 të ligjit përkatës.")
    )


def test_uppercase_codes_still_extracted():
    cites = extract_citations("Sipas nenit 176 të LPK-së dhe nenit 12 të LMD.")
    codes = {c["code"] for c in cites}
    assert "LPK" in codes
    assert "LMD" in codes


def test_extracts_albanian_law_numbers():
    cites = extract_citations("E rregulluar me Ligji Nr. 03/L-006 për procedurën.")
    law = next(c for c in cites if c["kind"] == "law")
    assert "03/L-006" in law["cite"]
    # The lookup code is the bare number — that is how corpus `reference`
    # stores laws, so "Ligji Nr. 03/L-006" must not fail verification
    assert law["code"] == "03/L-006"


# ---------- extraction: hygiene ----------


def test_dedup_and_cap():
    text = " ".join("§ 573 BGB" for _ in range(5)) + " " + " ".join(
        f"§ {n} BGB" for n in range(1, 60)
    )
    cites = extract_citations(text)
    assert len([c for c in cites if c["cite"] == "§ 573 BGB"]) == 1
    assert len(cites) <= MAX_CITATIONS


def test_plain_text_has_no_citations():
    assert extract_citations("Përshëndetje, si mund t'ju ndihmoj sot?") == []


# ---------- verification with a faked DB ----------


class _Row:
    def __init__(self, docs=None, first=None, rows=None):
        self._docs = docs or []
        self._first = first
        self._rows = rows or []

    def scalars(self):
        docs = self._docs

        class _S:
            def __iter__(self):  # list(rows.scalars())
                return iter(docs)

        return _S()

    def first(self):
        return self._first

    def all(self):  # quote-verification chunk fetch (v2)
        return self._rows


class _Doc:
    def __init__(self, title, doc_type="law", reference=None):
        self.id = uuid.uuid4()
        self.title = title
        self.doc_type = doc_type
        self.reference = reference


class FakeDB:
    """First execute() per citation looks up docs; the second (if any)
    checks the section; further chunk queries (v2) feed quote matching.
    Behavior is scripted per test."""

    def __init__(self, doc_hits, section_hit, chunk_rows=None):
        self.doc_hits = doc_hits  # dict code-fragment -> [docs]
        self.section_hit = section_hit
        self.chunk_rows = chunk_rows or []  # [(chunk_id, text)] for quotes
        self.calls = 0

    async def execute(self, stmt):
        self.calls += 1
        text = str(stmt.compile(compile_kwargs={"literal_binds": True})).lower()
        if "legal_corpus_chunks" in text:
            return _Row(
                first=(uuid.uuid4(),) if self.section_hit else None,
                rows=self.chunk_rows,
            )
        for frag, docs in self.doc_hits.items():
            if frag.lower() in text:
                return _Row(docs=docs)
        return _Row(docs=[])


@pytest.mark.anyio
async def test_verify_statute_full_match():
    db = FakeDB({"bgb": [_Doc("Bürgerliches Gesetzbuch")]}, section_hit=True)
    results = await verify_citations(db, uuid.uuid4(), "Nach § 573 BGB gilt...")
    assert len(results) == 1
    r = results[0]
    assert r["cite"] == "§ 573 BGB"
    assert r["kind"] == "statute"
    assert r["status"] == "verified"
    assert r["source_title"] == "Bürgerliches Gesetzbuch"
    # v2: results carry the source ids for clickable citations
    assert r["doc_id"]
    assert r["chunk_id"]


@pytest.mark.anyio
async def test_verify_law_found_but_not_section():
    db = FakeDB({"bgb": [_Doc("Bürgerliches Gesetzbuch")]}, section_hit=False)
    results = await verify_citations(db, uuid.uuid4(), "Nach § 9999 BGB gilt...")
    assert results[0]["status"] == "law_found"


@pytest.mark.anyio
async def test_verify_unknown_law_unverified():
    db = FakeDB({}, section_hit=False)
    results = await verify_citations(db, uuid.uuid4(), "Sipas nenit 176 të LPK-së...")
    assert results[0]["status"] == "unverified"


@pytest.mark.anyio
async def test_verify_case_number_by_reference():
    db = FakeDB({"viii zr 285/18": [_Doc("BGH, Urteil VIII ZR 285/18")]}, section_hit=False)
    results = await verify_citations(db, uuid.uuid4(), "Vgl. BGH VIII ZR 285/18.")
    case = next(r for r in results if r["kind"] == "case")
    assert case["status"] == "verified"


@pytest.mark.anyio
async def test_no_jurisdiction_returns_empty():
    db = FakeDB({}, section_hit=False)
    assert await verify_citations(db, None, "Nach § 573 BGB...") == []


# ---------- v2: quote-level verification ----------

_LAW_TEXT = (
    "Kontrata e qirasë mund të zgjidhet vetëm për shkaqe të arsyeshme të "
    "parashikuara me ligj dhe me njoftim paraprak me shkrim prej tridhjetë "
    "ditësh dërguar qiramarrësit në adresën e deklaruar."
)


def test_quote_coverage_exact_and_noise():
    assert _quote_coverage(_LAW_TEXT, "para " + _LAW_TEXT + " pas") == 1.0
    # markdown/typographic noise must not break the match (whole words only —
    # markdown never splits inside a word)
    noisy = _LAW_TEXT.replace(" ligj ", " **ligj** ").replace(
        " njoftim ", " _njoftim_ "
    )
    assert _quote_coverage(_LAW_TEXT, noisy) > 0.85


def test_quote_coverage_fabricated_is_low():
    fake = (
        "Qiradhënësi mund ta zgjidhë kontratën në çdo kohë pa njoftim dhe "
        "pa arsyetim sipas dëshirës së tij të lirë plotësisht"
    )
    assert _quote_coverage(fake, _LAW_TEXT) < 0.3


def test_attribute_quotes_same_sentence_only():
    text = (
        'Sipas nenit 176 të LPK, "ankesa paraqitet brenda pesëmbëdhjetë '
        'ditësh nga dita e dorëzimit të aktgjykimit" — kjo është baza.\n'
        'Një paragraf tjetër me "citat që nuk i takon askujt sepse është '
        'shumë larg dhe në rresht tjetër fare".'
    )
    cites = extract_citations(text)
    attributed = _attribute_quotes(text, cites)
    all_quotes = [q for qs in attributed.values() for q in qs]
    assert any("pesëmbëdhjetë" in q for q in all_quotes)
    assert not any("nuk i takon askujt" in q for q in all_quotes)


@pytest.mark.anyio
async def test_verify_quote_found_stays_verified():
    quote = "ankesa paraqitet brenda pesëmbëdhjetë ditësh nga dita e dorëzimit"
    chunk = (uuid.uuid4(), f"Neni 176. {quote} të aktgjykimit tek palët.")
    db = FakeDB({"lpk": [_Doc("Ligji i procedurës kontestimore")]},
                section_hit=True, chunk_rows=[chunk])
    text = f'Sipas nenit 176 të LPK, "{quote}".'
    results = await verify_citations(db, uuid.uuid4(), text)
    assert results[0]["status"] == "verified"
    assert results[0]["chunk_id"]


@pytest.mark.anyio
async def test_verify_fabricated_quote_downgrades_to_unverified():
    chunk = (uuid.uuid4(), _LAW_TEXT)
    db = FakeDB({"lpk": [_Doc("Ligji i procedurës kontestimore")]},
                section_hit=True, chunk_rows=[chunk])
    text = ('Sipas nenit 176 të LPK, "gjykata vendos sipas bindjes së lirë '
            'pa asnjë kufizim procedural dhe pa afat fare".')
    results = await verify_citations(db, uuid.uuid4(), text)
    assert results[0]["status"] == "unverified"
    assert "note" in results[0]


def test_doc_rank_prefers_base_act_over_amendment_and_judgment():
    from types import SimpleNamespace

    from app.services.citation_check import _doc_rank

    base = SimpleNamespace(title="Kodi i Procedurës Penale", doc_type="code")
    amendment = SimpleNamespace(
        title="Ligji për Ndryshimin dhe Plotësimin e Kodit të Procedurës Penale",
        doc_type="law",
    )
    judgment = SimpleNamespace(
        title="Gjykata Supreme — KPPP. nr.284/23", doc_type="judgment"
    )
    ranked = sorted([judgment, amendment, base], key=_doc_rank)
    assert ranked[0] is base
    assert ranked[-1] is judgment


def test_statute_alias_map_shape():
    from app.seeds.kosovo import XK_STATUTE_REFS

    assert XK_STATUTE_REFS["KPP"][0] == "08/L-032"
    assert XK_STATUTE_REFS["KPRK"] == ["06/L-074"]
    for refs in XK_STATUTE_REFS.values():
        assert refs and all("/" in r or r.startswith("2004") for r in refs)


def test_norm_law_name_inflections():
    from app.services.citation_check import _norm_law_name

    assert _norm_law_name("Ligjit të Punës") == "ligj punes"
    assert _norm_law_name("Ligji i Punës") == "ligj punes"
    assert (
        _norm_law_name("Kodit të Procedurës Penale të Kosovës")
        == "kod procedures penale"
    )
    assert _norm_law_name("Ligjit për Marrëdhëniet e Detyrimeve") == (
        "ligj marredheniet detyrimeve"
    )


def test_statute_name_alias_map_normalized_keys():
    from app.seeds.kosovo import XK_STATUTE_NAME_REFS
    from app.services.citation_check import _norm_law_name

    for key in XK_STATUTE_NAME_REFS:
        assert key == _norm_law_name(key), key
