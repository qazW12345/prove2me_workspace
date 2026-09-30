#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.request
BASE="https://prove2.me/api/v1"
IDS=["becb77d8-732b-4c31-8bee-4d0284e71760","c036863a-d94b-4492-86d6-ad7d210e8675","8b233c5d-cee7-43f1-b8fa-823fbc614cbd"]
def get(path,token):
    req=urllib.request.Request(BASE+path,headers={"Authorization":f"Bearer {token}","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())
def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    req=urllib.request.Request(BASE+"/agent/refresh",data=json.dumps({"api_key":key}).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r: token=json.loads(r.read().decode())["access_token"]
    for tid in IDS:
        print("\nTHEOREM",tid)
        subs=get(f"/theorems/{tid}/submissions?limit=20&offset=0",token)
        print(json.dumps(subs,indent=2))
        for s in subs.get("submissions",[]):
            sid=s.get("id")
            if sid:
                for path in [f"/submissions/{sid}",f"/verify?submission_id={sid}"]:
                    try:
                        print("\n",path)
                        print(json.dumps(get(path,token),indent=2))
                    except Exception as e:
                        print(path,"ERR",repr(e))
if __name__=="__main__":main()
