"""Markdown bilik fayllarını `##` başlıqlar üzrə chunk-lara bölür."""
from __future__ import annotations

import re
from pathlib import Path

Chunk = dict  # {"id", "title", "text", "source"}

_H2 = re.compile(r"^##\s+(.+)$", re.MULTILINE)


def parse_markdown(text: str, source: str) -> list[Chunk]:
    """Mətni `## başlıq` blokları üzrə chunk-lara bölür.

    Hər chunk-ın mətni başlığı + gövdəni əhatə edir (embedding üçün).
    İlk `##`-dən əvvəlki giriş (məs. `# Terms`) atılır.
    """
    chunks: list[Chunk] = []
    matches = list(_H2.finditer(text))
    for i, m in enumerate(matches):
        title = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        slug = re.sub(r"\W+", "-", title.lower()).strip("-")
        chunks.append(
            {
                "id": f"{source}#{i}-{slug}"[:80],
                "title": title,
                "text": f"{title}\n{body}",
                "source": source,
            }
        )
    return chunks


def load_chunks(knowledge_dir: Path) -> list[Chunk]:
    """knowledge_dir-dəki bütün .md fayllarını oxuyub chunk-lara bölür."""
    chunks: list[Chunk] = []
    for path in sorted(knowledge_dir.glob("*.md")):
        chunks.extend(parse_markdown(path.read_text(encoding="utf-8"), path.name))
    return chunks
