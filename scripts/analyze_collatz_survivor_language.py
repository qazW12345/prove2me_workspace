#!/usr/bin/env python3
"""Analyze the symbolic survivor language of the seven-mod-32 Syracuse residual.

This does NOT publish new Prove2Me nodes.  It studies the hard residue sieve as a
language of accelerated Syracuse valuation words.

Key notation:
  a_i = v2(3 * Syr^{i-1}(n) + 1)
  S_t = a_1 + ... + a_t
  L   = log_2(3)

For the seven-mod-32 branch the surviving words begin (1,1,2).  A coefficient
certificate appears as soon as S_t > t*L.  The symbolic "coefficient-safe"
language therefore consists of positive-integer words satisfying
S_j <= floor(j*L) at every prefix.

The script reproduces the observed first-appearance batch counts, derives the
Sturmian slack recurrence, and optionally brute-verifies the exact residue
sieve through a requested modulus depth.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

L = math.log2(3.0)
PREFIX = (1, 1, 2)

OBSERVED_FIRST_BATCHES = {
    # descent_time: (first_modulus_depth, count)
    11: (19, 194),
    12: (21, 525),
    13: (22, 1570),
    14: (24, 3387),
    15: (25, 9690),
    16: (27, 20423),
    17: (28, 58040),
    18: (30, 121977),
}

S13 = {679,1191,2663,3687,4199,4455,5191,5607,5959,6215,6375,6631,6983,7079,7399,7495,7847,7911,8103}
S15 = {839,1095,2119,2279,2727,2983,3303,4007,6503,6759,7783,9959,10055,11079,11943,12967,14439,16743,16871,17735,17767,19623,20199,21223,23399,24647,24679,25703,25831,26087,26535,27111,27975,28999,29863,30311,30887}
S16 = {359,1351,2407,2791,2887,3239,3815,4775,5863,6247,7015,8263,8551,9319,9543,10151,10727,11431,12007,12615,12775,13671,13927,14503,15207,16455,17127,17223,17479,17511,18343,18919,19111,19367,19687,20807,21735,22119,22695,22887,23143,25415,25671,26343,26439,27303,27559,27879,28327,31079,31335,33255,34151,34535,34631,36519,37607,37735,40039,41063,41447,42215,42343,42471,43111,43335,44359,45223,45799,46247,46407,48295,49255,50407,50663,51271,51431,52071,52551,53159,53319,54375,54439,55207,56935,57671,58983,59463,59559,59623,60231,61351,62119,62279,63335,63591,64167,64871,65127}


def v2(n: int) -> int:
    return (n & -n).bit_length() - 1


def syr_step(n: int) -> tuple[int, int]:
    x = 3 * n + 1
    a = v2(x)
    return x >> a, a


def old_residual(n: int) -> bool:
    return (
        n % 128 in {39, 71, 103}
        and n % 256 not in {39, 199}
        and n % 1024 not in {423, 583, 999}
        and n % 4096 not in {231, 615, 935, 1703, 3143, 3559, 3911}
        and n % 8192 not in S13
        and n % 32768 not in S15
        and n % 65536 not in S16
    )


def barrier(depth: int) -> int:
    return math.floor(depth * L)


def first_certificate_depth(t: int) -> int:
    # First precision K at which S_t = floor(t L)+1 is uniformly visible.
    return barrier(t) + 2


def admissible_dp(max_t: int) -> dict[int, dict[int, int]]:
    """Counts safe words by cumulative valuation S_t.

    states[t][s] = number of words (a_1,...,a_t) beginning PREFIX,
    all a_i >= 1, all prefix sums S_j <= floor(j log_2 3), with S_t=s.
    """
    s0 = sum(PREFIX)
    for j in range(1, len(PREFIX) + 1):
        assert sum(PREFIX[:j]) <= barrier(j)
    out = {len(PREFIX): {s0: 1}}
    states = {s0: 1}
    for t in range(len(PREFIX) + 1, max_t + 1):
        b = barrier(t)
        nxt: dict[int, int] = defaultdict(int)
        for s, count in states.items():
            for ns in range(s + 1, b + 1):
                nxt[ns] += count
        states = dict(nxt)
        out[t] = states
    return out


def weighted_safe_probability(dp: dict[int, dict[int, int]], t: int) -> float:
    """Haar/geometric probability of a safe word through t, conditional on PREFIX."""
    raw = sum(count * (2.0 ** (-s)) for s, count in dp[t].items())
    prefix_weight = 2.0 ** (-sum(PREFIX))
    return raw / prefix_weight


def coefficient_stop(n: int, limit: int = 10000) -> tuple[int, int, int] | None:
    x = n
    s = 0
    for t in range(1, limit + 1):
        x, a = syr_step(x)
        s += a
        if s > t * L:
            return t, s, x
    return None


def stopping_time(n: int, limit: int = 10000) -> tuple[int, int, int] | None:
    x = n
    s = 0
    for t in range(1, limit + 1):
        x, a = syr_step(x)
        s += a
        if x < n:
            return t, s, x
    return None


def representative_certificate(n: int, K: int) -> tuple[int, int] | None:
    x = n
    s = 0
    for t in range(1, 256):
        x, a = syr_step(x)
        s += a
        if s + 1 > K:
            return None
        if (3 ** t) < (2 ** s) and x < n:
            return t, s
    return None


def coefficient_safe_cylinder(n: int, K: int) -> bool:
    """Whether every uniformly determined prefix stays above coefficient contraction."""
    x = n
    s = 0
    for t in range(1, 256):
        x, a = syr_step(x)
        s += a
        if s + 1 > K:
            return True
        if s > barrier(t):
            return False
    raise RuntimeError("unexpectedly long determined prefix")


def brute_verify(max_K: int) -> dict:
    """Reproduce the exact residue frontier, intended for K<=30."""
    frontier = [n for n in range(1 << 16) if old_residual(n)]
    assert len(frontier) == 395
    levels = {}
    for K in range(17, max_K + 1):
        candidates = [y for x in frontier for y in (x, x + (1 << (K - 1)))]
        next_frontier = []
        killed_by_parent: Counter[int] = Counter()
        mismatches = 0
        shapes: Counter[tuple[int, int]] = Counter()
        for n in candidates:
            cert = representative_certificate(n, K)
            survives = cert is None
            if survives:
                next_frontier.append(n)
            else:
                killed_by_parent[n % (1 << (K - 1))] += 1
                shapes[cert] += 1
            if survives != coefficient_safe_cylinder(n, K):
                mismatches += 1

        children_surviving = Counter()
        next_set = set(next_frontier)
        for p in frontier:
            children_surviving[
                int(p in next_set) + int((p + (1 << (K - 1))) in next_set)
            ] += 1

        levels[str(K)] = {
            "parent_count": len(frontier),
            "candidate_count": len(candidates),
            "survivor_count": len(next_frontier),
            "removed_count": len(candidates) - len(next_frontier),
            "children_surviving_per_parent": dict(sorted(children_surviving.items())),
            "certificate_shapes": {
                f"t={t},S={s}": c for (t, s), c in sorted(shapes.items())
            },
            "coefficient_language_mismatches": mismatches,
        }
        frontier = next_frontier
    return {"levels": levels, "final_count": len(frontier)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-word-length", type=int, default=100)
    ap.add_argument("--bruteforce-depth", type=int, default=0,
                    help="optional exact residue verification; 30 is useful but comparatively expensive")
    ap.add_argument("--output", default="agent-state/collatz-survivor-language.json")
    args = ap.parse_args()

    max_t = max(args.max_word_length, 20)
    dp = admissible_dp(max_t)

    symbolic_counts = {t: sum(dp[t].values()) for t in range(3, max_t + 1)}

    observed_checks = {}
    for descent_t, (K, count) in OBSERVED_FIRST_BATCHES.items():
        predicted = symbolic_counts[descent_t - 1]
        predicted_K = first_certificate_depth(descent_t)
        assert predicted == count, (descent_t, predicted, count)
        assert predicted_K == K, (descent_t, predicted_K, K)
        observed_checks[str(descent_t)] = {
            "observed_count": count,
            "predicted_from_safe_prefixes": predicted,
            "observed_first_depth": K,
            "predicted_first_depth": predicted_K,
        }

    # The branch base representatives provide a finite sanity check on CST behavior.
    base = [n for n in range(1 << 16) if old_residual(n)]
    cst_mismatches = []
    base_stats = []
    for n in base:
        cs = coefficient_stop(n)
        st = stopping_time(n)
        assert cs is not None and st is not None
        if cs[0] != st[0]:
            cst_mismatches.append({"n": n, "coefficient": cs, "stopping": st})
        base_stats.append((n, st[0], st[1], st[2]))
    hardest = max(base_stats, key=lambda row: row[2])

    clock = []
    for t in range(3, min(max_t, 60)):
        jump = barrier(t + 1) - barrier(t)
        assert jump in (1, 2)
        clock.append({
            "from_t": t,
            "jump": jump,
            "epsilon": jump - 1,
        })

    projected = {}
    for descent_t in range(11, min(max_t + 1, 31)):
        projected[str(descent_t)] = {
            "new_family_count": symbolic_counts[descent_t - 1],
            "first_modulus_depth": first_certificate_depth(descent_t),
        }

    report = {
        "lambda_log2_3": L,
        "valuation_prefix": list(PREFIX),
        "symbolic_language": {
            "condition": "S_j <= floor(j*log2(3)) at every determined prefix",
            "slack": "D_j = floor(j*log2(3)) - S_j",
            "recurrence": "D_(j+1) = D_j + epsilon_j - b_(j+1), b=a-1>=0, epsilon in {0,1}",
            "clock": "epsilon_j = floor((j+1)log2(3))-floor(j log2(3))-1",
            "no_dead_ends_reason": "a_(j+1)=1 is always admissible because floor((j+1)L)-floor(jL)>=1",
        },
        "observed_batch_checks": observed_checks,
        "safe_word_counts": {str(t): symbolic_counts[t] for t in range(3, min(max_t, 100) + 1)},
        "projected_first_appearance_families": projected,
        "conditional_haar_safe_probability": {
            str(t): weighted_safe_probability(dp, t)
            for t in (10, 20, 30, 50, 75, 100)
            if t <= max_t
        },
        "base_residue_representatives": {
            "count": len(base),
            "coefficient_vs_actual_stopping_time_mismatches": cst_mismatches,
            "largest_required_uniform_precision": {
                "n": hardest[0],
                "accelerated_stopping_time": hardest[1],
                "total_stripped_exponent": hardest[2],
                "first_uniform_modulus_depth": hardest[2] + 1,
                "descent_value": hardest[3],
            },
            "n_71": {
                "stopping": stopping_time(71),
                "note": "71 survives every residue frontier through K=30 but descends after 32 accelerated steps with total exponent 51; its whole residue class needs K>=52 for that certificate."
            },
        },
        "clock_prefix": clock,
    }

    if args.bruteforce_depth:
        if args.bruteforce_depth < 17:
            raise SystemExit("--bruteforce-depth must be >=17")
        report["bruteforce"] = brute_verify(args.bruteforce_depth)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(out),
        "A10": symbolic_counts[10],
        "A17": symbolic_counts[17],
        "next_new_families": {k: projected[k] for k in ("19","20","21") if k in projected},
        "base_cst_mismatches": len(cst_mismatches),
        "hardest_base_representative": hardest,
    }, indent=2))


if __name__ == "__main__":
    main()
