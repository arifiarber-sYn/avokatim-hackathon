"""AvokatIM MCP server (audit 2026-09-18, advancement #8): tool catalog and
the read-only contract. The tools proxy the live HTTP API; here we verify
the surface, not the network."""

import importlib

mcp_server = importlib.import_module("scripts.mcp_server")

EXPECTED_TOOLS = {
    "kerko_korpusin",
    "lexo_lenden",
    "lista_e_lendeve",
    "afatet_e_lendes",
    "kerko_dokumentet",
    "drafto_memo",
}


def test_all_tools_registered():
    assert EXPECTED_TOOLS <= {t.__name__ for t in [
        mcp_server.kerko_korpusin, mcp_server.lexo_lenden,
        mcp_server.lista_e_lendeve, mcp_server.afatet_e_lendes,
        mcp_server.kerko_dokumentet, mcp_server.drafto_memo,
    ]}


def test_drafto_memo_is_the_only_write():
    """Everything except drafto_memo must be GET-only (read scope works);
    drafto_memo labels its note as a draft needing lawyer review."""
    import inspect

    for name in EXPECTED_TOOLS - {"drafto_memo"}:
        src = inspect.getsource(getattr(mcp_server, name))
        assert ".post(" not in src, f"{name} must not write"
    memo_src = inspect.getsource(mcp_server.drafto_memo)
    assert "DRAFT MEMO" in memo_src
    assert "read_write" in memo_src  # rejects read-only tokens with guidance


def test_token_required():
    old = mcp_server.TOKEN
    mcp_server.TOKEN = ""
    try:
        try:
            mcp_server._client()
            raised = False
        except RuntimeError:
            raised = True
        assert raised
    finally:
        mcp_server.TOKEN = old
