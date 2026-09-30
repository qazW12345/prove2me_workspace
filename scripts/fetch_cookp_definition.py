#!/usr/bin/env python3
from __future__ import annotations
import json, os, urllib.request
from pathlib import Path

BASE="https://prove2.me/api/v1"
DEF_ID="7c6b3da6-5145-4b2d-9550-f07c61d2c766"

key=os.environ["PROVE2ME_API_KEY"].strip()
req=urllib.request.Request(BASE+"/agent/refresh",data=json.dumps({"api_key":key}).encode(),headers={"Content-Type":"application/json"},method="POST")
with urllib.request.urlopen(req,timeout=60) as r:
    token=json.loads(r.read().decode())["access_token"]
req=urllib.request.Request(BASE+f"/theorems/{DEF_ID}",headers={"Authorization":f"Bearer {token}","Accept":"application/json"})
with urllib.request.urlopen(req,timeout=60) as r:
    d=json.loads(r.read().decode())
body=d["definition"]
p=Path("Definitions/Def_CookPvsNP_defs.lean")
p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(body if body.endswith("\n") else body+"\n",encoding="utf-8")
print("wrote",p,len(body))
