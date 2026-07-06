from app.api.corpus import _split_by_articles
from app.services.rag import chunk_text


def test_chunk_text_splits_long_text():
    text = "\n\n".join(f"Paragrafi {i}. " + "fjalë " * 100 for i in range(10))
    chunks = chunk_text(text)
    assert len(chunks) > 1
    assert all(len(c) <= 2500 for c in chunks)


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
