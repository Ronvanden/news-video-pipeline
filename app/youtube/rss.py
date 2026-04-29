"""Neueste Videos per offiziellem YouTube-Atom-Feed (ohne API-Key)."""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Tuple

import httpx

logger = logging.getLogger(__name__)

_ATOM_NS = "http://www.w3.org/2005/Atom"
_MEDIA_NS = "http://search.yahoo.com/mrss/"
_NS = {
    "atom": _ATOM_NS,
    # YouTube liefert je nach Feed v5 oder 2015; videoId daher per Suffix-Lookup.
    "yt": "http://www.youtube.com/xml/schemas/v5",
    "media": "http://search.yahoo.com/mrss/",
}

_DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NewsToVideo-ChannelDiscovery/1.0; +https://github.com/) "
        "AppleWebKit/537.36 (KHTML, like Gecko)"
    ),
    "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de,en;q=0.9",
}
_HTTP_TIMEOUT = httpx.Timeout(25.0, connect=15.0)


@dataclass
class RssVideoEntry:
    title: str
    video_id: str
    url: str
    published_at: str
    duration_seconds: int | None


def _entry_video_id(entry: ET.Element) -> str:
    """YouTube namespaces: v5 und 2015 — lokaler Name videoId."""
    for child in list(entry):
        if child.tag.endswith("}videoId") or child.tag == "videoId":
            t = (child.text or "").strip()
            if t:
                return t
    return ""


def _parse_duration(entry: ET.Element) -> int | None:
    for el in entry.iter():
        if el.tag == f"{{{_MEDIA_NS}}}content" or el.tag.endswith("}content"):
            dur = el.get("duration")
            if dur is not None and str(dur).isdigit():
                return int(dur)
    return None


def fetch_channel_feed_entries(channel_id: str, max_results: int) -> Tuple[str, List[RssVideoEntry], List[str]]:
    """
    Ruft https://www.youtube.com/feeds/videos.xml?channel_id=… ab.
    Gibt (feed_title, entries, warnings) zurück.
    """
    warnings: List[str] = []
    feed_title = ""
    entries: List[RssVideoEntry] = []
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    try:
        with httpx.Client(timeout=_HTTP_TIMEOUT, headers=_DEFAULT_HEADERS, follow_redirects=True) as client:
            r = client.get(url)
        if r.status_code != 200:
            warnings.append(f"YouTube-RSS nicht erreichbar (HTTP {r.status_code}).")
            return feed_title, entries, warnings
        root = ET.fromstring(r.content)
    except ET.ParseError as e:
        logger.error("RSS XML parse error: %s", type(e).__name__)
        warnings.append("RSS-Antwort konnte nicht als XML gelesen werden.")
        return feed_title, entries, warnings
    except httpx.HTTPError as e:
        warnings.append(f"Netzwerkfehler beim RSS-Abruf: {type(e).__name__}")
        return feed_title, entries, warnings

    title_el = root.find(f"{{{_ATOM_NS}}}title")
    if title_el is None:
        title_el = root.find("atom:title", _NS)
    if title_el is not None and title_el.text:
        feed_title = title_el.text.strip()

    entry_els = root.findall(f"{{{_ATOM_NS}}}entry")
    if not entry_els:
        entry_els = root.findall("atom:entry", _NS)

    for entry in entry_els:
        if len(entries) >= max_results:
            break
        video_id = _entry_video_id(entry)
        if not video_id:
            continue
        title_ = entry.find(f"{{{_ATOM_NS}}}title")
        published_el = entry.find(f"{{{_ATOM_NS}}}published")
        link_els = entry.findall(f"{{{_ATOM_NS}}}link")
        title_text = (title_.text or "").strip() if title_ is not None else ""
        published = (published_el.text or "").strip() if published_el is not None else ""
        href = ""
        for link_el in link_els:
            h = (link_el.get("href") or "").strip()
            if h:
                href = h
                break
        if not href and video_id:
            href = f"https://www.youtube.com/watch?v={video_id}"
        dur = _parse_duration(entry)
        entries.append(
            RssVideoEntry(
                title=title_text,
                video_id=video_id,
                url=href,
                published_at=published,
                duration_seconds=dur,
            )
        )

    if not entries:
        warnings.append("RSS-Feed enthielt keine Video-Einträge (ungültige Channel-ID oder leerer Feed).")

    return feed_title, entries, warnings
