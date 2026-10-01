#!/usr/bin/env python3
"""2-adic analysis of the coefficient-safe Syracuse survivor language."""
from __future__ import annotations

import json
import math
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

L = math.log2(3.0)
PREFIX = (1, 1, 2)


def barrier(t: int) -> int:
    return math.floor(t * L)


def canonical_residues(word: list[int]):
    """Return (t,a_t,S_t,C_t,r_t,lift_digit) for the unique cylinder.

    T^t(x) = (3^t x + C_t) / 2^S_t,
    r_t = -C_t * 3^{-t} mod 2^S_t.
    """
    C = 0
    S = 0
    prev_r = 0
    prev_S = 0
    rows = []
    for t, a in enumerate(word, 1):
        C = 3 * C + (1 << S)
        S += a
        modulus = 1 << S
        inv = pow(pow(3, t, modulus), -1, modulus)
        r = (-C * inv) % modulus
        q = None if t == 1 else (r - prev_r) >> prev_S
        rows.append({
            "t": t, "a": a, "S": S, "C": C,
            "canonical_residue": r,
            "modulus_bits": S,
            "lift_digit": q,
        })
        prev_r, prev_S = r, S
    return rows


def zero_slack_word(length: int) -> list[int]:
    """Unique path with D_t=0 for every t>=3."""
    if length < 3:
        return list(PREFIX[:length])
    w = list(PREFIX)
    for t in range(4, length + 1):
        w.append(barrier(t) - barrier(t - 1))
    return w


def bounded_slack_state(B: int, tmax: int):
    d0 = barrier(3) - sum(PREFIX)
    states = {d0: 1}
    for t in range(3, tmax):
        eps = barrier(t + 1) - barrier(t) - 1
        nxt = defaultdict(int)
        for d, count in states.items():
            for d2 in range(0, min(B, d + eps) + 1):
                nxt[d2] += count
        states = dict(nxt)
    return states


def full_safe_state(tmax: int):
    d0 = barrier(3) - sum(PREFIX)
    states = {d0: 1}
    for t in range(3, tmax):
        eps = barrier(t + 1) - barrier(t) - 1
        nxt = defaultdict(int)
        for d, count in states.items():
            for d2 in range(0, d + eps + 1):
                nxt[d2] += count
        states = dict(nxt)
    return states


def conditional_haar_probability(states: dict[int, int], t: int) -> float:
    # S_t = floor(tL)-D_t; word probability is 2^{-S_t}.
    prefix_weight = 2.0 ** (-sum(PREFIX))
    return sum(c * 2.0 ** (-(barrier(t) - d)) for d, c in states.items()) / prefix_weight


def periodic_point(block: list[int]) -> Fraction:
    """Fixed point of one accelerated valuation block.

    If T_block(x)=(3^p x+C)/2^A, then x=C/(2^A-3^p).
    """
    C = 0
    S = 0
    for a in block:
        C = 3 * C + (1 << S)
        S += a
    p = len(block)
    return Fraction(C, (1 << S) - 3**p)


def is_cyclically_coefficient_safe(block: list[int]) -> bool:
    """Sufficient direct check for a periodic word repeated from phase zero."""
    if not block:
        return False
    A = sum(block)
    p = len(block)
    if A >= p * L:
        return False
    # Check enough repeats to catch each cyclic phase against the global barrier.
    s = 0
    for t in range(1, 8 * p + 1):
        s += block[(t - 1) % p]
        if s > barrier(t):
            return False
    return True


def main():
    out = Path("agent-state/collatz-2adic-survivors.json")
    t_values = (20, 50, 100, 200)

    bands = {}
    for t in t_values:
        full = full_safe_state(t)
        p_full = conditional_haar_probability(full, t)
        row = {"all_safe_probability": p_full, "bands": {}}
        for B in (0, 1, 2, 3, 4, 5, 10):
            st = bounded_slack_state(B, t)
            p = conditional_haar_probability(st, t)
            row["bands"][str(B)] = {
                "word_count": sum(st.values()),
                "conditional_haar_probability": p,
                "fraction_of_safe_probability": p / p_full,
            }
        bands[str(t)] = row

    zword = zero_slack_word(300)
    zrows = canonical_residues(zword)
    longest_zero_lift = 0
    run = 0
    zero_runs = []
    for row in zrows[1:]:
        if row["lift_digit"] == 0:
            run += 1
            longest_zero_lift = max(longest_zero_lift, run)
        elif run:
            zero_runs.append(run)
            run = 0
    if run:
        zero_runs.append(run)

    # Small examples of periodic safe tails. Every such fixed point must be negative.
    examples = []
    for block in ([1], [1, 1], [1, 2], [1, 1, 2], [1, 2, 1, 2, 1]):
        x = periodic_point(list(block))
        examples.append({
            "block": list(block),
            "sum_A": sum(block),
            "period_p": len(block),
            "average_A_over_p": sum(block) / len(block),
            "below_log2_3": sum(block) < len(block) * L,
            "periodic_point_num": x.numerator,
            "periodic_point_den": x.denominator,
            "periodic_point_sign": -1 if x < 0 else (1 if x > 0 else 0),
            "phase_zero_safe_check": is_cyclically_coefficient_safe(list(block)),
        })

    report = {
        "log2_3": L,
        "canonical_residue_formula": {
            "iterate": "T^t(x)=(3^t*x+C_t)/2^S_t",
            "C_recurrence": "C_(t+1)=3*C_t+2^S_t",
            "residue": "r_t=-C_t*3^{-t} mod 2^S_t",
            "positive_integer_criterion": (
                "An infinite valuation word represents a nonnegative integer n iff "
                "the canonical residues r_t are eventually constant at n once 2^S_t>n."
            ),
        },
        "periodic_safe_obstruction": {
            "statement": (
                "Any eventually periodic coefficient-safe accelerated valuation word "
                "represents a negative rational 2-adic, hence cannot represent a positive integer."
            ),
            "proof_core": (
                "For a tail period of length p and valuation sum A, global coefficient safety "
                "forces A/p<log2(3) (strict because log2(3) is irrational). "
                "The period map has fixed point C/(2^A-3^p), with C>0 and denominator<0. "
                "Inverse accelerated steps x=(2^a*y-1)/3 preserve negativity."
            ),
            "examples": examples,
        },
        "critical_density_translation": {
            "ordinary_half_collatz_steps": "ell=S_t",
            "odd_steps": "h=t",
            "parity_density": "h/ell=t/S_t",
            "safe_side": "S_t/t <= log2(3), equivalently t/S_t >= 1/log2(3)",
            "rational_noncyclic_necessary_condition": (
                "Lopez-Stoll imply the critical value must be approached: "
                "liminf t/S_t=1/log2(3), hence liminf D_t/t=0 along accelerated block endpoints."
            ),
            "research_target": (
                "A positive integer survivor must therefore be aperiodic, coefficient-safe, "
                "and return arbitrarily close to the critical boundary on a linear scale."
            ),
        },
        "bounded_slack_bands": bands,
        "zero_slack_path": {
            "description": "The unique D_t=0 path for all t>=3.",
            "valuation_prefix_60": zword[:60],
            "canonical_residue_rows_20": zrows[:20],
            "canonical_residue_at_300": zrows[-1]["canonical_residue"],
            "modulus_bits_at_300": zrows[-1]["modulus_bits"],
            "longest_zero_lift_run_through_300": longest_zero_lift,
            "eventual_stabilization_seen": False,
        },
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(out),
        "longest_zero_lift_run_zero_slack_path": longest_zero_lift,
        "safe_prob_t100": bands["100"]["all_safe_probability"],
        "fraction_safe_with_slack_le_5_t100": bands["100"]["bands"]["5"]["fraction_of_safe_probability"],
        "fraction_safe_with_slack_le_10_t200": bands["200"]["bands"]["10"]["fraction_of_safe_probability"],
    }, indent=2))


if __name__ == "__main__":
    main()
