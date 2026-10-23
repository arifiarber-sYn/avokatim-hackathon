"""Article chunking and language plumbing for the multilingual corpus
(official gazette languages: sq, sr, tr, bs, en — Law 03/L-190)."""
from app.api.corpus import _SECTION_RE, _split_by_articles


def test_section_regex_all_gazette_languages():
    for header in ["Neni 176", "Član 5", "Clan 12", "ČLAN 41", "Madde 7",
                   "MADDE 19", "Article 3", "第一条"]:
        assert _SECTION_RE.match(header), header


def test_section_regex_rejects_plain_words():
    for line in ["Nenit 5 i referohemi", "Članovi dhe të tjera", "Maddeler",
                 "Articles overview", "Neni", "tekst i thjeshtë"]:
        assert _SECTION_RE.match(line) is None, line


def test_split_by_articles_serbian():
    text = (
        "ZAKON Br. 03/L-006 O PARNIČNOM POSTUPKU\n\n"
        "Član 1\nOvim zakonom utvrđuju se pravila postupka.\n\n"
        "Član 2\nSud odlučuje u granicama zahteva.\n"
    )
    pieces = _split_by_articles(text)
    sections = [s for s, _ in pieces]
    assert "Član 1" in sections
    assert "Član 2" in sections


def test_split_by_articles_turkish():
    text = (
        "KANUN\n\nMadde 1\nBu kanunun amacı usul kurallarını belirlemektir.\n\n"
        "Madde 2\nMahkeme talep sınırları içinde karar verir.\n"
    )
    sections = [s for s, _ in _split_by_articles(text)]
    assert "Madde 1" in sections and "Madde 2" in sections


def test_ava_ask_accepts_locale():
    from app.api.marketplace import AvaAskIn

    body = AvaAskIn(question="Koliko dana imam za žalbu?", locale="sr")
    assert body.locale == "sr"


def test_ask_request_accepts_locale():
    from app.schemas.assistant import AskRequest

    body = AskRequest(question="Test?", locale="tr")
    assert body.locale == "tr"
