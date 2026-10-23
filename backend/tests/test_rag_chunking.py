from app.api.corpus import _split_by_articles
from app.services.rag import chunk_text


def test_chunk_text_splits_long_text():
    text = "\n\n".join(f"Paragrafi {i}. " + "fjalë " * 100 for i in range(10))
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 2500 for c in chunks)


def test_chunk_text_splits_giant_paragraph():
    # German legal paragraphs are often multi-kilobyte single paragraphs —
    # they must be split, never kept as one oversized chunk (DE launch-gate item 3).
    text = "§ 1\n" + "Satz. " * 300  # ~1800 chars, one paragraph, no blank lines
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 2500 for c in chunks)
    assert "Satz" in chunks[0]


def test_chunk_text_hard_caps_oversized_sentence():
    # A single sentence longer than CHUNK_SIZE (no sentence boundary to split
    # on) still gets hard-capped at CHUNK_SIZE instead of staying one blob.
    text = "X" * 3000  # no spaces, no punctuation — worst case
    chunks = chunk_text(text)
    assert all(len(c) <= 2500 for c in chunks)
    assert "".join(chunks) == text


def test_chunk_text_keeps_abbreviations_intact():
    # "Art. 1", "Abs. 2", "z. B." must not be split mid-abbreviation.
    text = "Gemäß Art. 1 Abs. 2 gilt dies, z. B. für Mieter. " * 100
    chunks = chunk_text(text)
    assert all(len(c) <= 2500 for c in chunks)
    assert any("Art. 1 Abs. 2" in c for c in chunks)


def test_split_by_articles_albanian():
    text = "Hyrje e ligjit.\n\nNeni 1\nDispozita e parë.\n\nNeni 2\nDispozita e dytë."
    pieces = _split_by_articles(text)
    sections = [s for s, _ in pieces]
    assert "Neni 1" in sections
    assert "Neni 2" in sections


def test_split_by_articles_chinese():
    text = "第一条\n本法所称。\n\n第二条\n另一条款。"
    pieces = _split_by_articles(text)
    assert any(s and s.startswith("第一") for s, _ in pieces)


def test_split_by_articles_german_judgment_sections():
    text = (
        "Normen: § 4 InsO\n\n"
        "Tenor\nDer Antrag wird abgelehnt.\n\n"
        "Gründe\nDie Rechtsbeschwerde ist unzulässig."
    )
    sections = [s for s, _ in _split_by_articles(text)]
    assert "Tenor" in sections
    assert "Gründe" in sections


def test_judgment_headings_do_not_split_mid_sentence():
    # "Gründe für …" inside a law text must NOT start a new section.
    text = "§ 573\nGründe für ein berechtigtes Interesse des Vermieters."
    pieces = _split_by_articles(text)
    assert len(pieces) == 1
    assert pieces[0][0].startswith("§ 573")


# --- Hybrid fusion for matter documents (extends D-042 to case files) ------

class _Chunk:
    def __init__(self, cid):
        self.id = cid


class _MatterDoc:
    """Matter Document stand-in: deliberately has NO doc_type attribute —
    fusion without a judgment cap must never touch it."""

    def __init__(self, name):
        self.filename = name


def test_rrf_fuse_without_cap_never_reads_doc_type():
    from app.services.rag import _rrf_fuse

    a, b, c = _Chunk("a"), _Chunk("b"), _Chunk("c")
    doc = _MatterDoc("kontrata.pdf")
    vec = [(a, doc), (b, doc)]
    fts = [(b, doc), (c, doc)]
    out = _rrf_fuse([vec, fts], limit=3)  # no max_judgments
    ids = [chunk.id for chunk, _ in out]
    # b appears in both legs -> highest RRF score
    assert ids[0] == "b"
    assert set(ids) == {"a", "b", "c"}


def test_rrf_fuse_single_leg_still_ranks():
    from app.services.rag import _rrf_fuse

    doc = _MatterDoc("prova.pdf")
    vec = [(_Chunk(i), doc) for i in range(5)]
    out = _rrf_fuse([vec, []], limit=3)
    assert [chunk.id for chunk, _ in out] == [0, 1, 2]


def test_index_document_chunks_sets_simple_tsv():
    # The tsv expression must use the language-neutral 'simple' config
    # (matter documents are multilingual with no language column).
    import inspect

    from app.services import rag

    src = inspect.getsource(rag.index_document_chunks)
    assert 'to_tsvector("simple"' in src
