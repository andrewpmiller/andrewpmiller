#!/usr/bin/env python3
"""Replace the marked YouTube card section in README.md.

Refuses to write an empty section or to touch a README without both markers,
so a bad run can never blank or corrupt the cards.
"""
import os
import re

PATTERN = r"(<!-- BEGIN YOUTUBE-CARDS -->).*?(<!-- END YOUTUBE-CARDS -->)"


def inject(content: str, markdown: str) -> str:
    """Return README content with the marker section replaced by markdown."""
    if not markdown.strip():
        raise ValueError("Empty markdown — refusing to write the card section.")
    if not re.search(PATTERN, content, flags=re.DOTALL):
        raise ValueError("YouTube cards markers not found in README.md")
    return re.sub(
        PATTERN,
        lambda m: m.group(1) + "\n" + markdown + "\n" + m.group(2),
        content,
        flags=re.DOTALL,
    )


def main() -> None:
    markdown = os.environ["MARKDOWN"]
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(inject(content, markdown))


if __name__ == "__main__":
    main()
