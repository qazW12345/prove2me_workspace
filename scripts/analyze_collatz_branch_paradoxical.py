#!/usr/bin/env python3
"""Pruned paradoxical-cylinder search restricted to the seven-mod-32 residual.

For each fixed Terras length T, search every seed satisfying the old residual
low-16-bit predicate that is coefficient-contracting at T but has not descended
below its start at any earlier time.  This is a finite computation at each T,
not an all-length proof.

The pruning envelope is copied from msharpe248/collatz analysis/paradoxical_pruned.py
and is backed there by Lean-proved suffix/correction bounds.
"""
from __future__ import annotations
import argparse, json
from bisect import bisect_left
from functools import cache
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
BASESET=set(BASES)
assert len(BASES)==395
ALLOWED_PREFIX=[None]*17
for d in range(17):
    m=1<<d
    ALLOWED_PREFIX[d]={r%m for r in BASES}

def step(n):return n//2 if n%2==0 else (3*n+1)//2

def orbit(seed,depth):
    out=[seed]
    for _ in range(depth):out.append(step(out[-1]))
    return out

@cache
def jump_table():
    rows=[]
    for r in range(256):
        vals=orbit(r,8); odd=sum(x%2 for x in vals[:-1])
        rows.append((vals[-1],3**odd,odd))
    return rows

def advance(n,length):
    tab=jump_table();odd=0
    for _ in range(length//8):
        endpoint,coef,c=tab[n&255];n=endpoint+coef*(n>>8);odd+=c
    for _ in range(length%8):
        odd+=n%2;n=step(n)
    return n,odd

def completion_parameters(length,depth,odd,powers,max_odd):
    k=min(length-depth,max_odd-odd)
    if k<0:return None
    return (powers[k],(1<<(length-k))*(powers[k]-(1<<k)),(1<<length)-powers[odd+k])

def branch_compatible(depth,r):
    if depth<=16:return r in ALLOWED_PREFIX[depth]
    return (r&65535) in BASESET

def search(length,work_limit=10_000_000,direct_limit=32):
    powers=[3**j for j in range(length+1)]
    max_odd=bisect_left(powers,1<<length)-1
    env=[[completion_parameters(length,d,o,powers,max_odd) for o in range(d+1)] for d in range(length+1)]
    stack=[(0,0,0,0,0)]
    visited=pruned=branch_pruned=resolved=checked=0
    paradoxical=[]
    no_prior=[]
    max_seed=None
    while stack and visited<work_limit:
        d,r,endpoint,odd,correction=stack.pop();visited+=1
        if not branch_compatible(d,r):
            branch_pruned+=1;continue
        params=env[d][odd]
        modulus=1<<d
        # minimum positive branch-compatible lift is not trivial before depth16.
        # Use the generic minimum 3; this weakens pruning but preserves correctness.
        minimum=r+modulus*max(0,(3-r+modulus-1)//modulus)
        if params is None or params[0]*correction+params[1] < params[2]*minimum:
            pruned+=1;continue
        seed_upper=(params[0]*correction+params[1])//params[2]
        qlo=(minimum-r)//modulus
        qhi=(seed_upper-r)//modulus
        # Resolve short quotient intervals directly. Filter branch predicate exactly.
        if d<length and qhi-qlo+1<=direct_limit:
            resolved+=1
            for q in range(qlo,qhi+1):
                n=r+modulus*q
                if not old_residual(n):continue
                checked+=1
                final,extra=advance(endpoint+powers[odd]*q,length-d)
                j=odd+extra
                if final>=n and powers[j]<(1<<length):
                    vals=orbit(n,length)
                    first=next((t for t,x in enumerate(vals) if x<n),None)
                    row={"length":length,"seed":n,"endpoint":final,"odd_steps":j,
                         "first_descent_within_segment":first}
                    paradoxical.append(row)
                    if first is None:no_prior.append(row)
                    max_seed=n if max_seed is None else max(max_seed,n)
            continue
        if d==length:
            denom=(1<<d)-powers[odd]
            if denom<=0 or endpoint<r:continue
            lo=max(qlo,0);hi=min(qhi,(endpoint-r)//denom)
            for q in range(lo,hi+1):
                n=r+(1<<d)*q
                if not old_residual(n):continue
                checked+=1
                vals=orbit(n,length)
                if vals[-1]>=n and powers[odd]<(1<<length):
                    first=next((t for t,x in enumerate(vals) if x<n),None)
                    row={"length":length,"seed":n,"endpoint":vals[-1],"odd_steps":odd,
                         "first_descent_within_segment":first}
                    paradoxical.append(row)
                    if first is None:no_prior.append(row)
                    max_seed=n if max_seed is None else max(max_seed,n)
            continue
        for lift in (1,0):
            value=endpoint+lift*powers[odd]
            bit=value%2
            stack.append((d+1,r+lift*(1<<d),step(value),odd+bit,
                          3*correction+(1<<d) if bit else correction))
    return {
      "length":length,
      "status":"complete" if not stack else "incomplete_work_limit",
      "visited_nodes":visited,"pruned_nodes":pruned,"branch_pruned_nodes":branch_pruned,
      "resolved_cylinders":resolved,"checked_seeds":checked,"pending_nodes":len(stack),
      "paradoxical_count":len(paradoxical),"no_prior_descent_count":len(no_prior),
      "max_paradoxical_seed":max_seed,
      "no_prior_descent_examples":no_prior[:100],
      "paradoxical_examples":paradoxical[:100],
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--lengths",nargs="+",type=int,default=[66,80,100,128,160,200])
    ap.add_argument("--work-limit",type=int,default=10_000_000)
    ap.add_argument("--direct-limit",type=int,default=32)
    ap.add_argument("--output",default="agent-state/collatz-branch-paradoxical-search.json")
    args=ap.parse_args()
    rows=[]
    for L in args.lengths:
        row=search(L,args.work_limit,args.direct_limit);rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if not k.endswith("examples")}),flush=True)
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({
      "scope":"fixed Terras lengths, restricted to old seven-mod-32 residual low-16-bit classes",
      "warning":"Finite computation only; complete status is per listed length, not all intermediate lengths or all lengths.",
      "results":rows},indent=2,sort_keys=True)+"\n")

if __name__=="__main__":main()
