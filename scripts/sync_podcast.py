#!/usr/bin/env python3

import json
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


RSS_URL = "https://pinecast.com/feed/iroh"
OUTPUT_FILE = Path("_data/episodes.json")

ITUNES = "{http://www.itunes.com/dtds/podcast-1.0.dtd}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"


def get_text(node, path):
    element = node.find(path)
    if element is None or element.text is None:
        return ""
    return element.text.strip()


def parse_date(value):
    if not value:
        return "", 0

    try:
        date = parsedate_to_datetime(value)
        if date.tzinfo is None:
            date = date.replace(tzinfo=timezone.utc)
        return date.isoformat(), date.timestamp()
    except (TypeError, ValueError):
        return value, 0


request = Request(
    RSS_URL,
    headers={"User-Agent": "IROH-Website-RSS-Sync/1.0"},
)

with urlopen(request, timeout=30) as response:
    root = ET.fromstring(response.read())

channel = root.find("channel")
if channel is None:
    raise RuntimeError("The RSS feed does not contain a channel.")

channel_image_element = channel.find(f"{ITUNES}image")
channel_image = (
    channel_image_element.get("href", "")
    if channel_image_element is not None
    else ""
)
channel_image = channel_image or get_text(channel, "image/url")

episodes = []

for item in channel.findall("item"):
    enclosure = item.find("enclosure")
    audio_url = enclosure.get("url", "") if enclosure is not None else ""
    audio_type = enclosure.get("type", "audio/mpeg") if enclosure is not None else ""

    published, sort_time = parse_date(get_text(item, "pubDate"))

    episode_image_element = item.find(f"{ITUNES}image")
    episode_image = (
        episode_image_element.get("href", "")
        if episode_image_element is not None
        else ""
    )

    description = (
        get_text(item, f"{CONTENT}encoded")
        or get_text(item, "description")
    )

    episodes.append(
        {
            "title": get_text(item, "title"),
            "link": get_text(item, "link") or audio_url,
            "guid": get_text(item, "guid") or audio_url,
            "published": published,
            "duration": get_text(item, f"{ITUNES}duration"),
            "episode_number": get_text(item, f"{ITUNES}episode"),
            "episode_type": get_text(item, f"{ITUNES}episodeType"),
            "description_html": description,
            "audio_url": audio_url,
            "audio_type": audio_type,
            "image_url": episode_image or channel_image,
            "_sort_time": sort_time,
        }
    )

episodes.sort(key=lambda episode: episode["_sort_time"], reverse=True)

for episode in episodes:
    del episode["_sort_time"]

output = {
    "feed_title": get_text(channel, "title"),
    "feed_link": get_text(channel, "link"),
    "episodes": episodes,
}

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.write_text(
    json.dumps(output, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

print(f"Updated {OUTPUT_FILE} with {len(episodes)} episodes.")
