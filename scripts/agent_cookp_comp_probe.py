#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.request, urllib.error, urllib.parse
from pathlib import Path

BASE="https://prove2.me/api/v1"
OUT=Path("agent-state/cookp-compose-probe.json")
DEF_ID="7c6b3da6-5145-4b2d-9550-f07c61d2c766"
THM_ID="028ccdb8-1f42-4651-94d3-63758b6500fd"

def api(method,path,token=None):
    h={"Accept":"application/json","User-Agent":"prove2me-cookp-probe/1"}
    if token: h["Authorization"]=f"Bearer {token}"
    req=urllib.request.Request(BASE+path,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read().decode(); return {"ok":True,"data":json.loads(raw) if raw else {}}
    except urllib.error.HTTPError as e:
        return {"ok":False,"status":e.code,"body":e.read().decode(errors="replace")[:4000]}

def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    ref=urllib.request.Request(BASE+"/agent/refresh",data=json.dumps({"api_key":key}).encode(),
      headers={"Content-Type":"application/json","Accept":"application/json"},method="POST")
    with urllib.request.urlopen(ref,timeout=60) as r: token=json.loads(r.read().decode())["access_token"]
    paths=[
      f"/theorems/{DEF_ID}",
      f"/definitions/{DEF_ID}",
      "/definitions?"+urllib.parse.urlencode({"definition_name":"CookPvsNP_defs"}),
      "/definitions?"+urllib.parse.urlencode({"q":"CookPvsNP_defs"}),
      f"/theorems/{THM_ID}",
      f"/theorems/{THM_ID}/decompositions",
      f"/theorems/{THM_ID}/submissions?limit=20&offset=0",
    ]
    out={p:api("GET",p,token) for p in paths}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
