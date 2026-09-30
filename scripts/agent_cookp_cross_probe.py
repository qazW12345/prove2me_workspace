#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.request
from pathlib import Path

BASE="https://prove2.me/api/v1"
OUT=Path("agent-state/cookp-cross-probe.json")
IDS={
  "cook_target":"028ccdb8-1f42-4651-94d3-63758b6500fd",
  "cook_def":"7c6b3da6-5145-4b2d-9550-f07c61d2c766",
  "pvsnp_comp":"becb77d8-732b-4c31-8bee-4d0284e71760",
  "pvsnp_def":"7812f284-a31c-4ed6-95c0-eff181cdd944",
  "tape_step":"efd5b425-95e0-4cdc-b660-f6ea7d5a0e8e",
  "tape_run":"9d55c3c8-3b45-4c36-a8c2-aa6581cf8a5b",
  "pow_absorb":"c036863a-d94b-4492-86d6-ad7d210e8675",
  "out_len":"8b233c5d-cee7-43f1-b8fa-823fbc614cbd",
}

def get(path,token):
    req=urllib.request.Request(BASE+path,headers={"Authorization":f"Bearer {token}","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode())

def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    req=urllib.request.Request(BASE+"/agent/refresh",data=json.dumps({"api_key":key}).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r: token=json.loads(r.read().decode())["access_token"]
    out={k:get(f"/theorems/{v}",token) for k,v in IDS.items()}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(out,indent=2)+"\n")
    for k,v in out.items():
        print("\n###",k)
        print("name:",v.get("theorem_name"),"status:",v.get("status"))
        print("preamble:\n",v.get("preamble",""))
        print("formal:\n",v.get("formal_statement",""))
        if v.get("status")=="Definition":
            print("definition:\n",v.get("definition","")[:40000])
if __name__=="__main__": main()
