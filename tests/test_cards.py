#!/usr/bin/env python3
"""Tests for the two scripts that rewrite README.md.

Run with: python3 tests/test_cards.py  (exits non-zero on any failure)
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from feed_health import MAX_CONSECUTIVE_FAILURES, load, next_count, save, should_fail
from normalize_cards import normalize
from write_cards import inject

CARDS = (
    '[![A](https://ytcards.demolab.com/?id=1 "A")](https://youtu.be/1)\n'
    '[![B](https://ytcards.demolab.com/?id=2 "B")](https://youtu.be/2)'
)
README = (
    "# Hi\n"
    "<!-- BEGIN YOUTUBE-CARDS -->\n"
    "old line\n"
    "<!-- END YOUTUBE-CARDS -->\n"
    "bye\n"
)


def test_splits_cards_onto_separate_lines():
    assert normalize(CARDS) == CARDS


def test_bracket_in_title_still_splits():
    # A title containing "]" used to defeat the old splitter.
    md = (
        '[![Tune [beta] test](https://ytcards.demolab.com/?id=1 "x")](https://youtu.be/1) '
        '[![Next](https://ytcards.demolab.com/?id=2 "y")](https://youtu.be/2)'
    )
    out = normalize(md)
    assert out.count("\n") == 1, out


def test_normalize_is_idempotent():
    assert normalize(normalize(CARDS)) == normalize(CARDS)


def test_normalize_empty():
    assert normalize("") == ""


def test_inject_replaces_between_markers():
    out = inject(README, CARDS)
    assert "old line" not in out
    assert out.splitlines()[1] == "<!-- BEGIN YOUTUBE-CARDS -->"
    assert out.splitlines()[2] == CARDS.splitlines()[0]
    assert out.splitlines()[3] == CARDS.splitlines()[1]
    assert out.splitlines()[4] == "<!-- END YOUTUBE-CARDS -->"
    assert out.startswith("# Hi\n") and out.endswith("bye\n")


def test_inject_missing_markers_raises():
    try:
        inject("no markers here", CARDS)
    except ValueError:
        return
    raise AssertionError("expected ValueError when markers are missing")


def test_inject_empty_markdown_raises():
    try:
        inject(README, "   ")
    except ValueError:
        return
    raise AssertionError("expected ValueError when markdown is empty")


def test_quiet_publishing_is_never_an_error():
    # Feed reachable is the only thing that matters; a long gap between
    # uploads must not fail, whatever the counts say.
    assert not should_fail(0, True)
    assert not should_fail(9, True)


def test_a_single_feed_failure_is_tolerated():
    assert next_count(0, False) == 1
    assert not should_fail(1, False)


def test_a_reachable_feed_resets_the_streak():
    assert next_count(2, True) == 0


def test_repeated_feed_failures_eventually_fail():
    count, outcomes = 0, []
    for _ in range(MAX_CONSECUTIVE_FAILURES):
        count = next_count(count, False)
        outcomes.append(should_fail(count, False))
    assert outcomes[:-1] == [False] * (MAX_CONSECUTIVE_FAILURES - 1)
    assert outcomes[-1] is True


def test_state_round_trips():
    path = os.path.join(tempfile.mkdtemp(), "state.json")
    save(2, path)
    assert load(path) == 2


def test_missing_state_reads_as_zero():
    assert load(os.path.join(tempfile.mkdtemp(), "absent.json")) == 0


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\n{len(tests)} tests passed")
