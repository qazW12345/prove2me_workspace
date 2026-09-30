#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.request, urllib.error, uuid

BASE="https://prove2.me/api/v1"
TARGETS=[
{
"id":"222cd0d9-2d37-4232-8975-4554b73da451",
"name":"WorkbookCorrected.plus_47605",
"proof_type":"prove",
"explanation":"""The formal theorem is simply (10=10). It does not contain the finite-sum expression described in the natural-language text. Therefore the Lean goal is closed directly by reflexivity.""",
"content":r'''import Mathlib.Tactic.NormNum

theorem solution : 10 = 10 := by
  rfl
'''
},
{
"id":"a7369287-fb7a-47cd-9b94-4abe32a07462",
"name":"WorkbookCorrected.plus_2048",
"proof_type":"prove",
"explanation":"""For positive base (2), real exponentiation satisfies
$$
2^{x-y}=\frac{2^x}{2^y}.
$$
Apply this with (x=\log_2 5) and (y=2). Mathlib's `Real.rpow_sub` gives the quotient with the denominator written as the real power (2^{(2:ℝ)}), and `Real.rpow_two` identifies this with the ordinary square (2^2), exactly matching the target.""",
"content":r'''import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Tactic.NormNum

theorem solution :
    (2:ℝ) ^ (Real.logb 2 5 - 2) =
      (2:ℝ) ^ (Real.logb 2 5) / (2:ℝ) ^ 2 := by
  rw [Real.rpow_sub (by norm_num), Real.rpow_two]
'''
}
]

def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-third-aisle/1"}; data=None
    if token: h["Authorization"]=f"Bearer {token}"
    if payload is not None:
        h["Content-Type"]="application/json"; data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read().decode(); return json.loads(raw) if raw else {}

def verify(token,t):
    boundary="----p2m"+uuid.uuid4().hex
    parts=[]
    for n,v in [("theorem_id",t["id"]),("proof_type",t["proof_type"]),("explanation",t["explanation"])]:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"solution.lean\"\r\nContent-Type: text/plain\r\n\r\n".encode()+t["content"].encode()+b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={
        "Authorization":f"Bearer {token}","Accept":"application/json",
        "Content-Type":f"multipart/form-data; boundary={boundary}",
        "User-Agent":"prove2me-third-aisle/1"
    },method="POST")
    try:
        with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"http_status":e.code,"submit_error":e.read().decode(errors="replace")}

def main():
    token=api("POST","/agent/refresh",payload={"api_key":os.environ["PROVE2ME_API_KEY"].strip()})["access_token"]
    results=[]
    for t in TARGETS:
        s=verify(token,t); results.append((t["name"],s)); print(t["name"],s)
    pending={s.get("submission_id"):name for name,s in results if s.get("submission_id")}
    terminal={"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}
    deadline=time.time()+900
    while pending and time.time()<deadline:
        time.sleep(8)
        for sid in list(pending):
            st=api("GET",f"/verify?submission_id={sid}",token=token)
            if st.get("status") in terminal:
                print(pending[sid],st.get("status"),st.get("error_message",""))
                del pending[sid]

if __name__=="__main__": main()
