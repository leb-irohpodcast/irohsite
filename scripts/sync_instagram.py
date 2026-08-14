#!/usr/bin/env python3

"""Cache the latest official IROH Instagram posts for the Jekyll gallery.

The official Instagram API needs an access token, supplied only through the
INSTAGRAM_ACCESS_TOKEN environment variable. The token is sent as a bearer
header and is never written to the repository or generated data.
"""

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


PROFILE_URL = "https://www.instagram.com/iroh_show/"
OUTPUT_FILE = Path("_data/instagram_posts.json")
IMAGE_DIRECTORY = Path("_images/instagram")
API_BASE = os.environ.get("INSTAGRAM_API_BASE", "https://graph.instagram.com").rstrip("/")
API_VERSION = os.environ.get("INSTAGRAM_API_VERSION", "").strip().strip("/")
ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "").strip()
GALLERY_LIMIT = max(1, min(int(os.environ.get("INSTAGRAM_GALLERY_LIMIT", "6")), 12))

MEDIA_FIELDS = ",".join(
    [
        "id",
        "caption",
        "media_type",
        "media_product_type",
        "media_url",
        "permalink",
        "thumbnail_url",
        "timestamp",
        "username",
        "children{media_type,media_url,thumbnail_url}",
    ]
)


def api_url(path, parameters):
    base = f"{API_BASE}/{API_VERSION}" if API_VERSION else API_BASE
    return f"{base}/{path.lstrip('/')}?{urlencode(parameters)}"


def fetch_json(url):
    request = Request(
        url,
        headers={
            "Authorization": f"Bearer {ACCESS_TOKEN}",
            "User-Agent": "IROH-Website-Instagram-Sync/1.0",
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_image(url):
    request = Request(
        url,
        headers={"User-Agent": "IROH-Website-Instagram-Sync/1.0"},
    )
    with urlopen(request, timeout=45) as response:
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
        return response.read(), content_type


def load_existing_posts():
    if not OUTPUT_FILE.exists():
        return {}

    try:
        payload = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}

    return {
        str(post.get("id")): post
        for post in (payload.get("posts") or [])
        if post.get("id")
    }


def post_key(media):
    permalink = str(media.get("permalink") or "").rstrip("/")
    if permalink:
        candidate = urlparse(permalink).path.rstrip("/").rsplit("/", 1)[-1]
        if candidate:
            return candidate
    return str(media.get("id") or "")


def media_image_url(media):
    media_type = str(media.get("media_type") or "").upper()
    if media_type == "VIDEO":
        return media.get("thumbnail_url") or media.get("media_url") or ""
    if media_type == "CAROUSEL_ALBUM":
        children = (media.get("children") or {}).get("data") or []
        for child in children:
            image_url = child.get("thumbnail_url") or child.get("media_url")
            if image_url:
                return image_url
    return media.get("media_url") or media.get("thumbnail_url") or ""


def kind_label(media):
    media_type = str(media.get("media_type") or "").upper()
    product_type = str(media.get("media_product_type") or "").upper()
    if media_type == "CAROUSEL_ALBUM":
        return "PHOTO SET"
    if media_type == "VIDEO" or product_type == "REELS":
        return "VIDEO"
    return "PHOTO"


def title_from_caption(caption, label):
    for line in caption.splitlines():
        candidate = re.sub(r"\s+", " ", line).strip(" -")
        if not candidate or candidate.startswith("#"):
            continue
        if len(candidate) > 64:
            candidate = candidate[:61].rstrip() + "..."
        return candidate
    return f"{label.title()} from the HBI Picture Wire"


def extension_for(content_type):
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }.get(content_type, ".jpg")


def local_image(media, key, published, existing):
    existing_path = str(existing.get("image") or "")
    if existing_path and Path(existing_path.lstrip("/")).exists():
        return existing_path

    remote_url = media_image_url(media)
    if not remote_url:
        return ""

    image_bytes, content_type = fetch_image(remote_url)
    safe_key = re.sub(r"[^a-zA-Z0-9_-]+", "-", key).strip("-") or "post"
    date_prefix = str(published or "")[:10] or "undated"
    destination = IMAGE_DIRECTORY / f"{date_prefix}-{safe_key}{extension_for(content_type)}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(image_bytes)
    print(f"Cached Instagram preview: {destination}")
    return f"/{destination.as_posix()}"


def update_instagram_gallery():
    if not ACCESS_TOKEN:
        print(
            "INSTAGRAM_ACCESS_TOKEN is not configured; keeping the existing "
            "Instagram gallery unchanged."
        )
        return

    payload = fetch_json(
        api_url(
            "me/media",
            {
                "fields": MEDIA_FIELDS,
                "limit": max(GALLERY_LIMIT, 8),
            },
        )
    )
    existing_posts = load_existing_posts()
    posts = []

    for media in payload.get("data") or []:
        key = post_key(media)
        permalink = str(media.get("permalink") or "").strip()
        published = str(media.get("timestamp") or "").strip()
        caption = str(media.get("caption") or "").strip()
        existing = existing_posts.get(key, {})
        label = kind_label(media)

        if not key or not permalink or not published:
            continue

        image = local_image(media, key, published, existing)
        if not image:
            continue

        posts.append(
            {
                "id": key,
                "published": published,
                "kind_label": label,
                "bureau": existing.get("bureau", ""),
                "title": existing.get("title") or title_from_caption(caption, label),
                "caption": caption,
                "author": existing.get("author", ""),
                "url": permalink,
                "image": image,
                "alt": existing.get("alt", ""),
            }
        )

        if len(posts) == GALLERY_LIMIT:
            break

    if not posts:
        raise RuntimeError("Instagram returned no usable public media.")

    gallery = {
        "source_name": "IROH on Instagram",
        "source_url": PROFILE_URL,
        "handle": "@iroh_show",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "posts": posts,
    }
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(gallery, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Updated {OUTPUT_FILE} with {len(posts)} Instagram posts.")


if __name__ == "__main__":
    update_instagram_gallery()
