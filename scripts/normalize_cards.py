#!/usr/bin/env python3
"""Split single-line YouTube card markdown into one card per line.

Upstream collapses the card block onto one line (unquoted `echo`), so we
re-split it. Idempotent: an already well-formed section round-trips unchanged.
"""
import os
import re


def normalize(markdown: str) -> str:
    markdown = re.sub(r"\s+", " ", markdown).strip()
    if not markdown:
        return ""
    # Split on the literal card opener "[![" rather than matching structure:
    # titles contain parens and brackets, so bracket/paren matching is wrong.
    cards = [c.strip() for c in re.split(r"(?=\[!\[)", markdown) if c.strip()]
    return "\n".join(cards)


def main() -> None:
    normalized = normalize(os.environ.get("MARKDOWN", ""))
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
        out.write("markdown<<NORM_EOF\n")
        out.write(normalized + "\n")
        out.write("NORM_EOF\n")
    count = sum(1 for line in normalized.splitlines() if line.startswith("[!["))
    print(f"Cards on separate lines: {count}")


if __name__ == "__main__":
    main()
