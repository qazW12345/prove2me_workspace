#!/usr/bin/env python3
"""Test the residue-2-mod-9 sampled-return route on the seven-mod-32 branch."""
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

def first_two_hit(n:int,limit=10000):
    x=n
    for t in range(limit+1):
        if x%9==2:
            return t,x
        x=terras(x)
    return None

def first_two_return(x:int,limit=10000):
    assert x%9==2
    y=x
    odd=0
    for t in range(1,limit+1):
        if y%2: odd+=1
        y=terras(y)
        if y%9==2:
            return t,odd,y
    return None

def first_descent(n:int,limit=10000):
    x=n
    for t in range(1,limit+1):
        x=terras(x)
        if x<n:return t,x
    return None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--depth",type=int,default=28)
    ap.add_argument("--output",default="agent-state/collatz-mod9-sampled-scan.json")
    args=ap.parse_args()
    lifts=1<<(args.depth-16)
    counts={
      "tested":0,"first_return_contracting":0,"first_return_noncontracting":0,
      "return_below_sampled":0,"return_below_original":0,
      "return_not_below_original":0,
    }
    longest_return={"t":-1}
    worst_ratio=None
    counterexamples=[]
    by_first_hit_residue={}
    max_hit_time={"t":-1}
    for base in BASES:
      for k in range(lifts):
        n=base+(k<<16); counts["tested"]+=1
        hit=first_two_hit(n)
        if hit is None:
            counterexamples.append({"n":n,"kind":"no_two_hit"}); continue
        s,q=hit
        if s>max_hit_time["t"]:max_hit_time={"n":n,"t":s,"q":q}
        ret=first_two_return(q)
        if ret is None:
            counterexamples.append({"n":n,"kind":"no_two_return","hit":hit}); continue
        t,j,r=ret
        contracting=3**j<2**t
        if contracting: counts["first_return_contracting"]+=1
        else: counts["first_return_noncontracting"]+=1
        if r<q: counts["return_below_sampled"]+=1
        if r<n: counts["return_below_original"]+=1
        else: counts["return_not_below_original"]+=1
        if t>longest_return.get("t",-1):
            longest_return={"n":n,"hit_time":s,"sampled":q,"t":t,"odd":j,"returned":r,
                            "contracting":contracting,"below_original":r<n}
        # exact rational ratio returned/original, compare cross products
        if worst_ratio is None or r*worst_ratio["n"] > worst_ratio["returned"]*n:
            worst_ratio={"n":n,"hit_time":s,"sampled":q,"return_time":t,"odd":j,"returned":r,
                         "ratio":r/n,"contracting":contracting}
        # Track first-hit sampled value modulo modest powers to find special structure.
        key=str(q%162)
        by_first_hit_residue[key]=by_first_hit_residue.get(key,0)+1
        if (not contracting or r>=n) and len(counterexamples)<100:
            counterexamples.append({"n":n,"hit_time":s,"sampled":q,"return_time":t,
              "odd":j,"returned":r,"contracting":contracting,"below_original":r<n,
              "first_descent":first_descent(n)})
    report={
      "depth":args.depth,"base_classes":395,"counts":counts,
      "max_first_hit_time":max_hit_time,"longest_first_return":longest_return,
      "worst_returned_over_original":worst_ratio,
      "first_hit_sampled_residue_mod162":dict(sorted(by_first_hit_residue.items(),key=lambda kv:int(kv[0]))),
      "counterexample_sample":counterexamples,
      "interpretation":{
        "target":"If every branch seed had a coefficient-contracting first return from its first 2 mod 9 hit AND that return fell below the original seed, the branch would have a direct finite sampled-return proof.",
        "warning":"A contracting first return is guaranteed to fall below the sampled state, not automatically below the original seed."
      }
    }
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"counts":counts,"max_first_hit":max_hit_time,
      "longest_return":longest_return,"worst_ratio":worst_ratio,
      "counterexample_sample_size":len(counterexamples)},indent=2))

if __name__=="__main__": main()
