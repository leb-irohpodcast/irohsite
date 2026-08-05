#!/usr/bin/env python3

import json
import os
import re
import unicodedata
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from html import escape as html_escape
from html import unescape as html_unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET


RSS_URL = "https://pinecast.com/feed/iroh"
OUTPUT_FILE = Path("_data/episodes.json")
BULLETIN_OUTPUT_FILE = Path("_data/network_bulletin.json")
POLL_BANK_FILE = Path("_data/polls.json")
CURRENT_POLL_FILE = Path("_data/current_poll.json")
TRANSCRIPT_DIRECTORY = Path("transcripts")
BROADCAST_DIRECTORY = Path("broadcasts")
POST_DIRECTORY = Path("_posts")
REFRESH_TRANSCRIPTS = os.environ.get("REFRESH_TRANSCRIPTS") == "1"

BLUESKY_HANDLE = "irohpodcast.com"
BLUESKY_FEED_URL = "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
BLUESKY_BULLETIN_LIMIT = 3

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


def bluesky_post_url(uri):
    record_key = uri.rsplit("/", 1)[-1]
    if not record_key or record_key == uri:
        return f"https://bsky.app/profile/{BLUESKY_HANDLE}"
    return f"https://bsky.app/profile/{BLUESKY_HANDLE}/post/{record_key}"


def update_network_bulletin():
    query = urlencode(
        {
            "actor": BLUESKY_HANDLE,
            "filter": "posts_no_replies",
            "limit": 12,
        }
    )
    payload = json.loads(fetch_text(f"{BLUESKY_FEED_URL}?{query}"))
    posts = []

    for entry in payload.get("feed", []):
        post = entry.get("post") or {}
        author = post.get("author") or {}
        record = post.get("record") or {}

        # The author feed may contain reposts. The bulletin should contain only
        # original public dispatches published by the IROH account.
        if author.get("handle") != BLUESKY_HANDLE or entry.get("reason"):
            continue
        if record.get("reply"):
            continue

        text = html_unescape(record.get("text") or "").strip()
        created_at = record.get("createdAt") or post.get("indexedAt") or ""
        uri = post.get("uri") or ""

        if not text or not created_at:
            continue

        posts.append(
            {
                "text": text,
                "created_at": created_at,
                "url": bluesky_post_url(uri),
            }
        )

        if len(posts) == BLUESKY_BULLETIN_LIMIT:
            break

    bulletin = {
        "source_name": "IROH on Bluesky",
        "source_url": f"https://bsky.app/profile/{BLUESKY_HANDLE}",
        "updated_at": posts[0]["created_at"] if posts else "",
        "posts": posts,
    }

    BULLETIN_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    BULLETIN_OUTPUT_FILE.write_text(
        json.dumps(bulletin, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Updated {BULLETIN_OUTPUT_FILE} with {len(posts)} Bluesky dispatches."
    )


def write_current_poll(current_poll):
    CURRENT_POLL_FILE.parent.mkdir(parents=True, exist_ok=True)
    CURRENT_POLL_FILE.write_text(
        json.dumps(current_poll, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    status = current_poll["id"] if current_poll["enabled"] else "disabled"
    print(f"Updated {CURRENT_POLL_FILE}; listener poll is {status}.")


def disabled_poll():
    return {
        "enabled": False,
        "id": "",
        "starts": "",
        "question": "",
        "options": [],
    }


def update_current_poll():
    if not POLL_BANK_FILE.exists():
        write_current_poll(disabled_poll())
        return

    bank = json.loads(POLL_BANK_FILE.read_text(encoding="utf-8"))
    enabled = bank.get("enabled") is True

    # While the bank is being assembled, the disabled switch keeps the poll
    # off the site and allows incomplete future drafts without breaking builds.
    if not enabled:
        write_current_poll(disabled_poll())
        return

    scheduled_polls = bank.get("polls") or []
    eligible_polls = []
    poll_ids = set()

    for poll in scheduled_polls:
        poll_id = str(poll.get("id") or "").strip()
        starts = str(poll.get("starts") or "").strip()
        question = str(poll.get("question") or "").strip()
        options = [
            str(option).strip()
            for option in (poll.get("options") or [])
            if str(option).strip()
        ]

        if not poll_id or not starts or not question or len(options) < 2:
            raise ValueError(
                "Each scheduled poll needs an id, starts date, question, "
                "and at least two options."
            )
        if poll_id in poll_ids:
            raise ValueError(f"Duplicate poll id: {poll_id}")
        poll_ids.add(poll_id)

        try:
            starts_date = date.fromisoformat(starts)
        except ValueError as error:
            raise ValueError(
                f"Poll {poll_id} has an invalid starts date; use YYYY-MM-DD."
            ) from error

        if starts_date <= datetime.now(timezone.utc).date():
            eligible_polls.append(
                {
                    "id": poll_id,
                    "starts": starts,
                    "question": question,
                    "options": options,
                    "_starts_date": starts_date,
                }
            )

    eligible_polls.sort(key=lambda poll: poll["_starts_date"])
    selected_poll = eligible_polls[-1] if enabled and eligible_polls else None

    if selected_poll:
        del selected_poll["_starts_date"]
        current_poll = {"enabled": True, **selected_poll}
    else:
        current_poll = disabled_poll()

    write_current_poll(current_poll)


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


def iso_duration(value):
    value = str(value or "").strip()
    if not value:
        return ""

    try:
        if value.isdigit():
            total_seconds = int(value)
        else:
            parts = [int(part) for part in value.split(":")]
            if len(parts) == 3:
                hours, minutes, seconds = parts
            elif len(parts) == 2:
                hours = 0
                minutes, seconds = parts
            else:
                return ""
            total_seconds = hours * 3600 + minutes * 60 + seconds
    except ValueError:
        return ""

    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    pieces = ["PT"]
    if hours:
        pieces.append(f"{hours}H")
    if minutes:
        pieces.append(f"{minutes}M")
    if seconds or len(pieces) == 1:
        pieces.append(f"{seconds}S")
    return "".join(pieces)


def episode_number_key(episode_number, title):
    value = str(episode_number or "").strip()
    if value.isdigit():
        return str(int(value))

    match = re.search(r"\bEpisode\s+0*(\d+)\b", title or "", flags=re.IGNORECASE)
    return str(int(match.group(1))) if match else ""


def find_archived_transcripts():
    transcripts = {}

    for post in POST_DIRECTORY.glob("*.md"):
        text = post.read_text(encoding="utf-8", errors="replace")
        if not text.startswith("---"):
            continue

        front_matter_end = text.find("\n---", 3)
        if front_matter_end == -1:
            continue

        front_matter = text[3:front_matter_end]
        episode_match = re.search(
            r'^iroh_episode:\s*["\']?(\d+)["\']?\s*$',
            front_matter,
            flags=re.MULTILINE,
        )
        permalink_match = re.search(
            r'^permalink:\s*["\']?([^"\'\s]+)["\']?\s*$',
            front_matter,
            flags=re.MULTILINE,
        )

        if episode_match and permalink_match:
            transcripts[str(int(episode_match.group(1)))] = permalink_match.group(1)

    return transcripts


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


def write_broadcast_page(episode):
    broadcast_slug = make_slug(episode["title"])
    destination = BROADCAST_DIRECTORY / broadcast_slug / "index.md"
    description = truncate_description(episode.get("description_text", ""))
    if not description:
        description = (
            f"Listen to {episode['title']} from The International Race of "
            "Hammpions Show."
        )

    lines = [
        "---",
        "layout: broadcast",
        f"title: {json.dumps(episode['title'], ensure_ascii=False)}",
        f"description: {json.dumps(description, ensure_ascii=False)}",
        "image: /_images/IROH_SocialLogo.png",
        f"permalink: {episode['episode_path']}",
        "podcast_episode: true",
        f"episode_title: {json.dumps(episode['title'], ensure_ascii=False)}",
        f"episode_number: {json.dumps(episode['episode_number'], ensure_ascii=False)}",
        f"episode_type: {json.dumps(episode['episode_type'], ensure_ascii=False)}",
        f"published: {json.dumps(episode['published'], ensure_ascii=False)}",
        f"duration: {json.dumps(episode['duration'], ensure_ascii=False)}",
        f"duration_iso: {json.dumps(episode['duration_iso'], ensure_ascii=False)}",
        f"audio_url: {json.dumps(episode['audio_url'], ensure_ascii=False)}",
        f"audio_type: {json.dumps(episode['audio_type'], ensure_ascii=False)}",
        f"external_url: {json.dumps(episode['link'], ensure_ascii=False)}",
        f"transcript_path: {json.dumps(episode['transcript_path'], ensure_ascii=False)}",
        f"transcript_source_url: {json.dumps(episode['transcript_source_url'], ensure_ascii=False)}",
        "---",
        "",
    ]

    if episode.get("description_html"):
        lines.append(episode["description_html"])
    else:
        lines.append(
            f"<p>{html_escape(description)}</p>"
        )

    lines.append("")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    print(f"Updated broadcast page: {episode['title']}")
    return destination


def remove_stale_broadcast_pages(active_pages):
    if not BROADCAST_DIRECTORY.exists():
        return

    for page in BROADCAST_DIRECTORY.glob("*/index.md"):
        if page in active_pages:
            continue

        text = page.read_text(encoding="utf-8", errors="replace")
        front_matter = text.split("---", 2)[1] if text.startswith("---") else ""
        if "layout: broadcast" not in front_matter:
            continue
        if "podcast_episode: true" not in front_matter:
            continue

        page.unlink()
        if not any(page.parent.iterdir()):
            page.parent.rmdir()
        print(f"Removed stale broadcast page: {page}")


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
archived_transcripts = find_archived_transcripts()
active_broadcast_pages = set()
episode_paths = set()

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

    episode_title = get_text(item, "title")
    episode_slug = make_slug(episode_title)

    episode = {
        "title": episode_title,
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
        "episode_path": f"/broadcasts/{episode_slug}/",
        "_sort_time": sort_time,
    }
    episode["duration_iso"] = iso_duration(episode["duration"])
    if episode["episode_path"] in episode_paths:
        raise ValueError(f"Duplicate broadcast page path: {episode['episode_path']}")
    episode_paths.add(episode["episode_path"])

    episode_key = episode_number_key(episode["episode_number"], episode["title"])
    if not episode["episode_number"] and episode_key:
        episode["episode_number"] = episode_key
    archived_transcript_path = archived_transcripts.get(episode_key, "")

    if archived_transcript_path:
        episode["transcript_path"] = archived_transcript_path
    elif episode["transcript_source_url"]:
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

    active_broadcast_pages.add(write_broadcast_page(episode))

    episodes.append(episode)

remove_stale_broadcast_pages(active_broadcast_pages)

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

try:
    update_network_bulletin()
except (HTTPError, URLError, TimeoutError, UnicodeError, ValueError, json.JSONDecodeError) as error:
    # A temporary Bluesky outage should not prevent episode and transcript
    # updates. Preserve the last successful bulletin already in the repository.
    print(f"Network bulletin unavailable; keeping the previous copy: {error}")

update_current_poll()
