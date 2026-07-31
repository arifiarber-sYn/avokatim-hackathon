"""Document upload allowlist (D-033): docs/images/media in, executables out."""
from app.api.documents import upload_type_allowed


def test_common_legal_documents_allowed():
    assert upload_type_allowed("aktgjykim.pdf", "application/pdf")
    assert upload_type_allowed(
        "padi.docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    assert upload_type_allowed("prova.jpg", "image/jpeg")
    assert upload_type_allowed("regjistrimi.mp3", "audio/mpeg")
    assert upload_type_allowed("seanca.mp4", "video/mp4")
    assert upload_type_allowed("shenime.txt", "text/plain")


def test_unknown_mime_decided_by_extension():
    # browsers often send application/octet-stream for anything unusual
    assert upload_type_allowed("kontrata.pdf", "application/octet-stream")
    assert upload_type_allowed("kontrata.pdf", None)
    assert not upload_type_allowed("virus.exe", "application/octet-stream")


def test_executables_and_archives_rejected():
    assert not upload_type_allowed("payload.exe", "application/x-msdownload")
    assert not upload_type_allowed("script.sh", "text/x-shellscript")
    assert not upload_type_allowed("arkiva.zip", "application/zip")
    assert not upload_type_allowed("faqe.html", "text/html")
    # spoofed MIME with an executable extension must still fail
    assert not upload_type_allowed("payload.exe", "application/pdf")
    assert not upload_type_allowed("noext", "application/pdf")
