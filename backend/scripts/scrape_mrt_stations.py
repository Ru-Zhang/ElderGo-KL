#!/usr/bin/env python3
"""
Discover and scrape all station pages on mrt.com.my.

Usage (from repo root):
  ./.venv311/bin/python backend/scripts/scrape_mrt_stations.py [--limit N]

Outputs:
  backend/data/mrt_stations_facilities.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BACKEND_DIR / "data" / "mrt_stations_facilities.csv"
INDEX_URL = "https://mrt.com.my/stations.htm"
BASE_URL = "https://mrt.com.my/"

UA = "Mozilla/5.0 ElderGo-KL/1.0 (+local research; contact: dev)"
DELAY_S = 0.4
TIMEOUT_S = 30.0

# Lower number = higher priority when a station appears in multiple sections.
LINE_PRIORITY = {
    "MRT Kajang Line": 0,
    "MRT Putrajaya Line": 1,
    "LRT Kelana Jaya Line": 2,
    "LRT Ampang Line": 3,
    "LRT Sri Petaling Line": 4,
    "KL Monorail Line": 5,
    "KTM Komuter Seremban Line": 6,
    "KTM Komuter Port Klang Line": 7,
    "RTS Link": 8,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("scrape_mrt")


def slugify_to_location_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return f"station:{slug}"


def fetch_soup(client: httpx.Client, url: str) -> BeautifulSoup:
    r = client.get(url, follow_redirects=True, timeout=TIMEOUT_S)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def discover_links(client: httpx.Client) -> list[dict]:
    """Return [{display_name, line, url}] for every station link on the index."""
    soup = fetch_soup(client, INDEX_URL)
    out: list[dict] = []
    for header in soup.find_all(string=re.compile(r"Stations in ")):
        line_name = re.sub(r"^Stations in\s*", "", header.strip())
        if not line_name:
            continue
        parent = header.parent
        table = parent.find_next("table") if parent else None
        if table is None:
            continue
        for a in table.find_all("a"):
            text = a.get_text(strip=True)
            href = a.get("href")
            if not text or not href:
                continue
            url = urljoin(BASE_URL, href)
            out.append({"display_name": text, "line": line_name, "url": url})
    return out


def group_candidates(links: list[dict]) -> dict[str, dict]:
    """Group links by location_id, keep sorted candidate URLs and line list."""
    grouped: dict[str, dict] = {}
    for link in links:
        loc_id = slugify_to_location_id(link["display_name"])
        bucket = grouped.setdefault(
            loc_id,
            {
                "location_id": loc_id,
                "display_name": link["display_name"],
                "lines": set(),
                "candidates": [],
            },
        )
        bucket["lines"].add(link["line"])
        if link["url"] not in [c["url"] for c in bucket["candidates"]]:
            bucket["candidates"].append({"url": link["url"], "line": link["line"]})

    for bucket in grouped.values():
        bucket["candidates"].sort(key=lambda c: LINE_PRIORITY.get(c["line"], 99))
    return grouped


def _normalize_facility_line(line: str) -> str | None:
    s = re.sub(r"^\s*[•\-\*]\s*", "", line.strip())
    s = re.sub(r"\s+", " ", s)
    return s or None


def extract_facilities(soup: BeautifulSoup) -> list[str]:
    header = soup.find("b", string=re.compile(r"^\s*Station Facilities\s*$"))
    if header is None:
        text_node = soup.find(string=re.compile(r"Station Facilities"))
        if text_node and getattr(text_node, "parent", None):
            header = text_node.parent if text_node.parent.name == "b" else None
    if header is None:
        return []
    table = header.find_next("table")
    if table is None:
        return []
    items: list[str] = []
    for td in table.find_all("td"):
        chunk = td.get_text("\n", strip=True)
        for raw in chunk.split("\n"):
            norm = _normalize_facility_line(raw)
            if norm and norm not in items:
                items.append(norm)
    return items


def extract_station_information(soup: BeautifulSoup) -> dict[str, str]:
    label = soup.find(string=re.compile(r"Station Information"))
    if not label:
        return {}
    start = label.parent if getattr(label, "parent", None) and label.parent.name == "p" else label
    table = start.find_next("table") if start else None
    if table is None:
        return {}
    rows: dict[str, str] = {}
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 2:
            continue
        key = re.sub(r"\s+", " ", tds[0].get_text(" ", strip=True))
        val = re.sub(r"\s+", " ", tds[1].get_text(" ", strip=True))
        if key:
            rows[key] = val
    return rows


def build_hours_summary(info: dict[str, str]) -> str | None:
    parts: list[str] = []
    if info.get("Station Open"):
        parts.append(f"Station open: {info['Station Open']}")
    if info.get("Station Closed"):
        parts.append(f"Station closed: {info['Station Closed']}")
    last_keys = sorted(k for k in info if k.strip().lower().startswith("last train"))
    for k in last_keys:
        parts.append(f"{k}: {info[k]}")
    return "\n".join(parts) if parts else None


def score(facilities: list[str], address: str | None, hours: str | None) -> int:
    """Higher score = richer page. Used to pick best candidate when station is multi-line."""
    return len(facilities) * 2 + (1 if address else 0) + (1 if hours else 0)


def scrape_one(
    client: httpx.Client, candidates: list[dict]
) -> tuple[list[str], str | None, str | None, str | None]:
    """Visit each candidate URL and merge the data they expose.

    facilities -> union (preserving first-seen order)
    address    -> first non-empty
    hours      -> first non-empty
    source_url -> the URL of the page that contributed the most fields
    """
    merged_facilities: list[str] = []
    address: str | None = None
    hours: str | None = None
    best_url: str | None = None
    best_score = -1

    for candidate in candidates:
        url = candidate["url"]
        try:
            soup = fetch_soup(client, url)
        except httpx.HTTPError as exc:
            log.warning("HTTP error on %s: %s", url, exc)
            continue

        page_facilities = extract_facilities(soup)
        info = extract_station_information(soup)
        page_address = info.get("Address") or None
        page_hours = build_hours_summary(info)

        for item in page_facilities:
            if item not in merged_facilities:
                merged_facilities.append(item)
        if address is None and page_address:
            address = page_address
        if hours is None and page_hours:
            hours = page_hours

        page_score = score(page_facilities, page_address, page_hours)
        if page_score > best_score:
            best_score = page_score
            best_url = url
        time.sleep(DELAY_S)

    if not (merged_facilities or address or hours):
        return [], None, None, None
    return merged_facilities, address, hours, best_url


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Limit stations for testing")
    args = parser.parse_args()

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict[str, str]] = []
    stats = {"total": 0, "with_data": 0, "empty": 0, "errors": 0}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with httpx.Client(headers={"User-Agent": UA}) as client:
        log.info("Discovering station links from %s", INDEX_URL)
        links = discover_links(client)
        grouped = group_candidates(links)
        log.info("Found %d unique stations across %d index entries", len(grouped), len(links))

        items = list(grouped.values())
        if args.limit > 0:
            items = items[: args.limit]
        stats["total"] = len(items)

        for idx, bucket in enumerate(items, start=1):
            loc_id = bucket["location_id"]
            display_name = bucket["display_name"]
            try:
                facilities, address, hours, source_url = scrape_one(client, bucket["candidates"])
            except Exception as exc:
                log.exception("Unexpected error on %s: %s", loc_id, exc)
                stats["errors"] += 1
                continue

            has_data = bool(facilities or address or hours)
            if has_data:
                stats["with_data"] += 1
            else:
                stats["empty"] += 1

            rows_out.append(
                {
                    "location_id": loc_id,
                    "display_name": display_name,
                    "lines": "; ".join(sorted(bucket["lines"])),
                    "source_url": source_url or bucket["candidates"][0]["url"],
                    "facilities_json": json.dumps(facilities, ensure_ascii=False),
                    "address": address or "",
                    "hours_summary": hours or "",
                    "scraped_at": now,
                }
            )

            log.info(
                "[%d/%d] %s -> %s facilities, addr=%s, hours=%s",
                idx,
                len(items),
                display_name,
                len(facilities),
                "y" if address else "n",
                "y" if hours else "n",
            )
            time.sleep(DELAY_S)

    rows_out.sort(key=lambda r: r["location_id"])
    with DATA_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "location_id",
                "display_name",
                "lines",
                "source_url",
                "facilities_json",
                "address",
                "hours_summary",
                "scraped_at",
            ],
        )
        w.writeheader()
        w.writerows(rows_out)

    log.info("Wrote %d rows to %s", len(rows_out), DATA_PATH)
    log.info(
        "Stats: total=%d with_data=%d empty=%d errors=%d",
        stats["total"],
        stats["with_data"],
        stats["empty"],
        stats["errors"],
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
