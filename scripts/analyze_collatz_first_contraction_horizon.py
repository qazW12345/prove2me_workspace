#!/usr/bin/env python3
"""Certify a large first-coefficient-contraction horizon on the seven-mod-32 branch.

This combines:
  * the Lean-formal first-contraction seed inequality from msharpe248/collatz;
  * a contiguous exact integer census of the old seven-mod-32 residual branch.

For a first coefficient contraction at Terras time T with j odd steps, if
there has not yet been descent then

    3 * (2^T - 3^j) * n <= j * 3^j.

Thus every non-descending first contraction lies below an explicit threshold.
Whenever that threshold is inside the already-scanned seed interval, the two
ingredients splice into a finite-horizon exclusion.

The resulting statement is a machine-reproducible proof candidate until the
finite branch census is ported to a compact Lean certificate.
"""
from __future__ import annotations

import json
from pathlib import Path

BASE_SCAN = Path("agent-state/collatz-stabilization-records.json")
EXTENSIONS = [
    Path("agent-state/collatz-branch-interval-2p30-to-1447674322.json"),
]
OUT = Path("agent-state/collatz-first-contraction-horizon.json")
BASE_SCAN_BOUND = 1 << 30


def threshold_records_until_cross(bound: int, max_T: int = 1_000_000):
    """Record highs of the seed threshold; stop at first record > bound."""
    two_T = 1
    j = 0
    three_j = 1
    record = 0
    rows = []
    for T in range(1, max_T + 1):
        two_T <<= 1
        while three_j * 3 < two_T:
            three_j *= 3
            j += 1
        assert three_j < two_T <= three_j * 3
        M = (j * three_j) // (3 * (two_T - three_j)) + 1
        if M > record:
            record = M
            rows.append({"T": T, "j": j, "threshold_M": M})
            if record > bound:
                break
    else:
        raise RuntimeError("no threshold record exceeded the scan bound")
    return rows


def main():
    scan = json.loads(BASE_SCAN.read_text())
    assert scan["depth"] == 30
    assert scan["candidate_count"] == 395 * (1 << (30 - 16))
    assert scan["coefficient_actual_mismatch_count"] == 0
    assert scan["coefficient_actual_mismatch_sample"] == []

    coverage_high = BASE_SCAN_BOUND
    extensions = []
    for path in EXTENSIONS:
        if not path.exists():
            continue
        ext = json.loads(path.read_text())
        assert ext["low_inclusive"] == coverage_high
        assert ext["status"] == "complete"
        assert ext["unresolved_count_capped"] == 0
        assert ext["unresolved_sample"] == []
        coverage_high = ext["high_exclusive"]
        extensions.append({
            "path": str(path),
            "low_inclusive": ext["low_inclusive"],
            "high_exclusive": ext["high_exclusive"],
            "tested": ext["tested"],
            "max_observed_first_descent": ext["max_observed_first_descent"],
        })

    records = threshold_records_until_cross(coverage_high)
    crossing = records[-1]
    previous = records[-2]
    assert previous["threshold_M"] <= coverage_high
    assert crossing["threshold_M"] > coverage_high

    safe_horizon = crossing["T"] - 1
    assert crossing["T"] == safe_horizon + 1

    report = {
        "status": "exact computational proof candidate; Lean port pending",
        "branch": "old seven-mod-32 residual predicate",
        "scan": {
            "base_depth": scan["depth"],
            "base_exclusive_upper_bound": BASE_SCAN_BOUND,
            "base_candidate_count": scan["candidate_count"],
            "coefficient_actual_mismatch_count": scan["coefficient_actual_mismatch_count"],
            "largest_observed_first_coefficient_stop": scan["best_stopping_record"]["coefficient_stopping_time"],
            "largest_observed_record_seed": scan["best_stopping_record"]["n"],
            "contiguous_coverage_high_exclusive": coverage_high,
            "extensions": extensions,
        },
        "analytic_ingredient": {
            "external_repository": "msharpe248/collatz",
            "theorem": "Collatz.first_contraction_seed_bound",
            "source_path": "lean/Collatz/FirstContraction.lean",
            "inequality": "3*(2^T-3^j)*n <= j*3^j for a non-descending first contraction",
        },
        "record_thresholds": records,
        "combined_certificate": {
            "full_first_contraction_horizon": safe_horizon,
            "max_small_seed_threshold_below_horizon": previous["threshold_M"],
            "threshold_record_time": previous["T"],
            "threshold_record_odd_steps": previous["j"],
            "scan_bound": coverage_high,
            "next_time": crossing["T"],
            "next_threshold": crossing["threshold_M"],
            "logic": [
                f"If a branch seed n >= {previous['threshold_M']} has its first coefficient contraction at T <= {safe_horizon}, the first-contraction inequality forces actual descent.",
                f"If n < {previous['threshold_M']}, then n < {coverage_high} and lies inside the contiguous exact branch census; those scans found no unresolved seed.",
                f"Thus every branch seed covered by the analytic/census split whose first coefficient contraction occurs by Terras time {safe_horizon} descends.",
                f"The same splice first fails at T={crossing['T']}, where the exceptional threshold jumps to {crossing['threshold_M']} > {coverage_high}.",
            ],
        },
        "caveat": (
            "The analytic inequality is Lean-formalized externally. "
            "The branch census is exact Python integer computation and CI-reproducible, "
            "but not yet a Lean-kernel table in this workspace."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["combined_certificate"], indent=2))


if __name__ == "__main__":
    main()
