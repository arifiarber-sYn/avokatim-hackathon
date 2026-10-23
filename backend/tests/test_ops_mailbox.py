"""D-064: the mailbox-management tool must never touch a matter alias.

email_ingest.py files mail sent to <user>+<token>@<domain> into the matter
by searching UNSEEN. If ops_mailbox marked those read/archived first, the
client's mail would vanish. These tests pin the firewall.
"""
import importlib.util
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, BACKEND / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mailbox = _load("ops_mailbox")


def _mail(to: str, subject: str = "x", body: str = "hello") -> bytes:
    return (f"From: someone@ex.com\r\nTo: {to}\r\nSubject: {subject}\r\n"
            f"Message-ID: <{abs(hash((to, subject)))}@x>\r\n\r\n{body}\r\n").encode()


class FakeIMAP:
    """Minimal IMAP: a mailbox of raw messages by UID; records STORE calls."""

    def __init__(self, messages: dict[int, bytes]):
        self.messages = messages
        self.stores: list[tuple[int, str, str]] = []

    def uid(self, cmd, *args):
        if cmd == "FETCH":
            uid = int(args[0])
            if uid not in self.messages:
                return ("OK", [None])
            return ("OK", [(b"", self.messages[uid])])
        if cmd == "STORE":
            uid, flags, value = int(args[0]), args[1], args[2]
            self.stores.append((uid, flags, value))
            return ("OK", [b""])
        if cmd == "SEARCH":
            return ("OK", [" ".join(map(str, sorted(self.messages))).encode()])
        raise AssertionError(cmd)

    def logout(self):
        return ("BYE", [])


def _patch(monkeypatch, messages):
    fake = FakeIMAP(messages)
    monkeypatch.setattr(mailbox, "_connect", lambda readonly: fake)
    return fake


def test_is_matter_alias_detects_plus_token():
    plus = mailbox.email.message_from_bytes(
        _mail("arifi.arber+abc1234567def@gmail.com"))
    plain = mailbox.email.message_from_bytes(_mail("arifi.arber@gmail.com"))
    assert mailbox._is_matter_alias(plus) is True
    assert mailbox._is_matter_alias(plain) is False


def test_mark_read_skips_matter_alias(monkeypatch):
    fake = _patch(monkeypatch, {
        10: _mail("arifi.arber@gmail.com", "personal bank"),          # safe
        11: _mail("arifi.arber+abc1234567xy@gmail.com", "client"),    # alias
    })
    result = mailbox.cmd_mark_read([10, 11])
    assert result["marked_read"] == [10]
    assert result["skipped_matter_alias"] == [11]
    # Only UID 10 ever got a STORE — the alias was never flagged.
    assert all(uid == 10 for uid, _, _ in fake.stores)


def test_archive_skips_matter_alias(monkeypatch):
    fake = _patch(monkeypatch, {
        20: _mail("arifi.arber@gmail.com", "newsletter"),
        21: _mail("arifi.arber+deadbeef99aa@gmail.com", "matter"),
    })
    result = mailbox.cmd_archive([20, 21])
    assert result["archived"] == [20]
    assert result["skipped_matter_alias"] == [21]
    assert all(uid == 20 for uid, _, _ in fake.stores)


def test_label_refuses_matter_alias(monkeypatch):
    _patch(monkeypatch, {30: _mail("arifi.arber+0123456789ab@gmail.com")})
    result = mailbox.cmd_label(30, "Clients")
    assert "refused" in result["error"]


def test_read_is_readonly_and_flags_alias(monkeypatch):
    fake = _patch(monkeypatch, {40: _mail("arifi.arber+aabbccddeeff@gmail.com", "s", "body")})
    result = mailbox.cmd_read(40)
    assert result["matter_alias"] is True
    assert result["body"] == "body"
    # Reading must never STORE a flag.
    assert fake.stores == []
