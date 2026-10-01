#!/usr/bin/env python3
"""Merge contiguous branch interval scan shards and fail closed on gaps/unresolved seeds."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--glob",default="shards/shard-*.json")
    ap.add_argument("--expected-low",type=int,required=True)
    ap.add_argument("--expected-high",type=int,required=True)
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    paths=sorted(Path(".").glob(args.glob))
    if not paths: raise SystemExit("no shard files")
    rows=[json.loads(p.read_text()) for p in paths]
    rows.sort(key=lambda r:r["low_inclusive"])
    cursor=args.expected_low
    total=0
    maxrow={"t":-1}
    shards=[]
    for r in rows:
        assert r["low_inclusive"]==cursor,(cursor,r["low_inclusive"])
        assert r["status"]=="complete",r
        assert r["unresolved_count_capped"]==0,r
        assert r["unresolved_sample"]==[],r
        cursor=r["high_exclusive"]
        total+=r["tested"]
        if r["max_observed_first_descent"]["t"]>maxrow["t"]:
            maxrow=r["max_observed_first_descent"]
        shards.append({
          "low_inclusive":r["low_inclusive"],"high_exclusive":r["high_exclusive"],
          "tested":r["tested"],"max_observed_first_descent":r["max_observed_first_descent"]
        })
    assert cursor==args.expected_high,(cursor,args.expected_high)
    out={
      "status":"complete",
      "low_inclusive":args.expected_low,
      "high_exclusive":args.expected_high,
      "tested":total,
      "unresolved_count_capped":0,
      "unresolved_sample":[],
      "max_observed_first_descent":maxrow,
      "shard_count":len(shards),
      "shards":shards,
      "note":"Merged exact integer Terras scans over all old-residual branch seeds in a contiguous interval."
    }
    p=Path(args.output);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in out.items() if k!="shards"},indent=2))

if __name__=="__main__":main()
