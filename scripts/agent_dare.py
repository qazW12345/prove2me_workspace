#!/usr/bin/env python3
"""Read-only deep inspection of the selected DARE Prove2Me mission."""
from __future__ import annotations
import json, os, urllib.error, urllib.parse, urllib.request
from pathlib import Path
BASE="https://prove2.me/api/v1"
MISSION_ID="7ab42be1-7a05-40ad-8136-424509845706"
ROOT_ID="d3296345-6939-45d7-a96f-3fa2c1c27058"
OUT=Path("agent-state/dare.json")
def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-dare-inspect/1"}; data=None
    if token: h["Authorization"]=f"Bearer {token}"
    if payload is not None: h["Content-Type"]="application/json"; data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read().decode(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors="replace"); return {"_error":f"HTTP {e.code}: {raw[:1000]}"}
def q(x): return urllib.parse.quote(str(x),safe="")
def submissions(tid,token):
    page=api("GET",f"/theorems/{q(tid)}/submissions?limit=200&offset=0",token); out=[]
    for s in page.get("submissions",[]):
        z=dict(s); sid=s.get("id")
        if sid:
            src=api("GET",f"/submissions/{q(sid)}/solution",token)
            if "content" in src: z["solution_content"]=src["content"]
        out.append(z)
    return {"total":page.get("total",len(out)),"submissions":out}
def bundle(tid,token):
    return {
        "theorem":api("GET",f"/theorems/{q(tid)}",token),
        "decompositions":api("GET",f"/theorems/{q(tid)}/decompositions",token),
        "submissions":submissions(tid,token),
        "mentions":api("GET",f"/theorems/{q(tid)}/mentions",token),
        "missions":api("GET",f"/theorems/{q(tid)}/missions",token),
    }
def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    auth=api("POST","/agent/refresh",payload={"api_key":key}); token=auth["access_token"]
    ms=api("GET",f"/missions/{MISSION_ID}/milestones?limit=100&offset=0",token)
    milestones=[]
    for m in ms.get("milestones",[]):
        z=dict(m); mid=m.get("id")
        if mid: z["history"]=api("GET",f"/milestones/{q(mid)}/history?limit=100&offset=0",token)
        th=m.get("theorem")
        if isinstance(th,dict) and th.get("id"): z["theorem_detail"]=bundle(th["id"],token)
        milestones.append(z)
    searches={}
    for term in ["DAREx","Kearns","Saul","coefficient energy","Bernoulli","missing mass","empiricalVariance","DARE"]:
        searches[term]=api("GET",f"/theorems?q={q(term)}&limit=100&offset=0",token)
    definition_probes={}
    for path in ["/definitions?limit=100&offset=0","/definitions/Def_DAREx_Model"]:
        definition_probes[path]=api("GET",path,token)
    result={
        "platform_version":auth.get("version"),
        "mission_id":MISSION_ID,
        "comments":api("GET",f"/missions/{MISSION_ID}/comments",token),
        "milestones":milestones,
        "root":bundle(ROOT_ID,token),
        "searches":searches,
        "definition_probes":definition_probes,
    }
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "milestones":[{"id":m.get("id"),"title":m.get("title"),"completed":m.get("completed"),"theorem":m.get("theorem")} for m in milestones],
        "root_submissions":result["root"]["submissions"]["total"],
        "search_counts":{k:(v.get("total",len(v.get("theorems",[]))) if isinstance(v,dict) else None) for k,v in searches.items()},
        "definition_probe_status":{k:v.get("_error","ok") for k,v in definition_probes.items()},
    },indent=2))
if __name__=="__main__": main()
