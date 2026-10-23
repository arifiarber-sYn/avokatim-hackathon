"""Teste per demon offline mbi korpusin K-a (pa DB, pa rrjet)."""
import importlib.util
import pathlib

DEMO = pathlib.Path(__file__).resolve().parents[1] / "backend" / "hackathon" / "demo_corpus.py"


def _demo():
    spec = importlib.util.spec_from_file_location("demo_corpus", DEMO)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_answer_joins_three_sources():
    r = _demo().answer("Kush u ankua per dezinsektimin e Prizrenit dhe cka vendosi paneli?")
    assert r["ok"] is True
    assert r["skedari"].endswith("Vendimi_2025-1289.txt")
    assert r["numer"] == "622-25-1796-2-2-1"
    assert r["vlera"] == 80000.0
    assert 105 in r["nene"]
    assert "Ekologjia" in r["citat"]


def test_refuses_without_evidence():
    r = _demo().answer("Sa kushton qiraja ne Berlin?")
    assert r["ok"] is False
    assert "asnje vendim" in r["reason"]
