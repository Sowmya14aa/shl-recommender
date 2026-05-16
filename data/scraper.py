"""
scraper.py — Scrapes SHL Individual Test Solutions catalog.

CONFIRMED page structure (checked live May 2026):
- Base URL: https://www.shl.com/products/product-catalog/
- Individual Tests filter: ?start=0&type=1
- Pagination: start=0, 12, 24, ... 372  (32 pages total)
- Each row: name + link | remote_testing | adaptive_irt | test_type letters
- Detail page URL pattern: /products/product-catalog/view/<slug>/

Run ONCE to generate catalog.json:
    python data/scraper.py
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
import os

# ── Constants ─────────────────────────────────────────────────────────────────

BASE_URL      = "https://www.shl.com"
CATALOG_URL   = "https://www.shl.com/products/product-catalog/"
OUTPUT_PATH   = os.path.join(os.path.dirname(__file__), "catalog.json")
DELAY         = 1.2   # seconds between requests — be polite to SHL's servers

# SHL test type code → full label (from the legend on the catalog page)
TEST_TYPE_LABELS = {
    "A": "Ability & Aptitude",
    "B": "Biodata & Situational Judgement",
    "C": "Competencies",
    "D": "Development & 360",
    "E": "Assessment Exercises",
    "K": "Knowledge & Skills",
    "P": "Personality & Behavior",
    "S": "Simulations",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
}

# ── Helpers ───────────────────────────────────────────────────────────────────

def fetch(url: str) -> BeautifulSoup:
    """GET a URL and return parsed BeautifulSoup. Raises on HTTP error."""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def expand_test_types(codes_str: str) -> str:
    """
    'K P A'  →  'Knowledge & Skills, Personality & Behavior, Ability & Aptitude'
    Handles the space-separated letter codes SHL uses in the table.
    """
    codes  = codes_str.upper().split()
    labels = [TEST_TYPE_LABELS.get(c, c) for c in codes if c]
    return ", ".join(labels) if labels else ""


# ── Catalog list pages ────────────────────────────────────────────────────────

def scrape_list_page(start: int) -> list[dict]:
    """
    Scrape one paginated page of Individual Test Solutions.
    Returns a list of dicts with: name, url, remote_testing, adaptive_irt, test_type_codes.
    Returns [] when the page has no Individual Test Solutions table.
    """
    url  = f"{CATALOG_URL}?start={start}&type=1"
    soup = fetch(url)
    time.sleep(DELAY)

    assessments = []

    # The page has TWO tables: Pre-packaged Job Solutions AND Individual Test Solutions.
    # We only want the second one.  We identify it by its header text.
    tables = soup.find_all("table")

    target_table = None
    for table in tables:
        header = table.find("th")
        if header and "Individual Test Solutions" in header.get_text():
            target_table = table
            break

    if not target_table:
        return []

    rows = target_table.find_all("tr")[1:]  # skip the header row

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 4:
            continue

        # Column 0: name + link
        link_tag = cols[0].find("a")
        if not link_tag:
            continue

        name = link_tag.get_text(strip=True)
        href = link_tag.get("href", "")
        # href is already absolute on SHL's site, but handle relative just in case
        full_url = href if href.startswith("http") else BASE_URL + href

        # Column 1: Remote Testing  (contains a <span> or checkmark if supported)
        remote = "Yes" if cols[1].find(["span", "img", "i"]) else "No"

        # Column 2: Adaptive / IRT
        adaptive = "Yes" if cols[2].find(["span", "img", "i"]) else "No"

        # Column 3: Test type — rendered as letter codes separated by spaces
        type_codes = cols[3].get_text(separator=" ", strip=True)   # e.g. "K" or "A P"

        assessments.append({
            "name"           : name,
            "url"            : full_url,
            "remote_testing" : remote,
            "adaptive_irt"   : adaptive,
            "test_type"      : expand_test_types(type_codes),
            "test_type_codes": type_codes.upper(),   # keep raw codes too
        })

    return assessments


def scrape_all_list_pages() -> list[dict]:
    """
    Iterate through all 32 pages (start=0 to start=372, step=12).
    Deduplicate by URL.
    """
    all_items  : list[dict] = []
    seen_urls  : set[str]   = set()

    total_pages = 32   # confirmed from pagination: last page is start=372

    print(f"Scraping {total_pages} pages of Individual Test Solutions...")
    print("=" * 60)

    for page_num in range(total_pages):
        start = page_num * 12
        url   = f"{CATALOG_URL}?start={start}&type=1"
        print(f"  Page {page_num + 1:>2}/{total_pages}  (start={start})  {url}")

        try:
            items = scrape_list_page(start)
        except Exception as exc:
            print(f"    ✗ Error: {exc} — skipping")
            continue

        new = 0
        for item in items:
            if item["url"] not in seen_urls:
                seen_urls.add(item["url"])
                all_items.append(item)
                new += 1

        print(f"    ✓ {new} new items  (running total: {len(all_items)})")

    return all_items


# ── Detail pages ──────────────────────────────────────────────────────────────

def scrape_detail(url: str) -> dict:
    """
    Visit an individual assessment detail page and extract:
      - description  (first meaningful paragraph)
      - duration     (e.g. "20 minutes")

    Returns a dict; values are empty strings if not found.
    """
    result = {"description": "", "duration": ""}

    try:
        soup = fetch(url)
        time.sleep(DELAY)

        # ── Description ────────────────────────────────────────────────
        # SHL detail pages have the product description in <p> tags
        # inside a main content area. We skip boilerplate short paras.
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            # Skip cookie notices, nav text, and very short lines
            if len(text) > 80 and "cookie" not in text.lower():
                result["description"] = text
                break

        # ── Duration ───────────────────────────────────────────────────
        page_text = soup.get_text(" ", strip=True)
        m = re.search(r'(\d[\d\s\-–]*)\s*minutes?', page_text, re.IGNORECASE)
        if m:
            result["duration"] = m.group(0).strip()

    except Exception as exc:
        print(f"    ⚠ Could not fetch detail page {url}: {exc}")

    return result


def enrich_all(assessments: list[dict]) -> list[dict]:
    """
    Add description + duration to every assessment by visiting its detail page.
    Prints progress.  Takes ~10-15 minutes for 380+ items.
    """
    n = len(assessments)
    print(f"\nEnriching {n} assessments with detail page data...")
    print("(This runs once and saves to catalog.json — grab a coffee)\n")

    for i, item in enumerate(assessments, 1):
        print(f"  [{i:>3}/{n}] {item['name'][:55]:<55}", end=" ", flush=True)
        detail = scrape_detail(item["url"])
        item.update(detail)
        desc_preview = (detail["description"][:40] + "…") if detail["description"] else "no description"
        print(f"| {detail['duration'] or 'no duration':>12} | {desc_preview}")

    return assessments


# ── Save ──────────────────────────────────────────────────────────────────────

def save(assessments: list[dict], path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(assessments, f, indent=2, ensure_ascii=False)
    print(f"\nSaved {len(assessments)} assessments → {path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("SHL Individual Test Solutions Scraper")
    print("=" * 60)

    # Step 1: collect all items from the paginated list
    assessments = scrape_all_list_pages()

    if not assessments:
        print("\n✗ No assessments found — SHL may have changed their page structure.")
        print("  Open this URL in a browser and check the HTML:")
        print("  https://www.shl.com/products/product-catalog/?start=0&type=1")
        return

    print(f"\n✓ Found {len(assessments)} Individual Test Solutions in catalog")

    # Step 2: enrich each with description + duration from detail pages
    assessments = enrich_all(assessments)

    # Step 3: save
    save(assessments, OUTPUT_PATH)

    # Step 4: quick summary
    print("\nSample entries:")
    print("-" * 60)
    for item in assessments[:5]:
        print(f"  Name : {item['name']}")
        print(f"  URL  : {item['url']}")
        print(f"  Type : {item['test_type']}")
        print(f"  Desc : {item['description'][:80]}..." if item["description"] else "  Desc : (none)")
        print()

    print("Done!")


if __name__ == "__main__":
    main()