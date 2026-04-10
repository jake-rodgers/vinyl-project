# add_record.py
import json
import time
import urllib.request
import urllib.parse
from pathlib import Path

RECORDS_FILE = "records.json"

def fetch_mbid(artist, album):
    query = urllib.parse.urlencode({
        "query": f'release:"{album}" AND artist:"{artist}"',
        "fmt": "json",
        "limit": 5  # Grab a few results so we can pick the best one
    })
    url = f"https://musicbrainz.org/ws/2/release?{query}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "VinylDatabase/1.0 (your@email.com)"
    })
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())
    return data.get("releases", [])

def fetch_cover_url(mbid):
    url = f"https://coverartarchive.org/release/{mbid}/front"
    req = urllib.request.Request(url, headers={
        "User-Agent": "VinylDatabase/1.0 (your@email.com)"
    })
    try:
        with urllib.request.urlopen(req) as r:
            return r.url
    except urllib.error.HTTPError:
        return None

def fetch_tracklist(mbid):
    url = f"https://musicbrainz.org/ws/2/release/{mbid}?inc=recordings&fmt=json"
    req = urllib.request.Request(url, headers={
        "User-Agent": "VinylDatabase/1.0 (your@email.com)"
    })
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())

    tracks = []
    for medium in data.get("media", []):
        for track in medium.get("tracks", []):
            tracks.append(track["title"])
    return tracks

def add_record():
    artist = input("Artist name: ").strip()
    album = input("Album name: ").strip()

    print("Searching MusicBrainz...")
    releases = fetch_mbid(artist, album)

    if not releases:
        print("No results found. Try adjusting the artist/album name.")
        return

    # If multiple results, let the user pick the right one
    # (e.g. there may be multiple pressings/editions of the same album)

    if len(releases) > 1:
        print("\nMultiple releases found — pick the one you own:")
        for i, r in enumerate(releases):
            year    = r.get("date", "????")[:4]
            country = r.get("country", "??")
            format  = r.get("media", [{}])[0].get("format", "unknown format") if r.get("media") else "unknown format"
            tracks  = r.get("media", [{}])[0].get("track-count", "?") if r.get("media") else "?"
            print(f"  [{i}] {r['title']} ({year}, {country}) — {format}, {tracks} tracks")
        choice = int(input("Enter number: "))
    else:
        choice = 0

    release = releases[choice]
    mbid = release["id"]
    year = release.get("date", "")[:4]

    # MusicBrainz rate-limits to 1 request/second
    time.sleep(1)

    print("Fetching tracklist...")
    tracks = fetch_tracklist(mbid)
    time.sleep(1)

    print("Fetching cover art...")
    cover_url = fetch_cover_url(mbid)
    if not cover_url:
        cover_url = input("No cover found automatically. Paste an image URL (or leave blank): ").strip()

    # Load existing records and generate a new ID
    records = json.loads(Path(RECORDS_FILE).read_text()) if Path(RECORDS_FILE).exists() else []
    new_id = max((r["id"] for r in records), default=0) + 1

    new_record = {
        "id": new_id,
        "artist": artist,
        "album": album,
        "year": year,
        "mbid": mbid,
        "cover": cover_url,
        "tracks": tracks
    }

    records.append(new_record)
    Path(RECORDS_FILE).write_text(json.dumps(records, indent=2))

    print(f"\nAdded: {artist} — {album} ({year})")
    print(f"Tracks found: {len(tracks)}")
    print(f"Cover: {cover_url}")
    print(f"\nNow run: git add records.json && git commit -m 'Add {album}' && git push")

if __name__ == "__main__":
    add_record()