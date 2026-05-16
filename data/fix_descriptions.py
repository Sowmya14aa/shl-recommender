import json, time, re, os, requests
from bs4 import BeautifulSoup

CATALOG_PATH = os.path.join(os.path.dirname(__file__), "catalog.json")
DELAY = 1.0
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"}
BAD_PHRASES = ["If you choose to continue", "Outdated browser", "upgrading to a modern browser"]

def is_boilerplate(text):
    return any(p.lower() in text.lower() for p in BAD_PHRASES)

def scrape_detail(url):
    result = {"description": "", "duration": "", "job_levels": "", "languages": ""}
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        meta = soup.find("meta", attrs={"name": "description"}) or \
               soup.find("meta", attrs={"property": "og:description"})
        if meta:
            content = meta.get("content", "").strip()
            if ": " in content:
                content = content.split(": ", 1)[1]
            if content and not is_boilerplate(content):
                result["description"] = content

        if not result["description"]:
            for h4 in soup.find_all("h4"):
                if "description" in h4.get_text(strip=True).lower():
                    next_p = h4.find_next_sibling("p")
                    if next_p:
                        text = next_p.get_text(strip=True)
                        if not is_boilerplate(text):
                            result["description"] = text
                    break

        page_text = soup.get_text(" ", strip=True)
        m = re.search(r'Approximate Completion Time in minutes\s*=\s*(\d+)', page_text)
        if m:
            result["duration"] = f"{m.group(1)} minutes"
        else:
            m2 = re.search(r'(\d{1,3})\s*minutes?', page_text, re.IGNORECASE)
            if m2:
                result["duration"] = f"{m2.group(1)} minutes"

        for h4 in soup.find_all("h4"):
            if "job level" in h4.get_text(strip=True).lower():
                next_p = h4.find_next_sibling("p")
                if next_p:
                    result["job_levels"] = next_p.get_text(strip=True).rstrip(",").strip()
                break

        for h4 in soup.find_all("h4"):
            if "language" in h4.get_text(strip=True).lower():
                next_p = h4.find_next_sibling("p")
                if next_p:
                    result["languages"] = next_p.get_text(strip=True).rstrip(",").strip()
                break

    except Exception as exc:
        print(f"\n    Warning: {url}: {exc}")
    return result

def main():
    print("SHL Catalog Description Fixer")
    print("=" * 60)
    with open(CATALOG_PATH, encoding="utf-8") as f:
        assessments = json.load(f)

    total = len(assessments)
    print(f"Loaded {total} assessments. Fetching real descriptions...\n")
    fixed = 0

    for i, item in enumerate(assessments, 1):
        print(f"[{i:>3}/{total}] {item['name'][:50]:<50}", end=" ", flush=True)
        detail = scrape_detail(item["url"])
        time.sleep(DELAY)
        item.update(detail)

        if detail["description"]:
            fixed += 1
            print(f"OK | {detail['duration'] or '?':>10} | {detail['description'][:40]}...")
        else:
            print("no description")

        if i % 50 == 0:
            with open(CATALOG_PATH, "w", encoding="utf-8") as f:
                json.dump(assessments, f, indent=2, ensure_ascii=False)
            print(f"\n  -- Saved progress ({i}/{total}) --\n")

    with open(CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(assessments, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Fixed {fixed}/{total} descriptions.")
    print(f"Saved to {CATALOG_PATH}")

if __name__ == "__main__":
    main()