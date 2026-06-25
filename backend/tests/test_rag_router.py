"""Router parse testi — model sorğusuz (sırf parse məntiqi).

İşlət: backend/.venv/bin/python -m tests.test_rag_router
"""
from __future__ import annotations

from app.agents import advisor


def test_parse_info() -> None:
    assert advisor._parse_route('{"path": "info"}') == "info"


def test_parse_chart() -> None:
    assert advisor._parse_route('{"path": "chart"}') == "chart"


def test_parse_discussion() -> None:
    assert advisor._parse_route('{"path": "discussion"}') == "discussion"


def test_parse_garbage_defaults_discussion() -> None:
    assert advisor._parse_route("not json") == "discussion"


def test_parse_unknown_defaults_discussion() -> None:
    assert advisor._parse_route('{"path": "weather"}') == "discussion"


def _run() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} keçdi.")


if __name__ == "__main__":
    _run()
