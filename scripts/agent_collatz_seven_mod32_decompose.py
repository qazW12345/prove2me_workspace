#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BASE = "https://prove2.me/api/v1"
PARENT_ID = "b5094e6b-1347-43fe-ac3d-adbf79509f5e"
OUT = Path("agent-state/collatz-seven-mod32-decompose.json")

CHILD19 = "syracuse_descent_eleven_steps_seven_mod32_mod524288"
CHILD20 = "syracuse_descent_eleven_steps_seven_mod32_mod1048576"
RESIDUAL20 = "syracuse_descent_residual_seven_mod32_mod1048576"

S13 = {
    679, 1191, 2663, 3687, 4199, 4455, 5191, 5607, 5959, 6215,
    6375, 6631, 6983, 7079, 7399, 7495, 7847, 7911, 8103,
}
S15 = {
    839, 1095, 2119, 2279, 2727, 2983, 3303, 4007, 6503, 6759,
    7783, 9959, 10055, 11079, 11943, 12967, 14439, 16743, 16871,
    17735, 17767, 19623, 20199, 21223, 23399, 24647, 24679, 25703,
    25831, 26087, 26535, 27111, 27975, 28999, 29863, 30311, 30887,
}
S16 = {
    359, 1351, 2407, 2791, 2887, 3239, 3815, 4775, 5863, 6247,
    7015, 8263, 8551, 9319, 9543, 10151, 10727, 11431, 12007,
    12615, 12775, 13671, 13927, 14503, 15207, 16455, 17127, 17223,
    17479, 17511, 18343, 18919, 19111, 19367, 19687, 20807, 21735,
    22119, 22695, 22887, 23143, 25415, 25671, 26343, 26439, 27303,
    27559, 27879, 28327, 31079, 31335, 33255, 34151, 34535, 34631,
    36519, 37607, 37735, 40039, 41063, 41447, 42215, 42343, 42471,
    43111, 43335, 44359, 45223, 45799, 46247, 46407, 48295, 49255,
    50407, 50663, 51271, 51431, 52071, 52551, 53159, 53319, 54375,
    54439, 55207, 56935, 57671, 58983, 59463, 59559, 59623, 60231,
    61351, 62119, 62279, 63335, 63591, 64167, 64871, 65127,
}

PREAMBLE = """import Definitions.Def_syracuseStep
import Mathlib.Logic.Function.Iterate
import Mathlib.Data.Finset.Insert

set_option autoImplicit false\nset_option maxRecDepth 100000"""


def api(method: str, path: str, *, token: str | None = None, payload=None):
    headers = {
        "Accept": "application/json",
        "User-Agent": "prove2me-collatz-decompose/1",
    }
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {raw[:4000]}") from exc


def verify(token: str, theorem_id: str, content: str, explanation: str):
    boundary = "----p2m" + uuid.uuid4().hex
    parts = []
    for name, value in [
        ("theorem_id", theorem_id),
        ("proof_type", "prove"),
        ("explanation", explanation),
    ]:
        parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="solution.lean"\r\n'
        f'Content-Type: text/plain\r\n\r\n'.encode()
        + content.encode("utf-8")
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(
        BASE + "/verify",
        data=b"".join(parts),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"POST /verify -> HTTP {exc.code}: {raw[:4000]}") from exc


def v2(n: int) -> int:
    out = 0
    while n % 2 == 0:
        out += 1
        n //= 2
    return out


def syracuse_step(n: int) -> tuple[int, int]:
    x = 3 * n + 1
    a = v2(x)
    return x >> a, a


def uniform_certificate(rep: int, K: int):
    x = rep
    total = 0
    exponents = []
    for t in range(1, 128):
        x, a = syracuse_step(x)
        exponents.append(a)
        total += a
        if total + 1 > K:
            return None
        if 3**t < 2**total and x < rep:
            return {"t": t, "sum": total, "image": x, "exponents": exponents}
    return None


def old_residual_predicate(r: int) -> bool:
    return (
        r % 128 in {39, 71, 103}
        and r % 256 not in {39, 199}
        and r % 1024 not in {423, 583, 999}
        and r % 4096 not in {231, 615, 935, 1703, 3143, 3559, 3911}
        and r % 8192 not in S13
        and r % 32768 not in S15
        and r % 65536 not in S16
    )


def compute_refinement():
    r16 = [r for r in range(1 << 16) if old_residual_predicate(r)]
    assert len(r16) == 395

    frontier19 = [r + j * (1 << 16) for r in r16 for j in range(8)]
    c19, u19, cert19 = [], [], {}
    for r in frontier19:
        cert = uniform_certificate(r, 19)
        if cert is None:
            u19.append(r)
        else:
            c19.append(r)
            cert19[r] = cert

    frontier20 = [r2 for r in u19 for r2 in (r, r + (1 << 19))]
    c20, u20, cert20 = [], [], {}
    for r in frontier20:
        cert = uniform_certificate(r, 20)
        if cert is None:
            u20.append(r)
        else:
            c20.append(r)
            cert20[r] = cert

    c19.sort()
    c20.sort()
    u20.sort()

    assert len(frontier19) == 3160
    assert len(c19) == 194
    assert len(u19) == 2966
    assert len(frontier20) == 5932
    assert len(c20) == 194
    assert len(u20) == 5738
    assert all(cert19[r]["t"] == 11 and cert19[r]["sum"] == 18 for r in c19)
    assert all(cert20[r]["t"] == 11 and cert20[r]["sum"] == 19 for r in c20)
    assert 3**11 < 2**18 and 3**11 < 2**19

    c19_lifts20 = {r for a in c19 for r in (a, a + (1 << 19))}
    assert c19_lifts20.isdisjoint(c20)
    assert len(c19_lifts20) + len(c20) + len(u20) == 395 * 16
    return r16, c19, c20, u20


def list_hash(values):
    return hashlib.sha256(",".join(map(str, values)).encode()).hexdigest()


def finset(values, indent: int = 10, width: int = 100) -> str:
    pieces = [str(x) for x in values]
    lines = []
    current = " " * indent
    for p in pieces:
        token = p + ", "
        if len(current) + len(token) > width and current.strip():
            lines.append(current.rstrip())
            current = " " * indent + token
        else:
            current += token
    if current.strip():
        lines.append(current.rstrip(", "))
    return "{\n" + "\n".join(lines) + "\n" + " " * max(0, indent - 2) + "}"


def old_hypotheses() -> str:
    return """    (h : n % 128 = 39 ∨ n % 128 = 71 ∨ n % 128 = 103)
    (h256 : n % 256 ≠ 39 ∧ n % 256 ≠ 199)
    (h1024 : n % 1024 ≠ 423 ∧ n % 1024 ≠ 583 ∧ n % 1024 ≠ 999)
    (h4096 : n % 4096 ≠ 231 ∧ n % 4096 ≠ 615 ∧ n % 4096 ≠ 935 ∧ n % 4096 ≠ 1703 ∧ n % 4096 ≠ 3143 ∧ n % 4096 ≠ 3559 ∧ n % 4096 ≠ 3911)
    (h8192 : n % 8192 ∉ ({679, 1191, 2663, 3687, 4199, 4455, 5191, 5607, 5959, 6215,
      6375, 6631, 6983, 7079, 7399, 7495, 7847, 7911, 8103} : Finset ℕ))
    (h32768 : n % 32768 ∉ ({839, 1095, 2119, 2279, 2727, 2983, 3303, 4007, 6503, 6759,
      7783, 9959, 10055, 11079, 11943, 12967, 14439, 16743, 16871, 17735,
      17767, 19623, 20199, 21223, 23399, 24647, 24679, 25703, 25831, 26087,
      26535, 27111, 27975, 28999, 29863, 30311, 30887} : Finset ℕ))
    (h65536 : n % 65536 ∉ ({359, 1351, 2407, 2791, 2887, 3239, 3815, 4775, 5863, 6247,
      7015, 8263, 8551, 9319, 9543, 10151, 10727, 11431, 12007, 12615,
      12775, 13671, 13927, 14503, 15207, 16455, 17127, 17223, 17479, 17511,
      18343, 18919, 19111, 19367, 19687, 20807, 21735, 22119, 22695, 22887,
      23143, 25415, 25671, 26343, 26439, 27303, 27559, 27879, 28327, 31079,
      31335, 33255, 34151, 34535, 34631, 36519, 37607, 37735, 40039, 41063,
      41447, 42215, 42343, 42471, 43111, 43335, 44359, 45223, 45799, 46247,
      46407, 48295, 49255, 50407, 50663, 51271, 51431, 52071, 52551, 53159,
      53319, 54375, 54439, 55207, 56935, 57671, 58983, 59463, 59559, 59623,
      60231, 61351, 62119, 62279, 63335, 63591, 64167, 64871, 65127} : Finset ℕ))"""


def make_child_formals(c19, c20):
    f19, f20 = finset(c19), finset(c20)
    child19 = f"""theorem {CHILD19} (n : ℕ)
    (h : n % 524288 ∈ ({f19} : Finset ℕ)) :
    syracuseStep^[11] n < n := by sorry"""
    child20 = f"""theorem {CHILD20} (n : ℕ)
    (h : n % 1048576 ∈ ({f20} : Finset ℕ)) :
    syracuseStep^[11] n < n := by sorry"""
    residual = f"""theorem {RESIDUAL20} (n : ℕ)
{old_hypotheses()}
    (h524288 : n % 524288 ∉ ({f19} : Finset ℕ))
    (h1048576 : n % 1048576 ∉ ({f20} : Finset ℕ)) :
    ∃ t : ℕ, syracuseStep^[t] n < n := by sorry"""
    return child19, child20, residual


def make_parent_solution(c19, c20):
    f19, f20 = finset(c19), finset(c20)
    return f"""import Theorems.Thm_{CHILD19}
import Theorems.Thm_{CHILD20}
import Theorems.Thm_{RESIDUAL20}
import Definitions.Def_syracuseStep
import Mathlib.Logic.Function.Iterate
import Mathlib.Data.Finset.Insert

set_option autoImplicit false

theorem solution (n : ℕ)
{old_hypotheses()} :
    ∃ t : ℕ, syracuseStep^[t] n < n := by
  by_cases h19 : n % 524288 ∈ ({f19} : Finset ℕ)
  · exact ⟨11, {CHILD19} n h19⟩
  · by_cases h20 : n % 1048576 ∈ ({f20} : Finset ℕ)
    · exact ⟨11, {CHILD20} n h20⟩
    · exact {RESIDUAL20} n h h256 h1024 h4096 h8192 h32768 h65536 h19 h20
"""


def get_exact_theorem(token: str, name: str):
    query = urllib.parse.urlencode({"q": name, "limit": "100", "offset": "0"})
    result = api("GET", f"/theorems?{query}", token=token)
    for thm in result.get("theorems", []):
        if thm.get("theorem_name") == name:
            return thm
    return None


def publish_children(token: str, env: str, formals):
    child19_formal, child20_formal, residual_formal = formals
    specs = [
        {
            "theorem_name": CHILD19,
            "theorem_title": "Eleven-step Syracuse descent on 194 residual classes modulo $2^{19}$",
            "formal_statement": child19_formal,
            "natural_language_statement": "Let $T$ be the accelerated Syracuse map. For every natural number $n$ whose residue modulo $2^{19}=524288$ lies in the displayed 194-element set, the fixed iterate $T^{11}(n)$ is strictly smaller than $n$. These classes are the first uniformly contracting branches obtained by refining the 395 classes of `syracuse_descent_residual_seven_mod32_mod65536`: every canonical representative has a Terras certificate at 11 accelerated steps with total stripped 2-adic exponent 18, so $3^{11}<2^{18}$ and the 19-bit uniformity budget is sufficient.",
            "preamble": PREAMBLE,
            "source": "Exact residue refinement of Prove2Me theorem syracuse_descent_residual_seven_mod32_mod65536 (https://prove2.me/theorems/b5094e6b-1347-43fe-ac3d-adbf79509f5e), using syracuse_uniform_descent (https://prove2.me/theorems/cd79de19-4613-42b0-afc9-48de75023e4a) and exact accelerated Syracuse iteration. R. Terras, Acta Arith. 30 (1976), 241-252.",
            "tags": ["number-theory", "collatz", "syracuse", "stopping-time", "2-adic"],
        },
        {
            "theorem_name": CHILD20,
            "theorem_title": "Eleven-step Syracuse descent on 194 further residual classes modulo $2^{20}$",
            "formal_statement": child20_formal,
            "natural_language_statement": "Let $T$ be the accelerated Syracuse map. After removing the 194 certifying classes at modulus $2^{19}$, a further 194 classes at modulus $2^{20}=1048576$ admit the fixed descent $T^{11}(n)<n$. For every canonical representative in the displayed set, the 11-step exponent sum is 19; hence $3^{11}<2^{19}$ and the 20-bit Terras uniformity budget transfers the descent to the whole arithmetic progression.",
            "preamble": PREAMBLE,
            "source": "Second exact residue refinement of Prove2Me theorem syracuse_descent_residual_seven_mod32_mod65536 (https://prove2.me/theorems/b5094e6b-1347-43fe-ac3d-adbf79509f5e), using syracuse_uniform_descent (https://prove2.me/theorems/cd79de19-4613-42b0-afc9-48de75023e4a) and exact accelerated Syracuse iteration. R. Terras, Acta Arith. 30 (1976), 241-252.",
            "tags": ["number-theory", "collatz", "syracuse", "stopping-time", "2-adic"],
        },
        {
            "theorem_name": RESIDUAL20,
            "theorem_title": "Residual Syracuse descent after the $2^{19}$ and $2^{20}$ eleven-step refinements",
            "formal_statement": residual_formal,
            "natural_language_statement": "Assume the hypotheses of `syracuse_descent_residual_seven_mod32_mod65536`, and in addition exclude the 194 newly certified residue classes modulo $2^{19}$ and the 194 further certified residue classes modulo $2^{20}$. Then some accelerated Syracuse iterate is smaller than the starting value. At modulus $2^{20}$ this leaves 5738 of the 6320 lifts of the old 395-class residual, about 90.79% of its previous density. This child is the remaining infinite Collatz subproblem after the two finite certificate batches.",
            "preamble": PREAMBLE,
            "source": "Residual refinement of Prove2Me theorem syracuse_descent_residual_seven_mod32_mod65536 (https://prove2.me/theorems/b5094e6b-1347-43fe-ac3d-adbf79509f5e), complementary to the two explicit eleven-step certificate batches.",
            "tags": ["number-theory", "collatz", "syracuse", "stopping-time", "residual"],
        },
    ]

    ids, to_publish = {}, []
    for spec in specs:
        existing = get_exact_theorem(token, spec["theorem_name"])
        if existing:
            actual = existing.get("formal_statement", "").strip()
            if actual and actual != spec["formal_statement"].strip():
                raise RuntimeError(f"existing theorem {spec['theorem_name']} has a different formal statement")
            ids[spec["theorem_name"]] = existing.get("theorem_id") or existing.get("id")
        else:
            to_publish.append(spec)

    jobs = []
    if to_publish:
        published = api("POST", "/submit-problem", token=token, payload={"problems": to_publish, "env": env})
        print("publish-queued", json.dumps({"jobs": published.get("jobs", []), "errors": published.get("errors", [])}))
        if published.get("errors"):
            raise RuntimeError("pre-queue publish errors: " + json.dumps(published["errors"]))
        jobs = list(published.get("jobs", []))
        if len(jobs) != len(to_publish):
            raise RuntimeError("unexpected publish job count: " + json.dumps(published))
        pending = {j["job_id"]: j["name"] for j in jobs}
        for _ in range(180):
            if not pending:
                break
            time.sleep(5)
            for job_id, name in list(pending.items()):
                st = api("GET", f"/publish-jobs/{job_id}", token=token)
                status = st.get("status")
                print("publish-status", json.dumps({"name": name, "status": status, "error": st.get("error_message"), "theorem_id": st.get("theorem_id")}))
                if status == "PUBLISHED":
                    ids[name] = st.get("theorem_id")
                    del pending[job_id]
                elif status in {"FAILED", "ERROR"}:
                    raise RuntimeError("child publish failed: " + json.dumps(st))
        if pending:
            raise RuntimeError("timed out waiting for child publication")

    missing = [name for name in (CHILD19, CHILD20, RESIDUAL20) if not ids.get(name)]
    if missing:
        raise RuntimeError("missing child theorem ids: " + repr(missing))
    return ids, jobs


def main():
    key = os.environ.get("PROVE2ME_API_KEY", "").strip()
    if not key:
        raise RuntimeError("PROVE2ME_API_KEY is not available")
    refreshed = api("POST", "/agent/refresh", payload={"api_key": key})
    token = refreshed.get("access_token")
    if not token:
        raise RuntimeError("agent refresh returned no access_token")

    parent = api("GET", f"/theorems/{PARENT_ID}", token=token)
    if parent.get("theorem_name") != "syracuse_descent_residual_seven_mod32_mod65536":
        raise RuntimeError("parent theorem identity mismatch: " + json.dumps(parent)[:2000])
    env = parent.get("mathlib_rev")
    if not env:
        raise RuntimeError("parent theorem response did not include mathlib_rev")

    r16, c19, c20, u20 = compute_refinement()
    child_ids, publish_jobs = publish_children(token, env, make_child_formals(c19, c20))

    solution = make_parent_solution(c19, c20)
    explanation = (
        "Refine the old residual by excluded middle on two explicit finite certificate sets. "
        "If $n \\bmod 2^{19}$ lies in the first 194-element set, the first imported child gives "
        "$T^{11}(n)<n$. Otherwise, test the second 194-element set modulo $2^{20}$; membership "
        "there is handled by the second imported child, again at the fixed 11th iterate. "
        "If neither membership holds, the hypotheses are exactly those of the imported residual "
        "child at modulus $2^{20}$. Thus the parent follows from two finite certificate problems "
        "and one strictly smaller residual problem. The first batch removes 194 of 3160 depth-19 "
        "lifts; the second removes 194 further depth-20 classes, leaving 5738 of 6320 depth-20 "
        "lifts, a 9.21% reduction of the old residual density."
    )
    submission = verify(token, PARENT_ID, solution, explanation)
    print("verify-submitted", json.dumps(submission))
    submission_id = submission.get("submission_id")
    if not submission_id:
        raise RuntimeError("verify returned no submission_id")

    verdict = None
    for _ in range(180):
        time.sleep(5)
        verdict = api("GET", f"/verify?submission_id={submission_id}", token=token)
        status = verdict.get("status")
        print("verify-status", json.dumps({"status": status, "error": verdict.get("error_message")}))
        if status in {"ACCEPTED", "SKETCH_ACCEPTED", "CE", "WA", "SORRY", "FAILED", "ERROR"}:
            break

    report = {
        "platform_version": refreshed.get("version"),
        "parent": {"theorem_id": PARENT_ID, "theorem_name": parent.get("theorem_name"), "mathlib_rev": env, "status_before": parent.get("status")},
        "refinement": {
            "old_residual_classes_mod_2_16": len(r16),
            "depth_19_total_lifts": 395 * 8,
            "depth_19_new_certified": len(c19),
            "depth_19_remaining": 2966,
            "depth_20_total_lifts_of_old_residual": 395 * 16,
            "depth_20_new_certified_after_depth_19": len(c20),
            "depth_20_remaining": len(u20),
            "old_residual_density_removed_fraction": 1 - len(u20) / (395 * 16),
            "c19_sha256": list_hash(c19),
            "c20_sha256": list_hash(c20),
            "c19_first_20": c19[:20],
            "c20_first_20": c20[:20],
            "certificate_shape_19": {"steps": 11, "sum_v2": 18, "count": len(c19)},
            "certificate_shape_20": {"steps": 11, "sum_v2": 19, "count": len(c20)},
        },
        "children": child_ids,
        "publish_jobs": publish_jobs,
        "parent_submission": submission,
        "parent_verdict": verdict,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("wrote", OUT)

    if not verdict or verdict.get("status") not in {"SKETCH_ACCEPTED", "ACCEPTED"}:
        raise RuntimeError("parent reduction was not accepted: " + json.dumps(verdict))


if __name__ == "__main__":
    main()
