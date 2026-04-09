import json
import random
from datetime import datetime
from pathlib import Path

# ── Config ────────────────────────────────────────────────────────────────────
PICKS_PER_CYCLE = 3       # How many records to feature each month
RECORDS_FILE   = "records.json"
STATE_FILE     = "state.json"
OUTPUT_FILE    = "picks.json"   # Read by the website

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_json(path):
    p = Path(path)
    return json.loads(p.read_text()) if p.exists() else None

def save_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2))

# ── Core logic ────────────────────────────────────────────────────────────────

def pick_records():
    records = load_json(RECORDS_FILE)
    if not records:
        print("No records found — add some with add_record.py first.")
        return []

    state = load_json(STATE_FILE) or {"remaining": [], "picked_history": []}

    all_ids = [r["id"] for r in records]

    # Refill and reshuffle the pool once every record has been picked
    if not state["remaining"]:
        print("Full cycle complete — reshuffling all records.")
        state["remaining"] = all_ids.copy()
        random.shuffle(state["remaining"])

    # Take N records off the top of the shuffled pool
    n = min(PICKS_PER_CYCLE, len(state["remaining"]))
    chosen_ids = state["remaining"][:n]
    state["remaining"] = state["remaining"][n:]
    state["picked_history"].extend(chosen_ids)

    save_json(STATE_FILE, state)

    id_map = {r["id"]: r for r in records}
    return [id_map[i] for i in chosen_ids]

# ── Output ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    picks = pick_records()

    if picks:
        # Write picks.json — this is what the website reads
        output = {
            "updated": datetime.now().strftime("%B %d, %Y"),
            "picks": picks
        }
        save_json(OUTPUT_FILE, output)

        print(f"picks.json written with {len(picks)} records:")
        for r in picks:
            print(f"  {r['artist']} — {r['album']} ({r['year']})")