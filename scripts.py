"""Bulk-load data/incidents.json into Hindsight. Run once: python scripts/load_data.py"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import memory  # noqa: E402

path = pathlib.Path(__file__).resolve().parent.parent / "data" / "incidents.json"
incidents = json.loads(path.read_text())
for i, inc in enumerate(incidents, 1):
    memory.retain_incident(inc)
    print(f"[{i}/{len(incidents)}] retained {inc['id']}")
print("Done.")
