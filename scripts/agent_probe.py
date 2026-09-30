#!/usr/bin/env python3
"""Read-only Prove2Me state collector for the ChatGPT/GitHub bridge.\n\nCleanup status refresh 7.

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

BATCH_TARGET_IDS = [
    "025d0490-fea5-40ba-8336-27d897bf3b62",
    "306ad1d3-54a4-4381-95a6-98a82e56e0fd",
]


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
        raise RuntimeError("PROVE2ME_API_KEY is not available")
    refreshed = api("POST", "/agent/refresh", payload={"api_key": key})
    token = refreshed.get("access_token")
    if not token:
        raise RuntimeError("refresh returned no access_token")
    targets = []
    for theorem_id in BATCH_TARGET_IDS:
        theorem = api("GET", f"/theorems/{q(theorem_id)}", token=token)
        decompositions = api("GET", f"/theorems/{q(theorem_id)}/decompositions", token=token)
        leaves = api("GET", f"/theorems/{q(theorem_id)}/open-leaves?limit=100&offset=0", token=token)
        subs = api("GET", f"/theorems/{q(theorem_id)}/submissions?limit=20&offset=0", token=token)
        targets.append({"theorem": theorem, "decompositions": decompositions, "open_leaves": leaves, "submissions": subs})
    report = {
        "probe_kind": "read-only-cleanup-batch",
        "skill_version": SKILL_VERSION,
        "platform_version": refreshed.get("version"),
        "targets": targets,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "platform_version": report["platform_version"],
        "targets": [
            {"id": x["theorem"].get("id"), "name": x["theorem"].get("theorem_name"), "status": x["theorem"].get("status")}
            for x in targets
        ],
    }, indent=2))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PROBE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
