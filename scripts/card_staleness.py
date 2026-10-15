#!/usr/bin/env python3
"""Decide whether one empty card fetch may be tolerated.

YouTube's RSS feed hiccups on its own schedule. One missed fetch is not worth
a red run: the README still shows recently published cards and the next
scheduled run retries. But a feed that stays unreachable long enough to leave
the README visibly stale should fail loudly rather than look healthy.

Exits 0 when the README's cards are still fresh, 1 when they are stale or the
age cannot be established at all.
"""
import datetime
import os
import subprocess

STALE_DAYS = 3


def readme_age_days(now: datetime.datetime) -> float:
    """Days elapsed since the last commit that changed README.md.

    Prefer README_EPOCH from the environment. The cards action re-checks-out
    the repo with fetch-depth 1 mid-job, which replaces our deep clone and
    makes `git log -- README.md` report the wrong commit, so the age must be
    measured before that happens and passed through.
    """
    epoch = os.environ.get("README_EPOCH")
    if epoch:
        then = datetime.datetime.fromtimestamp(int(epoch), datetime.timezone.utc)
        return (now - then).total_seconds() / 86400
    out = subprocess.run(
        ["git", "log", "-1", "--format=%ct", "--", "README.md"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if not out:
        # No history to judge from; the caller must treat this as stale.
        raise RuntimeError("no commit history found for README.md")
    then = datetime.datetime.fromtimestamp(int(out), datetime.timezone.utc)
    return (now - then).total_seconds() / 86400


def is_stale(age_days: float) -> bool:
    """One failed daily run still leaves the README fresh; three do not."""
    return age_days >= STALE_DAYS


def main() -> None:
    now = datetime.datetime.now(datetime.timezone.utc)
    try:
        age = readme_age_days(now)
    except Exception as exc:  # cannot prove freshness -> do not assume it
        print(f"::error::Cannot determine README age ({exc}) — treating as stale.")
        raise SystemExit(1)
    print(f"README last updated {age:.2f} days ago (fail at {STALE_DAYS})")
    if is_stale(age):
        print(
            f"::error::README cards are {age:.1f} days old — the feed has been "
            "unreachable long enough to leave the profile visibly out of date."
        )
        raise SystemExit(1)
    print("README cards still fresh — tolerating a one-off feed failure.")


if __name__ == "__main__":
    main()
