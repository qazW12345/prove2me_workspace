#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.request, urllib.error, uuid
from pathlib import Path

BASE="https://prove2.me/api/v1"
OUT=Path("agent-state/cleanup-second-aisle.json")

TARGETS=[
{
"id":"025d0490-fea5-40ba-8336-27d897bf3b62",
"name":"WorkbookCorrected.plus_27001",
"proof_type":"disprove",
"explanation":"""The statement is false. Since (25=5^2) and (125=5^3), the logarithm power law gives
$$
\log_5 25 + \log_5 125 = 2\log_5 5 + 3\log_5 5 = 2+3=5.
$$
Thus the left-hand side is (5), not (4). The Lean proof computes the two logarithms from `Real.logb_pow` and `Real.logb_self_eq_one`, then derives the contradiction arithmetically.""",
"content":r'''import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Tactic.NormNum

theorem solution :
    ¬ (Real.logb 5 (25) + Real.logb 5 (125) = 4) := by
  intro h
  have h5 : Real.logb 5 5 = 1 := by
    simpa using (Real.logb_self_eq_one (show (1 : ℝ) < 5 by norm_num))
  have h25 : Real.logb 5 25 = 2 := by
    calc
      Real.logb 5 25 = Real.logb 5 ((5 : ℝ) ^ 2) := by norm_num
      _ = (2 : ℕ) * Real.logb 5 5 := Real.logb_pow 5 5 2
      _ = 2 := by rw [h5]; norm_num
  have h125 : Real.logb 5 125 = 3 := by
    calc
      Real.logb 5 125 = Real.logb 5 ((5 : ℝ) ^ 3) := by norm_num
      _ = (3 : ℕ) * Real.logb 5 5 := Real.logb_pow 5 5 3
      _ = 3 := by rw [h5]; norm_num
  rw [h25, h125] at h
  norm_num at h
'''
},
{
"id":"306ad1d3-54a4-4381-95a6-98a82e56e0fd",
"name":"WorkbookCorrected.plus_11295",
"proof_type":"disprove",
"explanation":"""The formal Lean statement is false because the inner exponent `1 / 2` is not annotated as a real number. In this ordinary power expression Lean interprets it as natural-number division, hence (1/2=0) and
$$
(4:ℝ)^{1/2}=4^0=1.
$$
The right-hand side is therefore (1^{-sqrt2}=1). On the other hand (sqrt2>0), so (-sqrt2<0), and since (2>1), the real-power monotonicity theorem gives
$$
2^{-sqrt2}<1.
$$
Therefore the two sides cannot be equal.""",
"content":r'''import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith

theorem solution :
    ¬ ((2:ℝ) ^ (-Real.sqrt 2) = ((4:ℝ) ^ (1 / 2)) ^ (-Real.sqrt 2)) := by
  intro h
  have hs : 0 < Real.sqrt 2 := Real.sqrt_pos.2 (by norm_num)
  have hlt : (2 : ℝ) ^ (-Real.sqrt 2) < 1 :=
    Real.rpow_lt_one_of_one_lt_of_neg (by norm_num) (neg_lt_zero.mpr hs)
  have hrhs : ((4 : ℝ) ^ (1 / 2)) ^ (-Real.sqrt 2) = 1 := by
    norm_num
  rw [hrhs] at h
  linarith
'''
}
]

def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-second-aisle/1"}; data=None
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
      "User-Agent":"prove2me-second-aisle/1"
    },method="POST")
    try:
        with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"http_status":e.code,"submit_error":e.read().decode(errors="replace")}

def main():
    token=api("POST","/agent/refresh",payload={"api_key":os.environ["PROVE2ME_API_KEY"].strip()})["access_token"]
    results=[]
    for t in TARGETS:
        s=verify(token,t); results.append({"target":t["name"],"theorem_id":t["id"],"submit":s}); print(t["name"],s)
    pending={r["submit"].get("submission_id"):r for r in results if r["submit"].get("submission_id")}
    terminal={"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}
    deadline=time.time()+900
    while pending and time.time()<deadline:
        time.sleep(8)
        for sid in list(pending):
            st=api("GET",f"/verify?submission_id={sid}",token=token)
            pending[sid]["verdict"]=st
            if st.get("status") in terminal:
                print(pending[sid]["target"],st.get("status"),st.get("error_message",""))
                del pending[sid]
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps({"results":results,"pending":list(pending)},indent=2)+"\n")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"results":results,"pending":list(pending)},indent=2)+"\n")

if __name__=="__main__": main()
