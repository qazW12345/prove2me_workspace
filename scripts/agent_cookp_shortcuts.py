#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.parse, urllib.request, urllib.error

BASE="https://prove2.me/api/v1"
SID="72f1f4b2-9ac8-47ae-88c0-a894ef6a0bf5"

def req(path, token):
    r=urllib.request.Request(BASE+path,headers={"Authorization":f"Bearer {token}","Accept":"application/json,text/plain,*/*"})
    try:
        with urllib.request.urlopen(r,timeout=60) as h:
            raw=h.read().decode(errors="replace")
            try: body=json.loads(raw)
            except: body=raw[:12000]
            return {"status":h.status,"body":body}
    except urllib.error.HTTPError as e:
        return {"status":e.code,"body":e.read().decode(errors="replace")[:4000]}

def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    rr=urllib.request.Request(BASE+"/agent/refresh",data=json.dumps({"api_key":key}).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(rr,timeout=60) as h: token=json.loads(h.read().decode())["access_token"]

    qs=["CookPvsNP halt run","CookPvsNP halting","CookPvsNP relabel","CookPvsNP rename",
        "CookPvsNP simulate","CookPvsNP compose","CookPvsNP output","CookPvsNP injection",
        "CookPvsNP tape alphabet","CookPvsNP polynomial budget"]
    for q in qs:
        out=req("/theorems?"+urllib.parse.urlencode({"q":q,"limit":"100","offset":"0"}),token)
        rows=[]
        if out["status"]==200 and isinstance(out["body"],dict):
            for t in out["body"].get("theorems",[]):
                rows.append({"id":t.get("theorem_id"),"name":t.get("theorem_name"),"status":t.get("status"),"title":t.get("theorem_title")})
        print("\nSEARCH",q)
        print(json.dumps(rows,indent=2))

    for suffix in ["/file","/source","/download","/solution","/content"]:
        print("\nSUBFILE",suffix)
        print(json.dumps(req(f"/submissions/{SID}{suffix}",token),indent=2)[:14000])

if __name__=="__main__": main()
