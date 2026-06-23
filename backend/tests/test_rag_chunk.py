"""RAG chunk parser testləri — xarici sorğusuz.

İşlət: backend/.venv/bin/python -m tests.test_rag_chunk
"""
from __future__ import annotations

from app.rag import chunk

SAMPLE = """# Terms

## P/E nisbəti
Qiymət/qazanc nisbəti. Səhmin bahalığını ölçür.

## RSI
Nisbi güc indeksi. 70+ həddən artıq alınıb.
"""


def test_parse_splits_on_h2() -> None:
    chunks = chunk.parse_markdown(SAMPLE, "terms.md")
    assert len(chunks) == 2, f"gözlənilən 2, alındı {len(chunks)}"


def test_chunk_has_title_and_text() -> None:
    chunks = chunk.parse_markdown(SAMPLE, "terms.md")
    assert chunks[0]["title"] == "P/E nisbəti"
    assert "Qiymət/qazanc" in chunks[0]["text"]
    assert chunks[0]["source"] == "terms.md"


def test_chunk_id_is_unique() -> None:
    chunks = chunk.parse_markdown(SAMPLE, "terms.md")
    ids = [c["id"] for c in chunks]
    assert len(set(ids)) == len(ids)


def test_text_includes_title() -> None:
    # Embedding üçün başlıq mətnə daxil olmalıdır.
    chunks = chunk.parse_markdown(SAMPLE, "terms.md")
    assert "P/E" in chunks[0]["text"]


def _run() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"  ok  {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} keçdi.")


if __name__ == "__main__":
    _run()
