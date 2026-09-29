#!/usr/bin/env python3
"""Discover actionable Prove2Me missions without mutating platform state."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://prove2.me/api/v1"
OUT = Path("agent-state/discovery.json")
MAX_OPEN_MISSIONS = 140
MAX_LEAVES_PER_MISSION = 4


def api(method: str, path: str, *, token: str | None = None, payload=None):
    headers = {"Accept": "application/json", "User-Agent": "prove2me-agent-discovery/1"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {body[:500]}") from exc


def q(v) -> str:
    return urllib.parse.quote(str(v), safe="")


def score_text(text: str) -> int:
    s = text.lower()
    score = 0
    if "arxiv" in s:
        score += 5
    if "doi" in s or "http://" in s or "https://" in s:
        score += 2
    for bad in (
        "awaiting release",
        "being prepared for release",
        "not yet public",
        "not public",
        "unavailable",
        "forthcoming",
        "to be released",
    ):
        if bad in s:
            score -= 10
    return score


def main():
    key = os.environ.get("PROVE2ME_API_KEY", "").strip()
    if not key:
        raise RuntimeError("missing PROVE2ME_API_KEY")
    refresh = api("POST", "/agent/refresh", payload={"api_key": key})
    token = refresh["access_token"]

    saved = api("GET", "/saved?status=Open&limit=50&offset=0", token=token)

    missions = []
    offset = 0
    while True:
        page = api("GET", f"/missions?limit=100&offset={offset}", token=token)
        batch = page.get("missions", [])
        missions.extend(batch)
        total = int(page.get("total", len(missions)))
        if not batch or len(missions) >= total:
            break
        offset += len(batch)

    open_missions = [
        m for m in missions
        if ((m.get("main_theorem") or {}).get("status") == "Open")
    ]

    candidates = []
    for mission in open_missions[:MAX_OPEN_MISSIONS]:
        root = mission.get("main_theorem") or {}
        root_id = root.get("theorem_id")
        if not root_id:
            continue
        try:
            frontier = api(
                "GET",
                f"/theorems/{q(root_id)}/open-leaves?limit={MAX_LEAVES_PER_MISSION}&offset=0",
                token=token,
            )
        except RuntimeError:
            continue
        leaves = frontier.get("open_leaves", [])
        if not leaves:
            continue

        for leaf in leaves:
            tid = leaf.get("theorem_id")
            if not tid:
                continue
            try:
                detail = api("GET", f"/theorems/{q(tid)}", token=token)
            except RuntimeError:
                continue

            statement = detail.get("formal_statement") or ""
            natural = detail.get("natural_language_statement") or ""
            source = detail.get("source") or ""
            context = " ".join([
                mission.get("name") or "",
                mission.get("description") or "",
                natural,
                source,
            ])
            score = score_text(context)
            closability = int(leaf.get("closability") or 0)
            score += min(closability, 8)
            if 80 <= len(statement) <= 3500:
                score += 2
            if detail.get("audits"):
                score += 1
            if source:
                score += 2
            if int(frontier.get("total") or len(leaves)) <= 12:
                score += 1
            if "sorry" not in statement:
                score -= 3

            candidates.append({
                "score": score,
                "mission_id": mission.get("id"),
                "mission_name": mission.get("name"),
                "mission_type": mission.get("mission_type"),
                "mission_description": mission.get("description"),
                "mission_created_at": mission.get("created_at"),
                "root_theorem_id": root_id,
                "root_theorem_name": root.get("theorem_name"),
                "frontier_total": frontier.get("total"),
                "closability": closability,
                "theorem_id": tid,
                "theorem_name": detail.get("theorem_name"),
                "theorem_title": detail.get("theorem_title"),
                "formal_statement": statement,
                "natural_language_statement": natural,
                "preamble": detail.get("preamble"),
                "source": source,
                "mathlib_rev": detail.get("mathlib_rev"),
                "tags": detail.get("tags"),
                "audits": detail.get("audits"),
            })

    candidates.sort(
        key=lambda x: (
            x["score"],
            x["closability"],
            x.get("mission_created_at") or "",
        ),
        reverse=True,
    )

    result = {
        "platform_version": refresh.get("version"),
        "saved_open": saved,
        "open_mission_count": len(open_missions),
        "missions_examined": min(len(open_missions), MAX_OPEN_MISSIONS),
        "candidates": candidates[:30],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "saved_open_total": saved.get("total", len(saved.get("saved", []))),
        "open_mission_count": len(open_missions),
        "missions_examined": result["missions_examined"],
        "top_candidates": [
            {
                "score": c["score"],
                "mission": c["mission_name"],
                "theorem": c["theorem_name"],
                "closability": c["closability"],
            }
            for c in candidates[:8]
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
