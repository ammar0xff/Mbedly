"""Mbedly core engine.

Pure logic layer - keeps all download/extraction functionality in one place so
the TUI, future Flutter backend, or any other client can reuse it.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import yt_dlp

APP_NAME = "Mbedly"
USER_AGENT = (
    "Mbedly/2.0 (+https://github.com/ammar0xff/Mbedly) "
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0 Safari/537.36"
)

RECOGNIZED_KINDS = ("youtube", "facebook", "livi-video", "m3u8", "mp4")

QUALITY_HEIGHTS = {
    "144p": 144,
    "360p": 360,
    "480p": 480,
    "720p": 720,
    "1080p": 1080,
    "2k": 1440,
    "4k": 2160,
}

QUALITIES = tuple(QUALITY_HEIGHTS.keys()) + ("mp3",)


def format_for(quality: str) -> str:
    """Map a user quality label to a yt-dlp format selector."""
    if quality == "mp3":
        return "bestaudio/best"
    height = QUALITY_HEIGHTS[quality]
    return (
        f"bestvideo[height<={height}][ext=mp4][vcodec^=avc]"
        f"+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/"
        f"best[height<={height}]/best"
    )


@dataclass
class MediaItem:
    """A downloadable media source discovered on a page."""

    url: str
    kind: str = "other"
    title: str = ""
    channel: str = ""


# --------------------------------------------------------------------------
# HTTP helpers
# --------------------------------------------------------------------------

def fetch(url: str, cookie: Optional[str] = None, timeout: int = 25) -> str:
    """Fetch a URL and return its body as text."""
    headers = {"User-Agent": USER_AGENT}
    if cookie:
        headers["Cookie"] = cookie
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


# --------------------------------------------------------------------------
# Link extraction
# --------------------------------------------------------------------------

def extract_links(html: str) -> list[str]:
    """Pull every raw http(s) URL out of arbitrary HTML/text.

    Mirrors the original bash scraper: split on quote/delimiter characters,
    cut everything before the http prefix, drop noise records and deduplicate.
    """
    found: set[str] = set()
    for chunk in re.split(r"[\s\"'<>`\[\]()\\]+", html):
        m = re.search(r"https?://\S+", chunk)
        if m:
            url = m.group(0).rstrip(".,;:!?)]'\"")
            if "channel" in url or "Quickbooks" in url:
                continue
            found.add(url)
    return sorted(found)


def classify(url: str) -> str:
    """Classify a URL into a supported media kind."""
    if re.search(r"youtu\.be|youtube\.com", url):
        return "youtube"
    if "liiivideo.com" in url and "embed" in url:
        return "livi-video"
    if "facebook.com" in url and re.search(r"/watch/?\?v=", url):
        return "facebook"
    if url.lower().startswith(("http://", "https://")) and url.lower().rstrip("/").endswith(".mp4"):
        return "mp4"
    if url.lower().startswith(("http://", "https://")) and url.lower().rstrip("/").endswith(".m3u8"):
        return "m3u8"
    return "other"


# --------------------------------------------------------------------------
# YouTube helpers
# --------------------------------------------------------------------------

_YOUTUBE_PATTERNS = (
    r"youtube\.com/watch\?.*?v=([\w-]{11})",
    r"youtu\.be/([\w-]{11})",
    r"youtube\.com/embed/([\w-]{11})",
    r"youtube\.com/shorts/([\w-]{11})",
    r"youtube\.com/v/([\w-]{11})",
    r"youtube\.com/live/([\w-]{11})",
)


def youtube_id(url: str) -> Optional[str]:
    """Extract an 11-character YouTube video id from any URL shape."""
    for pattern in _YOUTUBE_PATTERNS:
        m = re.search(pattern, url)
        if m:
            return m.group(1)
    return None


def youtube_meta(video_id: str) -> tuple[str, str]:
    """Best-effort title/channel lookup via the oEmbed endpoint."""
    api = (
        "https://www.youtube.com/oembed"
        f"?url=https%3A//youtube.com/watch%3Fv%3D{video_id}&format=json"
    )
    try:
        data = json.loads(fetch(api, timeout=12))
        return data.get("title", ""), data.get("author_name", "")
    except Exception:
        return "", ""


# --------------------------------------------------------------------------
# Course / site scrapers
# --------------------------------------------------------------------------

def maharatech_scrape(url: str, cookie: Optional[str] = None) -> list[MediaItem]:
    """Extract the YouTube lectures embedded inside a Mahara-Tech course."""
    headers = {"Cookie": cookie} if cookie else None
    items: list[MediaItem] = []
    seen: set[str] = set()

    course_pages = [
        link
        for link in extract_links(fetch(url))
        if "hvp" in link and "image" not in link
    ]

    for page in course_pages:
        page_html = fetch(page, cookie)
        links = extract_links(page_html)
        for link in links:
            if "youtu" not in link:
                continue
            if link in seen:
                continue
            seen.add(link)
            item = make_item(link)
            items.append(item)

    return items


def make_item(url: str) -> MediaItem:
    """Classify a URL and attach metadata where cheaply available."""
    kind = classify(url)
    item = MediaItem(url=url, kind=kind)
    if kind == "youtube":
        vid = youtube_id(url)
        if vid:
            item.title, item.channel = youtube_meta(vid)
    return item


def is_maharatech_course(url: str) -> bool:
    return "maharatech" in url and "course" in url


def scrape(url: str, cookie: Optional[str] = None) -> list[MediaItem]:
    """Full extraction pipeline: URL -> list of supported media items."""
    if is_maharatech_course(url):
        items = maharatech_scrape(url, cookie)
        if items:
            return items

    # Direct media/video link?
    if classify(url) in RECOGNIZED_KINDS:
        return [make_item(url)]

    # Generic page: scrape for embedded media.
    html = fetch(url, cookie)
    items: list[MediaItem] = []
    seen: set[str] = set()
    for link in extract_links(html):
        if classify(link) not in RECOGNIZED_KINDS:
            continue
        if link in seen:
            continue
        seen.add(link)
        items.append(make_item(link))
    return items


def resolve_meta(item: MediaItem) -> tuple[str, str]:
    """Best-effort (title, channel) for any media item.

    YouTube uses the cheap oEmbed lookup first, then falls back to a full
    yt-dlp metadata probe (also covers direct .mp4 files, HLS streams, ...).
    """
    if item.title:
        return item.title, item.channel
    if item.kind == "youtube":
        vid = youtube_id(item.url)
        if vid:
            title, channel = youtube_meta(vid)
            if title:
                return title, channel
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(item.url, download=False)
            title = str(info.get("title") or "") or item.url
            channel = str(info.get("channel") or info.get("uploader") or "")
            return title, channel or item.channel
    except Exception:
        return item.title or item.url, item.channel


def resolve_title(item: MediaItem) -> str:
    """Best-effort human readable title for any media item."""
    return resolve_meta(item)[0]


# --------------------------------------------------------------------------
# Downloading
# --------------------------------------------------------------------------

def download(
    url: str,
    quality: str = "1080p",
    output_dir: str | Path = "downloads",
    progress_cb: Optional[Callable[[dict], None]] = None,
) -> str:
    """Download one media URL at the requested quality.

    Returns the absolute path of the produced file (as reported by yt-dlp).
    """
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    outtmpl = str(outdir / "%(title).200B [%(id)s].%(ext)s")

    opts: dict = {
        "format": format_for(quality),
        "outtmpl": outtmpl,
        "noplaylist": True,
        "ignoreerrors": False,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "continuedl": True,
        "progress_hooks": [progress_cb] if progress_cb else [],
        "merge_output_format": "mp4" if quality != "mp3" else None,
        "http_headers": {"User-Agent": USER_AGENT},
        "extractor_args": {"generic": {"impersonate": ["chrome"]}},
    }
    if os.environ.get("MBEDLY_FFMPEG"):
        opts["ffmpeg_location"] = os.environ["MBEDLY_FFMPEG"]
    if quality == "mp3":
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]

    if not shutil.which("ffmpeg") and not os.environ.get("MBEDLY_FFMPEG"):
        msg = (
            "ffmpeg was not found on PATH. Install it for merged video/audio, "
            "mp3 conversion, and m3u8 support "
            "(apt install ffmpeg | brew install ffmpeg | winget install ffmpeg)."
        )
        raise RuntimeError(msg)

    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    return str(ydl.prepare_filename(info))


# --------------------------------------------------------------------------
# History
# --------------------------------------------------------------------------

def history_path() -> Path:
    return Path.home() / ".mbedly" / "history.json"


def record_history(entry: dict) -> None:
    """Append a download record to the local history log (kept to 50)."""
    import datetime

    path = history_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    rows: list = []
    if path.exists():
        try:
            rows = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            rows = []
    entry["at"] = datetime.datetime.now().isoformat(timespec="seconds")
    rows.append(entry)
    path.write_text(json.dumps(rows[-50:], indent=2, ensure_ascii=False), encoding="utf-8")