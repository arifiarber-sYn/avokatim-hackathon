"""Citation verification (D-059 F6): extraction of German and Kosovar legal
citations from LLM answers, and the verification logic against the corpus
(DB faked — the query behavior itself is exercised in production)."""

import uuid

import pytest

from app.services.citation_check import (
    MAX_CITATIONS,
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
    def __init__(self, docs=None, first=None):
        self._docs = docs or []
        self._first = first

    def scalars(self):
        docs = self._docs

        class _S:
            def __iter__(self):  # list(rows.scalars())
                return iter(docs)

        return _S()

    def first(self):
        return self._first


class _Doc:
    def __init__(self, title):
        self.id = uuid.uuid4()
        self.title = title


class FakeDB:
    """First execute() per citation looks up docs; the second (if any)
    checks the section. Behavior is scripted per test."""

    def __init__(self, doc_hits, section_hit):
        self.doc_hits = doc_hits  # dict code-fragment -> [docs]
        self.section_hit = section_hit
        self.calls = 0

    async def execute(self, stmt):
        self.calls += 1
        text = str(stmt.compile(compile_kwargs={"literal_binds": True})).lower()
        if "legal_corpus_chunks" in text:
            return _Row(first=("x",) if self.section_hit else None)
        for frag, docs in self.doc_hits.items():
            if frag.lower() in text:
                return _Row(docs=docs)
        return _Row(docs=[])


@pytest.mark.anyio
async def test_verify_statute_full_match():
    db = FakeDB({"bgb": [_Doc("Bürgerliches Gesetzbuch")]}, section_hit=True)
    results = await verify_citations(db, uuid.uuid4(), "Nach § 573 BGB gilt...")
    assert results == [
        {
            "cite": "§ 573 BGB",
            "kind": "statute",
            "status": "verified",
            "source_title": "Bürgerliches Gesetzbuch",
        }
    ]


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
