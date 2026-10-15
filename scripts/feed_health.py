#!/usr/bin/env python3
"""Decide whether an empty YouTube card fetch is a blip or an outage.

YouTube's RSS feed 404s/500s for minutes at a time. One failed daily run harms
nothing — the README is unchanged and tomorrow retries — so it stays green. A
feed that stays unreachable for several consecutive runs is a real outage and
should go red.

Only the feed is measured. Publishing cadence is deliberately not part of this:
a reachable feed resets the streak to zero, so any number of quiet, upload-free
days can pass without a failure.

Reads FEED_OK ("true" when this run fetched cards) and persists the consecutive
failure count to .github/youtube-feed-state.json. Exits 1 only once the feed has
failed MAX_CONSECUTIVE_FAILURES runs in a row.
"""
import json
import os
import sys

STATE = os.path.join(
    os.path.dirname(__file__), "..", ".github", "youtube-feed-state.json"
)
MAX_CONSECUTIVE_FAILURES = 3


def load(path=STATE):
    try:
        with open(path) as fh:
            return int(json.load(fh)["consecutive_failures"])
    except (OSError, ValueError, KeyError):
        return 0


def save(count, path=STATE):
    with open(path, "w") as fh:
        json.dump({"consecutive_failures": count}, fh)
        fh.write("\n")


def next_count(previous, feed_ok):
    return 0 if feed_ok else previous + 1


def should_fail(count, feed_ok):
    return not feed_ok and count >= MAX_CONSECUTIVE_FAILURES


def main():
    feed_ok = os.environ.get("FEED_OK") == "true"
    previous = load()
    count = next_count(previous, feed_ok)
    if count != previous:
        save(count)
    if feed_ok:
        print(f"Feed reachable — consecutive-failure count reset to 0 (was {previous}).")
        return 0
    if should_fail(count, feed_ok):
        print(
            f"::error::YouTube feed unreachable for {count} consecutive runs — "
            "failing so the outage is visible."
        )
        return 1
    print(
        f"::warning::YouTube feed unreachable ({count} of "
        f"{MAX_CONSECUTIVE_FAILURES} consecutive runs) — staying green, next run retries."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
