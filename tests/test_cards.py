#!/usr/bin/env python3
"""Tests for the two scripts that rewrite README.md.

Run with: python3 tests/test_cards.py  (exits non-zero on any failure)
"""
import datetime
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from card_staleness import STALE_DAYS, is_stale, readme_age_days
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


NOW = datetime.datetime(2026, 10, 15, tzinfo=datetime.timezone.utc)


def test_one_day_is_not_stale():
    # A single missed feed fetch must stay green.
    assert not is_stale(1.0)


def test_threshold_is_stale():
    assert is_stale(float(STALE_DAYS))


def test_freshly_updated_is_not_stale():
    assert not is_stale(0.0)


def test_readme_age_uses_the_last_commit_that_changed_readme():
    os.environ.pop("README_EPOCH", None)
    repo = tempfile.mkdtemp()
    env = dict(os.environ, GIT_AUTHOR_DATE="2026-10-10T00:00:00Z",
               GIT_COMMITTER_DATE="2026-10-10T00:00:00Z")
    run = lambda *a: subprocess.run(a, cwd=repo, env=env, check=True,
                                    capture_output=True, text=True)
    run("git", "init", "-q", ".")
    run("git", "config", "user.email", "t@t")
    run("git", "config", "user.name", "t")
    # A commit that does not touch README.md must not count.
    run("git", "commit", "-q", "--allow-empty", "-m", "noise")
    (Path(repo) / "README.md").write_text("hi")
    run("git", "add", "README.md")
    run("git", "commit", "-q", "-m", "cards")
    cwd = os.getcwd()
    os.chdir(repo)
    try:
        age = readme_age_days(NOW)
    finally:
        os.chdir(cwd)
    # 2026-10-10 -> 2026-10-15
    assert 4.9 < age < 5.1, age
    assert is_stale(age)


def test_readme_epoch_env_wins_over_git_history():
    # The cards action clobbers history mid-job, so the workflow captures the
    # age beforehand and passes it in. The env var must take precedence.
    epoch = str(int(datetime.datetime(2026, 10, 10, tzinfo=datetime.timezone.utc).timestamp()))
    os.environ["README_EPOCH"] = epoch
    cwd = os.getcwd()
    os.chdir(tempfile.mkdtemp())  # not a git repo on purpose
    try:
        age = readme_age_days(NOW)
    finally:
        os.chdir(cwd)
        os.environ.pop("README_EPOCH", None)
    assert 4.9 < age < 5.1, age
    assert is_stale(age)


def test_readme_epoch_env_recent_is_not_stale():
    epoch = str(int(datetime.datetime(2026, 10, 14, tzinfo=datetime.timezone.utc).timestamp()))
    os.environ["README_EPOCH"] = epoch
    try:
        age = readme_age_days(NOW)
    finally:
        os.environ.pop("README_EPOCH", None)
    assert not is_stale(age), age


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"\n{len(tests)} tests passed")
