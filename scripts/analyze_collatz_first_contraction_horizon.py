#!/usr/bin/env python3
"""Certify a large first-coefficient-contraction horizon on the seven-mod-32 branch.

This combines two ingredients:

1. The exact first-contraction seed inequality formalized in
   msharpe248/collatz, theorem Collatz.first_contraction_seed_bound:

     if T is the first coefficient contraction, j=oddSteps T n,
     and n has not descended by time T, then

       3 * (2^T - 3^j) * n <= j * 3^j.

   Therefore any such non-descending seed satisfies

       n < M(T) := floor(j*3^j / (3*(2^T-3^j))) + 1,

   where j is the largest integer with 3^j < 2^T.

2. The exact branch scan already committed in
   agent-state/collatz-stabilization-records.json.  It checks every seed
   satisfying the old seven-mod-32 residual predicate below 2^30 and
   found zero cases where coefficient stopping precedes actual descent.

For a horizon H, let M*(H)=max_{1<=T<=H} M(T).  If M*(H)<2^30,
then:
  - n >= M*(H): the analytic first-contraction inequality rules out
    a non-descending first contraction by time H;
  - n < M*(H): n is inside the exact branch scan, which found no mismatch.

This is an exact computational proof candidate, pending a compact Lean port
of the finite branch scan / imported theorem bridge.  It is not claimed as
a kernel-checked theorem in this repository yet.
"""
from __future__ import annotations

import json
from pathlib import Path

SCAN = Path("agent-state/collatz-stabilization-records.json")
OUT = Path("agent-state/collatz-first-contraction-horizon.json")
SCAN_BOUND = 1 << 30


def threshold_records_until_cross(bound: int = SCAN_BOUND, max_T: int = 1_000_000):
    """Return record highs of M(T), stopping at the first record >= bound.

    Powers are updated incrementally, so this is exact and fast even when
    T is tens of thousands.
    """
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
        # Now 3^j < 2^T <= 3^(j+1).
        assert three_j < two_T <= three_j * 3
        denominator = 3 * (two_T - three_j)
        M = (j * three_j) // denominator + 1
        if M > record:
            record = M
            rows.append({
                "T": T,
                "j": j,
                "threshold_M": M,
                "gap_2T_minus_3j": two_T - three_j,
            })
            if record >= bound:
                break
    else:
        raise RuntimeError("no threshold crossing found within max_T")
    return rows


def main():
    scan = json.loads(SCAN.read_text())
    assert scan["depth"] == 30
    assert scan["candidate_count"] == 395 * (1 << (30 - 16))
    assert scan["coefficient_actual_mismatch_count"] == 0
    assert scan["coefficient_actual_mismatch_sample"] == []

    records = threshold_records_until_cross()
    crossing = records[-1]
    previous = records[-2]
    assert previous["threshold_M"] < SCAN_BOUND
    assert crossing["threshold_M"] >= SCAN_BOUND

    safe_horizon = crossing["T"] - 1

    # At H=safe_horizon the maximum threshold is the preceding record.
    assert previous["T"] <= safe_horizon
    assert crossing["T"] == safe_horizon + 1

    report = {
        "status": "exact computational proof candidate; Lean port pending",
        "branch": "old seven-mod-32 residual predicate",
        "scan": {
            "depth": scan["depth"],
            "exclusive_upper_bound": SCAN_BOUND,
            "candidate_count": scan["candidate_count"],
            "coefficient_actual_mismatch_count": scan["coefficient_actual_mismatch_count"],
            "largest_observed_first_coefficient_stop": scan["best_stopping_record"]["coefficient_stopping_time"],
            "largest_observed_record_seed": scan["best_stopping_record"]["n"],
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
            "scan_bound": SCAN_BOUND,
            "next_time": crossing["T"],
            "next_threshold": crossing["threshold_M"],
            "logic": [
                f"If a branch seed n >= {previous['threshold_M']} has its first coefficient contraction at T <= {safe_horizon}, the first-contraction inequality forces actual descent.",
                f"If n < {previous['threshold_M']}, then n < 2^30 and is among the exact branch scan; that scan found zero coefficient/actual stopping mismatches.",
                f"Thus every tested/formally-bounded branch seed whose first coefficient contraction occurs by Terras time {safe_horizon} descends.",
                f"The same splice no longer follows from the current 2^30 scan at T={crossing['T']}, where the analytic exceptional threshold jumps to {crossing['threshold_M']} > 2^30.",
            ],
        },
        "caveat": (
            "The analytic inequality is already Lean-formalized externally. "
            "The <2^30 branch census is exact Python computation in this repository, "
            "not yet a Lean-kernel table. Therefore the combined statement is a "
            "machine-reproducible proof candidate, not yet a fully kernel-checked theorem."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report["combined_certificate"], indent=2))


if __name__ == "__main__":
    main()
