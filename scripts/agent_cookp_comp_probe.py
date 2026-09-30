#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from pathlib import Path

BASE = "https://prove2.me/api/v1"
OUT = Path("agent-state/cookp-compose-probe.json")
DEF_ID = "7c6b3da6-5145-4b2d-9550-f07c61d2c766"
THM_ID = "028ccdb8-1f42-4651-94d3-63758b6500fd"

def api(path, token):
    req = urllib.request.Request(BASE + path, headers={
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "prove2me-cookp-probe/2",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode()
        return json.loads(raw) if raw else {}

def main():
    key = os.environ["PROVE2ME_API_KEY"].strip()
    req = urllib.request.Request(
        BASE + "/agent/refresh",
        data=json.dumps({"api_key": key}).encode(),
        headers={"Content-Type":"application/json","Accept":"application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        token = json.loads(r.read().decode())["access_token"]

    out = {
        "definition": api(f"/theorems/{DEF_ID}", token),
        "target": api(f"/theorems/{THM_ID}", token),
        "decompositions": api(f"/theorems/{THM_ID}/decompositions", token),
        "submissions": api(f"/theorems/{THM_ID}/submissions?limit=20&offset=0",
      "/theorems?status=Proved&q=PolyTimeComputable&limit=100&offset=0",
      "/theorems?status=Open&q=CookPvsNP&limit=100&offset=0",
      "/theorems?status=Proved&q=CookPvsNP&limit=100&offset=0", token),
        "searches": {},
    }
    for q in ["CookPvsNP", "PolyTimeComputable", "TM simulation", "machine composition", "HaltsWithin"]:
        path = "/theorems?" + urllib.parse.urlencode({"q": q, "limit": "100", "offset": "0"})
        out["searches"][q] = api(path, token)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    compact = {
        q: [
            {
                "id": t.get("theorem_id"),
                "name": t.get("theorem_name"),
                "status": t.get("status"),
                "title": t.get("theorem_title"),
            }
            for t in (res.get("theorems") or [])
        ]
        for q, res in out["searches"].items()
    }
    print(json.dumps(compact, indent=2))

if __name__ == "__main__":
    main()
