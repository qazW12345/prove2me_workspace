#!/usr/bin/env python3
"""Read-only Prove2Me state collector for the ChatGPT/GitHub bridge.

Authenticates with the Actions secret, discovers the live target mission, and
writes only sanitized platform data. It never calls /verify or any mutating
Prove2Me endpoint.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://prove2.me/api/v1"
SKILL_VERSION = "0.11.5"
TARGET_HINTS = ("erdős problem 592", "partition ordinals", "schipperus")
OUT = Path("agent-state/probe-result.json")
MAX_SOLUTION_SOURCES = 30


def api(method: str, path: str, *, token: str | None = None, payload=None):
    headers = {
        "Accept": "application/json",
        "User-Agent": "prove2me-workspace-agent-probe/2",
    }
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {raw[:1000]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {path} -> network error: {exc.reason}") from exc


def q(value) -> str:
    return urllib.parse.quote(str(value), safe="")


def submissions_with_sources(theorem_id: str, token: str):
    submissions = []
    offset = 0
    while True:
        page = api(
            "GET",
            f"/theorems/{q(theorem_id)}/submissions?limit=200&offset={offset}",
            token=token,
        )
        batch = page.get("submissions", [])
        submissions.extend(batch)
        total = int(page.get("total", len(submissions)))
        if not batch or len(submissions) >= total:
            break
        offset += len(batch)

    enriched = []
    for index, submission in enumerate(submissions):
        item = dict(submission)
        if index < MAX_SOLUTION_SOURCES:
            sid = submission.get("id")
            if sid:
                try:
                    source = api("GET", f"/submissions/{q(sid)}/solution", token=token)
                    item["solution_content"] = source.get("content")
                except RuntimeError as exc:
                    item["solution_fetch_warning"] = str(exc)
        enriched.append(item)
    return {"total": len(submissions), "submissions": enriched}


def theorem_bundle(theorem_id: str, token: str):
    bundle = {
        "theorem": api("GET", f"/theorems/{q(theorem_id)}", token=token),
        "decompositions": api(
            "GET", f"/theorems/{q(theorem_id)}/decompositions", token=token
        ),
        "submissions": submissions_with_sources(theorem_id, token),
    }
    for key, path in (
        ("mentions", f"/theorems/{q(theorem_id)}/mentions"),
        ("missions", f"/theorems/{q(theorem_id)}/missions"),
    ):
        try:
            bundle[key] = api("GET", path, token=token)
        except RuntimeError as exc:
            bundle[key] = {"probe_warning": str(exc)}
    return bundle


def main() -> int:
    key = os.environ.get("PROVE2ME_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "PROVE2ME_API_KEY is not available to this workflow. "
            "Add it under repository Settings -> Secrets and variables -> Actions."
        )

    refreshed = api("POST", "/agent/refresh", payload={"api_key": key})
    token = refreshed.get("access_token")
    if not token:
        raise RuntimeError("Prove2Me refresh succeeded but returned no access_token")

    platform_version = refreshed.get("version")
    me = api("GET", "/me", token=token)

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

    def target_score(mission):
        text = " ".join(str(mission.get(k, "")) for k in ("name", "description")).lower()
        theorem = mission.get("main_theorem") or {}
        text += " " + " ".join(
            str(theorem.get(k, ""))
            for k in ("theorem_name", "theorem_title", "natural_language_statement")
        ).lower()
        return sum(1 for hint in TARGET_HINTS if hint in text)

    ranked = sorted(missions, key=target_score, reverse=True)
    target = ranked[0] if ranked and target_score(ranked[0]) > 0 else None

    report = {
        "probe_kind": "read-only",
        "skill_version": SKILL_VERSION,
        "platform_version": platform_version,
        "version_match": platform_version == SKILL_VERSION,
        "licensing_status": (me.get("licensing") or {}).get("status"),
        "mission_count": len(missions),
        "target_found": target is not None,
        "target": target,
        "milestones": None,
        "mission_comments": None,
        "open_leaves": None,
        "root": None,
        "frontier_details": [],
        "milestone_details": [],
    }

    if target:
        mission_id = target.get("id")
        main = target.get("main_theorem") or {}
        root_id = main.get("theorem_id") or main.get("id")

        if mission_id:
            report["milestones"] = api(
                "GET",
                f"/missions/{q(mission_id)}/milestones?limit=100&offset=0",
                token=token,
            )
            for milestone in report["milestones"].get("milestones", []):
                theorem = milestone.get("theorem") or {}
                theorem_id = (
                    milestone.get("theorem_id")
                    or theorem.get("theorem_id")
                    or theorem.get("id")
                )
                item = {"milestone": milestone}
                if theorem_id:
                    item["theorem"] = api(
                        "GET", f"/theorems/{q(theorem_id)}", token=token
                    )
                    item["decompositions"] = api(
                        "GET",
                        f"/theorems/{q(theorem_id)}/decompositions",
                        token=token,
                    )
                    item["graph"] = api(
                        "GET", f"/theorems/{q(theorem_id)}/graph", token=token
                    )
                    item["open_leaves"] = api(
                        "GET",
                        f"/theorems/{q(theorem_id)}/open-leaves?limit=200&offset=0",
                        token=token,
                    )
                report["milestone_details"].append(item)
            try:
                report["mission_comments"] = api(
                    "GET", f"/missions/{q(mission_id)}/comments", token=token
                )
            except RuntimeError as exc:
                report["mission_comments"] = {"probe_warning": str(exc)}

        if root_id:
            report["root"] = theorem_bundle(root_id, token)
            leaves = api(
                "GET",
                f"/theorems/{q(root_id)}/open-leaves?limit=100&offset=0",
                token=token,
            )
            report["open_leaves"] = leaves
            for leaf in leaves.get("open_leaves", []):
                theorem_id = leaf.get("theorem_id")
                if theorem_id:
                    report["frontier_details"].append(
                        {
                            "frontier": leaf,
                            "detail": theorem_bundle(theorem_id, token),
                        }
                    )

    if target is None:
        report["available_missions"] = [
            {
                "id": m.get("id"),
                "name": m.get("name"),
                "status": (m.get("main_theorem") or {}).get("status"),
            }
            for m in missions
        ]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = {
        "platform_version": platform_version,
        "version_match": report["version_match"],
        "target": target.get("name") if target else None,
        "root_theorem": ((target or {}).get("main_theorem") or {}).get("theorem_name"),
        "open_frontier": [
            {
                "theorem_name": leaf.get("theorem_name"),
                "theorem_id": leaf.get("theorem_id"),
                "closability": leaf.get("closability"),
            }
            for leaf in (report.get("open_leaves") or {}).get("open_leaves", [])
        ],
        "state_file": str(OUT),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PROBE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
