#!/usr/bin/env python3

import json
import os
import re
import unicodedata
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape as html_escape
from html import unescape as html_unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


RSS_URL = "https://pinecast.com/feed/iroh"
OUTPUT_FILE = Path("_data/episodes.json")
TRANSCRIPT_DIRECTORY = Path("transcripts")
REFRESH_TRANSCRIPTS = os.environ.get("REFRESH_TRANSCRIPTS") == "1"

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


def display_date(value):
    try:
        formatted = datetime.fromisoformat(value).strftime("%B %d, %Y")
        return formatted.replace(" 0", " ")
    except (TypeError, ValueError):
        return value


def make_slug(value):
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value[:80] or "transcript"


def fetch_text(url):
    request = Request(
        url,
        headers={"User-Agent": "IROH-Website-RSS-Sync/1.1"},
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


class TranscriptLinkFinder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.current_href = ""
        self.current_text = []
        self.transcript_url = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a" or self.current_href:
            return

        attributes = dict(attrs)
        self.current_href = attributes.get("href", "")
        self.current_text = []

    def handle_data(self, data):
        if self.current_href:
            self.current_text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() != "a" or not self.current_href:
            return

        anchor_text = " ".join(self.current_text).strip().lower()
        href_lower = self.current_href.lower()

        if "transcript" in anchor_text or "/transcript" in href_lower:
            self.transcript_url = self.current_href

        self.current_href = ""
        self.current_text = []


def find_transcript_url(description_html):
    if not description_html:
        return ""

    parser = TranscriptLinkFinder()
    parser.feed(description_html)
    return urljoin(RSS_URL, parser.transcript_url) if parser.transcript_url else ""


class EpisodeDescriptionParser(HTMLParser):
    BLOCK_TAGS = {
        "article",
        "blockquote",
        "br",
        "div",
        "h1",
        "h2",
        "h3",
        "h4",
        "hr",
        "li",
        "p",
        "section",
    }

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag.lower() in self.BLOCK_TAGS:
            self.parts.append(" ")

    def handle_data(self, data):
        self.parts.append(data)


def make_description_text(description_html):
    if not description_html:
        return ""

    parser = EpisodeDescriptionParser()
    parser.feed(description_html)
    text = " ".join("".join(parser.parts).split())
    text = re.sub(r"^(?:Episode|Broadcast)\s+Notes\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(
        r"\s*Read transcript(?:\.{3}|…)?\s*$",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.strip()


def truncate_description(value, limit=180):
    if len(value) <= limit:
        return value

    shortened = value[: limit + 1].rsplit(" ", 1)[0].rstrip(" ,.;:-")
    return f"{shortened}…"


class PinecastTranscriptParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside_main = False
        self.capture_tag = ""
        self.capture_kind = ""
        self.capture_text = []
        self.pending_speaker = ""
        self.subtitle = ""
        self.turns = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()

        if tag == "main":
            self.inside_main = True
            return

        if not self.inside_main or self.capture_tag:
            return

        if tag == "h2" and not self.subtitle:
            self.capture_tag = "h2"
            self.capture_kind = "subtitle"
            self.capture_text = []
        elif tag == "span":
            self.capture_tag = "span"
            self.capture_kind = "speaker"
            self.capture_text = []
        elif tag == "p" and self.pending_speaker:
            self.capture_tag = "p"
            self.capture_kind = "paragraph"
            self.capture_text = []

    def handle_data(self, data):
        if self.capture_tag:
            self.capture_text.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()

        if tag == "main":
            self.inside_main = False
            return

        if tag != self.capture_tag:
            return

        value = " ".join(" ".join(self.capture_text).split()).strip()

        if self.capture_kind == "subtitle" and value:
            self.subtitle = value
        elif self.capture_kind == "speaker":
            if re.match(r"^Speaker\s+[^:]+:$", value, flags=re.IGNORECASE):
                self.pending_speaker = value.rstrip(":")
        elif self.capture_kind == "paragraph" and value:
            self.turns.append((self.pending_speaker, value))

        self.capture_tag = ""
        self.capture_kind = ""
        self.capture_text = []


class PinecastPreloadedQueryParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.inside_preloaded_queries = False
        self.parts = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag.lower() == "script" and attributes.get("id") == "preloaded-queries":
            self.inside_preloaded_queries = True

    def handle_data(self, data):
        if self.inside_preloaded_queries:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.inside_preloaded_queries:
            self.inside_preloaded_queries = False

    def transcript(self):
        if not self.parts:
            return "", []

        payload = json.loads("".join(self.parts))
        episode = payload.get("share", {}).get("episode", {})
        transcript = episode.get("transcript") or {}

        speaker_map = {}
        for appearance in transcript.get("speakerAppearances") or []:
            label = appearance.get("transcriptSpeakerLabel", "")
            name = (appearance.get("speaker") or {}).get("name", "")
            if label and name:
                speaker_map[label] = html_unescape(name)

        turns = []
        for utterance in transcript.get("utteranceData") or []:
            text = html_unescape(utterance.get("text", "")).strip()
            if not text:
                continue

            label = utterance.get("speaker", "")
            speaker = speaker_map.get(label, f"Speaker {label}" if label else "Speaker")
            turns.append((speaker, text))

        return html_unescape(episode.get("subtitle") or ""), turns


def write_transcript_page(episode, source_url, destination, permalink):
    transcript_html = fetch_text(source_url)

    preloaded_parser = PinecastPreloadedQueryParser()
    preloaded_parser.feed(transcript_html)
    subtitle, turns = preloaded_parser.transcript()

    if not turns:
        legacy_parser = PinecastTranscriptParser()
        legacy_parser.feed(transcript_html)
        subtitle = legacy_parser.subtitle
        turns = legacy_parser.turns

    if not turns:
        raise ValueError("No transcript turns were found on the Pinecast page.")

    page_title = f"Transcript: {episode['title']}"
    page_description = truncate_description(episode.get("description_text", ""))
    lines = [
        "---",
        "layout: default",
        f"title: {json.dumps(page_title, ensure_ascii=False)}",
        f"description: {json.dumps(page_description, ensure_ascii=False)}",
        "image: /_images/IROH_SocialLogo.png",
        f"permalink: {permalink}",
        "---",
        "",
        "{% include iroh-masthead.html %}",
        "",
        '<article class="transcript-page">',
        '  <header class="transcript-header">',
        f"    <p class=\"broadcast-number\">HBI transcript service</p>",
        f"    <h1>{html_escape(episode['title'])}</h1>",
    ]

    if subtitle:
        lines.append(
            f'    <p class="transcript-subtitle">{html_escape(subtitle)}</p>'
        )

    lines.extend(
        [
            '    <p class="broadcast-meta">',
            f"      {html_escape(display_date(episode['published']))}",
            (
                f"      &nbsp;|&nbsp; {html_escape(episode['duration'])}"
                if episode["duration"]
                else ""
            ),
            "    </p>",
            f'    <audio controls preload="metadata" src="{html_escape(episode["audio_url"], quote=True)}"></audio>',
            '    <p class="broadcast-links">',
            f'      <a href="{html_escape(source_url, quote=True)}">Original Pinecast transcript</a>',
            '      <span aria-hidden="true">|</span>',
            '      <a href="{{ \'/\' | relative_url }}">Return to IROH</a>',
            "    </p>",
            "  </header>",
            '  <div class="transcript-copy">',
            '    <p class="transcript-notice">This is an automatically generated transcript and may contain errors.</p>',
        ]
    )

    for speaker, paragraph in turns:
        lines.extend(
            [
                '    <div class="transcript-turn">',
                f'      <p class="transcript-speaker">{html_escape(speaker)}</p>',
                f"      <p>{html_escape(paragraph)}</p>",
                "    </div>",
            ]
        )

    lines.extend(["  </div>", "</article>", ""])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")


rss_xml = fetch_text(RSS_URL)
root = ET.fromstring(rss_xml)

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

    episode = {
        "title": get_text(item, "title"),
        "link": get_text(item, "link") or audio_url,
        "guid": get_text(item, "guid") or audio_url,
        "published": published,
        "duration": get_text(item, f"{ITUNES}duration"),
        "episode_number": get_text(item, f"{ITUNES}episode"),
        "episode_type": get_text(item, f"{ITUNES}episodeType"),
        "description_html": description,
        "description_text": make_description_text(description),
        "audio_url": audio_url,
        "audio_type": audio_type,
        "image_url": episode_image or channel_image,
        "transcript_source_url": find_transcript_url(description),
        "transcript_path": "",
        "_sort_time": sort_time,
    }

    if episode["transcript_source_url"]:
        transcript_slug = make_slug(episode["title"])
        transcript_file = TRANSCRIPT_DIRECTORY / transcript_slug / "index.md"
        transcript_permalink = f"/transcripts/{transcript_slug}/"

        if REFRESH_TRANSCRIPTS or not transcript_file.exists():
            try:
                write_transcript_page(
                    episode,
                    episode["transcript_source_url"],
                    transcript_file,
                    transcript_permalink,
                )
                print(f"Updated transcript: {episode['title']}")
            except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError) as error:
                print(f"Transcript unavailable for {episode['title']}: {error}")

        if transcript_file.exists():
            episode["transcript_path"] = transcript_permalink

    episodes.append(episode)

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
