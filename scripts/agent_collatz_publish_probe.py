#!/usr/bin/env python3
import json, os, urllib.request, urllib.parse
from pathlib import Path
BASE="https://prove2.me/api/v1"
OUT=Path("agent-state/collatz-recursive-publish-probe.json")
def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"collatz-publish-probe/1"}; data=None
    if token: h["Authorization"]=f"Bearer {token}"
    if payload is not None:
        h["Content-Type"]="application/json"; data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read().decode(); return json.loads(raw) if raw else {}
def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    token=api("POST","/agent/refresh",payload={"api_key":key})["access_token"]
    page=api("GET","/publish-jobs?limit=100&offset=0",token=token)
    jobs=page if isinstance(page,list) else page.get("jobs",page.get("publish_jobs",[]))
    keep=[]
    for j in jobs:
        name=j.get("theorem_name") or j.get("definition_name") or j.get("name") or ""
        if "syracuse" in name.lower() and ("new21" in name.lower() or "new22" in name.lower() or "new23" in name.lower() or "new24" in name.lower() or "new25" in name.lower() or "2097152" in name or "4194304" in name or "8388608" in name or "16777216" in name or "33554432" in name):
            keep.append({k:j.get(k) for k in ("job_id","id","kind","theorem_name","definition_name","name","status","theorem_id","error_message","created_at","updated_at")})
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"jobs":keep},indent=2)+"\n")
    print(json.dumps({"jobs":keep},indent=2))
if __name__=="__main__": main()
