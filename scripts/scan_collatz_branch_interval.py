#!/usr/bin/env python3
"""Incrementally scan a numeric interval of the seven-mod-32 residual branch.

For each branch seed n in [low, high), verify direct Terras descent below n.
The scan is exact integer arithmetic.  It is intended to extend the finite
base used by the first-contraction horizon splice without rescanning smaller
seeds.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path

S13={679,1191,2663,3687,4199,4455,5191,5607,5959,6215,6375,6631,6983,7079,7399,7495,7847,7911,8103}
S15={839,1095,2119,2279,2727,2983,3303,4007,6503,6759,7783,9959,10055,11079,11943,12967,14439,16743,16871,17735,17767,19623,20199,21223,23399,24647,24679,25703,25831,26087,26535,27111,27975,28999,29863,30311,30887}
S16={359,1351,2407,2791,2887,3239,3815,4775,5863,6247,7015,8263,8551,9319,9543,10151,10727,11431,12007,12615,12775,13671,13927,14503,15207,16455,17127,17223,17479,17511,18343,18919,19111,19367,19687,20807,21735,22119,22695,22887,23143,25415,25671,26343,26439,27303,27559,27879,28327,31079,31335,33255,34151,34535,34631,36519,37607,37735,40039,41063,41447,42215,42343,42471,43111,43335,44359,45223,45799,46247,46407,48295,49255,50407,50663,51271,51431,52071,52551,53159,53319,54375,54439,55207,56935,57671,58983,59463,59559,59623,60231,61351,62119,62279,63335,63591,64167,64871,65127}

def old_residual(n:int)->bool:
    return (n%128 in {39,71,103}
      and n%256 not in {39,199}
      and n%1024 not in {423,583,999}
      and n%4096 not in {231,615,935,1703,3143,3559,3911}
      and n%8192 not in S13 and n%32768 not in S15 and n%65536 not in S16)

BASES=[n for n in range(1<<16) if old_residual(n)]
assert len(BASES)==395

def terras(n:int)->int:
    return n//2 if n%2==0 else (3*n+1)//2

def descent(n:int,limit:int):
    x=n
    for t in range(1,limit+1):
        x=terras(x)
        if x<n:
            return t,x
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--low",type=int,required=True)
    ap.add_argument("--high",type=int,required=True)
    ap.add_argument("--step-limit",type=int,default=125742)
    ap.add_argument("--output",default="agent-state/collatz-branch-interval-scan.json")
    args=ap.parse_args()
    if not (0<=args.low<args.high): raise SystemExit("bad interval")

    tested=0
    unresolved=[]
    max_time={"t":-1}
    # enumerate only the 395 admissible residues mod 2^16
    for base in BASES:
        k0=max(0,(args.low-base+(1<<16)-1)//(1<<16))
        k1=(args.high-1-base)//(1<<16)
        if k1<k0: continue
        for k in range(k0,k1+1):
            n=base+(k<<16)
            if not (args.low<=n<args.high): continue
            tested+=1
            d=descent(n,args.step_limit)
            if d is None:
                if len(unresolved)<100:
                    unresolved.append(n)
            elif d[0]>max_time["t"]:
                max_time={"n":n,"t":d[0],"value":d[1]}
    report={
      "low_inclusive":args.low,
      "high_exclusive":args.high,
      "step_limit":args.step_limit,
      "base_residue_count":len(BASES),
      "tested":tested,
      "unresolved_count_capped":len(unresolved),
      "unresolved_sample":unresolved,
      "max_observed_first_descent":max_time,
      "status":"complete" if not unresolved else "has_unresolved_or_sample_cap",
      "note":"Exact integer Terras scan over every old-residual residue class in the numeric interval."
    }
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
