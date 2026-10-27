"""
Reads docs/blog/findings.md: the hand-written interpretation of a run.

The file names the run it interprets in its front matter. If that is not
the run being reported, the text is ignored, so an interpretation can
never be paired with numbers it was not written for.
"""

import re
from pathlib import Path


Block = tuple


def _parse_blocks(lines: list[str], base: Path) -> list[Block]:
    blocks: list[Block] = []
    paragraph: list[str] = []
    bullets: list[str] = []
    table: list[str] = []

    def flush() -> None:
        nonlocal paragraph, bullets, table
        if paragraph:
            blocks.append(("p", " ".join(paragraph)))
        if bullets:
            blocks.append(("bullets", bullets))
        if table:
            rows = [
                [cell.strip() for cell in line.strip().strip("|").split("|")]
                for line in table
                if not re.fullmatch(r"\|?\s*:?-{3,}.*", line.strip())
            ]
            blocks.append(("table", rows[0], rows[1:]))
        paragraph, bullets, table = [], [], []

    for raw in lines:
        line = raw.rstrip()
        image = re.fullmatch(r"!\[(.*)\]\((.*)\)", line.strip())

        if not line.strip():
            flush()
        elif line.startswith("### "):
            flush()
            blocks.append(("h3", line[4:].strip()))
        elif image:
            flush()
            blocks.append(("image", image.group(1), base / image.group(2)))
        elif line.lstrip().startswith("|"):
            if paragraph or bullets:
                flush()
            table.append(line)
        elif line.startswith("- "):
            if paragraph or table:
                flush()
            bullets.append(line[2:].strip())
        elif bullets and raw.startswith("  "):
            bullets[-1] += " " + line.strip()
        else:
            if bullets or table:
                flush()
            paragraph.append(line.strip())

    flush()
    return blocks


def load_findings(path: Path, run_id: str) -> dict[str, list[Block]] | None:
    if not path.exists():
        return None

    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    front = re.match(r"---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)

    if not front or f"run: {run_id}" not in front.group(1):
        return None

    sections: dict[str, list[str]] = {}
    current = None

    for line in text[front.end():].splitlines():
        if line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is not None:
            sections[current].append(line)

    return {
        name: _parse_blocks(lines, path.parent)
        for name, lines in sections.items()
    }
