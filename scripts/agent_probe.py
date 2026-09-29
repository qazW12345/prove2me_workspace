#!/usr/bin/env python3
"""Read-only Prove2Me probe for the ChatGPT/GitHub bridge.

This script authenticates with the agent API key supplied by GitHub Actions,
reads public/account mission state, and writes a sanitized JSON report.
It never calls /verify or any mutating Prove2Me endpoint.
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
TARGET_HINTS = ("alphaevolve", "2.371177")
OUT = Path("probe-result.json")


def api(method: str, path: str, *, token: str | None = None, payload=None):
    headers = {
        "Accept": "application/json",
        "User-Agent": "prove2me-workspace-agent-probe/1",
    }
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        BASE + path,
        data=body,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        # The response body is safe to report; request headers/body (which carry
        # credentials) are intentionally never printed.
        raise RuntimeError(
            f"{method} {path} -> HTTP {exc.code}: {raw[:1000]}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {path} -> network error: {exc.reason}") from exc


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
        text = " ".join(
            str(mission.get(k, ""))
            for k in ("name", "description")
        ).lower()
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
        "account": {
            "username": me.get("username"),
            "licensing_status": (me.get("licensing") or {}).get("status"),
        },
        "mission_count": len(missions),
        "target_found": target is not None,
        "target": target,
        "milestones": None,
        "open_leaves": None,
        "mission_comments": None,
    }

    if target:
        mission_id = target.get("id")
        theorem = target.get("main_theorem") or {}
        theorem_id = theorem.get("theorem_id") or theorem.get("id")
        if mission_id:
            report["milestones"] = api(
                "GET",
                f"/missions/{urllib.parse.quote(str(mission_id), safe='')}/milestones?limit=100&offset=0",
                token=token,
            )
            try:
                report["mission_comments"] = api(
                    "GET",
                    f"/missions/{urllib.parse.quote(str(mission_id), safe='')}/comments",
                    token=token,
                )
            except RuntimeError as exc:
                report["mission_comments"] = {"probe_warning": str(exc)}
        if theorem_id:
            report["open_leaves"] = api(
                "GET",
                f"/theorems/{urllib.parse.quote(str(theorem_id), safe='')}/open-leaves?limit=100&offset=0",
                token=token,
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

    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        # Never dump environment variables or request objects here.
        print(f"PROBE FAILED: {exc}", file=sys.stderr)
        raise SystemExit(1)
