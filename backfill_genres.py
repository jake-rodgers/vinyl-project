import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
RECORDS_FILE  = "records.json"
DISCOGS_TOKEN = "HmwIRxGUHIDGuTACxNCXuFaZWKsiDTEDshSCoUdi"   # paste your token here

HEADERS = {
    "User-Agent": "VinylDatabase/1.0",
    "Authorization": f"Discogs token={DISCOGS_TOKEN}"
}

# ── Discogs genre lookup ───────────────────────────────────────────────────────

def fetch_genre(artist, album):
    """Search Discogs and return genre + style tags for a release."""
    query = urllib.parse.urlencode({
        "artist":        artist,
        "release_title": album,
        "type":          "release",
        "per_page":      3
    })
    url = f"https://api.discogs.com/database/search?{query}"
    req = urllib.request.Request(url, headers=HEADERS)

    try:
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
    except Exception as e:
        print(f"  Error searching Discogs: {e}")
        return []

    results = data.get("results", [])
    if not results:
        return []

    # Combine genre + style into one flat list, deduplicated
    genres = []
    for tag in results[0].get("genre", []):
        if tag not in genres:
            genres.append(tag)
    for tag in results[0].get("style", []):
        if tag not in genres:
            genres.append(tag)

    return genres

# ── Main ──────────────────────────────────────────────────────────────────────

def backfill_genres():
    records = json.loads(Path(RECORDS_FILE).read_text())
    updated = 0
    skipped = 0

    for i, record in enumerate(records):
        artist = record.get("artist", "")
        album  = record.get("album", "")

        # Skip if genre already exists and is not empty
        if record.get("genre"):
            print(f"[{i+1}/{len(records)}] Skipping — already has genre: {artist} — {album}")
            skipped += 1
            continue

        print(f"[{i+1}/{len(records)}] Searching: {artist} — {album}")
        genres = fetch_genre(artist, album)

        if genres:
            record["genre"] = genres
            print(f"  Found: {', '.join(genres)}")
            updated += 1
        else:
            record["genre"] = []
            print(f"  Nothing found — leaving blank")

        # Discogs rate limit: 60 requests/minute, so 1 second between calls is safe
        time.sleep(1)

    Path(RECORDS_FILE).write_text(json.dumps(records, indent=2))
    print(f"\nDone. {updated} records updated, {skipped} already had genre.")
    print("Now run: git add records.json && git commit -m 'Add genres' && git push")

if __name__ == "__main__":
    backfill_genres()