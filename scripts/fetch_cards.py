#!/usr/bin/env python3
"""Fetch the channel's newest videos from YouTube's RSS feed and emit card markdown.

Replaces the third-party github-readme-youtube-cards action: the same
ytcards.demolab.com URLs, no upstream action to break, and no re-split
workaround (that action collapsed the block onto one line).
"""
import os
import re
import time
import urllib.request
from datetime import datetime
from urllib.parse import quote_plus

FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
MAX_CARDS = 6
ATTEMPTS = 2
RETRY_SECONDS = 60


def _tag(entry: str, name: str) -> str:
    match = re.search(rf"<{name}>([^<]*)</{name}>", entry)
    return match.group(1) if match else ""


def build_markdown(feed: str, max_cards: int = MAX_CARDS) -> str:
    cards = []
    for entry in feed.split("<entry>")[1:]:
        video_id = _tag(entry, "yt:videoId")
        title = _tag(entry, "title")
        published = _tag(entry, "published")
        if not (video_id and title and published):
            continue
        timestamp = int(datetime.fromisoformat(published).timestamp())
        url = (
            f"https://ytcards.demolab.com/?id={video_id}&title={quote_plus(title)}"
            f"&lang=en&timestamp={timestamp}&background_color=%230d1117"
            f"&title_color=%23ffffff&stats_color=%23dedede&max_title_lines=1"
            f"&width=250&border_radius=5"
        )
        cards.append(
            f'[![{title}]({url} "{title}")](https://www.youtube.com/watch?v={video_id})'
        )
        if len(cards) == max_cards:
            break
    return "\n".join(cards)


def fetch(channel_id: str) -> str:
    error = ""
    for attempt in range(ATTEMPTS):
        try:
            request = urllib.request.Request(
                FEED_URL.format(channel_id=channel_id),
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(request, timeout=30) as response:
                return build_markdown(response.read().decode("utf-8", "replace"))
        except OSError as exc:
            error = exc
            if attempt + 1 < ATTEMPTS:
                time.sleep(RETRY_SECONDS)
    print(f"::warning::cannot fetch YouTube feed: {error}")
    return ""


def main(fetch_feed=fetch) -> None:
    markdown = fetch_feed(os.environ["CHANNEL_ID"])
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
        out.write("markdown<<CARDS_EOF\n")
        out.write(markdown + "\n")
        out.write("CARDS_EOF\n")
    print(f"Cards fetched: {len(markdown.splitlines())}")


if __name__ == "__main__":
    main()
