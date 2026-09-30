#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.parse, urllib.request
from pathlib import Path

BASE="https://prove2.me/api/v1"
OUT=Path("agent-state/formalpedia-scout.json")

def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-formalpedia-scout/1"}
    data=None
    if token: h["Authorization"]=f"Bearer {token}"
    if payload is not None:
        h["Content-Type"]="application/json"; data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read().decode(); return json.loads(raw) if raw else {}

def browse(token,q=None,tags=None,offset=0,limit=200):
    params={"status":"Open","sort":"newest","limit":str(limit),"offset":str(offset)}
    if q: params["q"]=q
    if tags: params["tags"]=tags
    return api("GET","/theorems?"+urllib.parse.urlencode(params),token=token)

def score(t):
    s=(t.get("formal_statement") or "")
    pre=(t.get("preamble") or "")
    tags=set(t.get("tags") or [])
    name=t.get("theorem_name") or ""
    pts=0
    reasons=[]
    if "workbook" in tags or "Workbook" in name:
        pts+=4; reasons.append("workbook")
    if "elementary" in tags:
        pts+=3; reasons.append("elementary")
    if "arithmetic" in tags:
        pts+=3; reasons.append("arithmetic")
    if len(s)<180:
        pts+=4; reasons.append("short statement")
    elif len(s)<300:
        pts+=2; reasons.append("moderate statement")
    if any(x in pre for x in ["NormNum","Ring","Linarith"]):
        pts+=2; reasons.append("basic tactics imported")
    if "∀" not in s and "fun " not in s and "∃" not in s:
        pts+=2; reasons.append("closed proposition")
    if "Finset" in s:
        pts-=1
    if any(x in s for x in ["Real.logb","Real.log ","Real.sqrt","Real.sin","Real.cos","Real.tan","abs "]):
        pts+=1; reasons.append("standard special function")
    if any(x in s for x in ["IsCompact","Measure","Category","Ordinal","SimpleGraph","Matrix","Polynomial"]):
        pts-=5; reasons.append("heavy structure")
    return pts,reasons

def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    token=api("POST","/agent/refresh",payload={"api_key":key})["access_token"]
    pools=[]
    for q in ["WorkbookCorrected","WorkbookRestored","elementary","arithmetic"]:
        for offset in [0,200,400]:
            res=browse(token,q=q,offset=offset)
            pools.extend(res.get("theorems",[]))
            if len(res.get("theorems",[]))<200: break
    # Also sample newest opens regardless of query.
    for offset in [0,200]:
        pools.extend(browse(token,offset=offset).get("theorems",[]))
    uniq={}
    for t in pools:
        uniq[t["theorem_id"]]=t
    ranked=[]
    for t in uniq.values():
        pts,reasons=score(t)
        ranked.append({
            "score":pts,
            "reasons":reasons,
            "theorem_id":t.get("theorem_id"),
            "theorem_name":t.get("theorem_name"),
            "theorem_title":t.get("theorem_title"),
            "formal_statement":t.get("formal_statement"),
            "natural_language_statement":t.get("natural_language_statement"),
            "preamble":t.get("preamble"),
            "tags":t.get("tags"),
            "created_at":t.get("created_at"),
            "vote_count":t.get("vote_count"),
        })
    ranked.sort(key=lambda x:(-x["score"], x["created_at"] or ""))
    corrected = browse(token,q="WorkbookCorrected",offset=0).get("theorems",[])
    restored = browse(token,q="WorkbookRestored",offset=0).get("theorems",[])
    newest = []
    for off in [0,200,400,600,800]:
        newest.extend(browse(token,offset=off).get("theorems",[]))
    report={
        "count":len(ranked),
        "top":ranked[:120],
        "corrected_open":corrected,
        "restored_open":restored,
        "newest_open":newest[:1000],
        "easy_text_candidates": sorted(
            [
                {
                    **t,
                    "_clues": sum(
                        1 for phrase in [
                            "immediate", "direct consequence", "follows directly",
                            "special case", "by reflexivity", "by simplification",
                            "closed under", "range restriction", "exactly the",
                            "reduces to", "definitionally"
                        ] if phrase in ((t.get("natural_language_statement") or "") + " " + (t.get("preamble") or "")).lower()
                    )
                }
                for t in newest
                if len(t.get("formal_statement") or "") < 700
            ],
            key=lambda t: (-t["_clues"], len(t.get("formal_statement") or ""), t.get("created_at") or ""),
        )[:100],
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"count":len(ranked),"top":[{"score":x["score"],"id":x["theorem_id"],"name":x["theorem_name"],"statement":x["formal_statement"]} for x in ranked[:30]]},indent=2))
if __name__=="__main__": main()
