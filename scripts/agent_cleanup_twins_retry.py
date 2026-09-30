#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.request, urllib.error, uuid
from pathlib import Path

BASE="https://prove2.me/api/v1"
OUT=Path("agent-state/cleanup-twins-result.json")

PROOF = r'''import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

theorem solution : {STATEMENT} := by
  let c : ℝ := 7⁻¹
  have hpos :
      (Real.logb 2 c)⁻¹ + (Real.logb 3 c)⁻¹ + (Real.logb 4 c)⁻¹ +
          (Real.logb 5 c)⁻¹ + (Real.logb 6 c)⁻¹ =
        (Real.logb 720 c)⁻¹ := by
    calc
      (Real.logb 2 c)⁻¹ + (Real.logb 3 c)⁻¹ + (Real.logb 4 c)⁻¹ +
          (Real.logb 5 c)⁻¹ + (Real.logb 6 c)⁻¹
          = (Real.logb (2 * 3) c)⁻¹ + (Real.logb 4 c)⁻¹ +
              (Real.logb 5 c)⁻¹ + (Real.logb 6 c)⁻¹ := by
                rw [Real.inv_logb_mul_base (a := (2 : ℝ)) (b := 3)
                  (by norm_num) (by norm_num) c]
      _ = (Real.logb ((2 * 3) * 4) c)⁻¹ +
              (Real.logb 5 c)⁻¹ + (Real.logb 6 c)⁻¹ := by
                rw [Real.inv_logb_mul_base (a := ((2 : ℝ) * 3)) (b := 4)
                  (by norm_num) (by norm_num) c]
      _ = (Real.logb (((2 * 3) * 4) * 5) c)⁻¹ +
              (Real.logb 6 c)⁻¹ := by
                rw [Real.inv_logb_mul_base (a := (((2 : ℝ) * 3) * 4)) (b := 5)
                  (by norm_num) (by norm_num) c]
      _ = (Real.logb ((((2 * 3) * 4) * 5) * 6) c)⁻¹ := by
                rw [Real.inv_logb_mul_base (a := ((((2 : ℝ) * 3) * 4) * 5)) (b := 6)
                  (by norm_num) (by norm_num) c]
      _ = (Real.logb 720 c)⁻¹ := by norm_num
  have hneg :
      (Real.logb 7 c)⁻¹ + (Real.logb 8 c)⁻¹ +
          (Real.logb 9 c)⁻¹ + (Real.logb 10 c)⁻¹ =
        (Real.logb 5040 c)⁻¹ := by
    calc
      (Real.logb 7 c)⁻¹ + (Real.logb 8 c)⁻¹ +
          (Real.logb 9 c)⁻¹ + (Real.logb 10 c)⁻¹
          = (Real.logb (7 * 8) c)⁻¹ +
              (Real.logb 9 c)⁻¹ + (Real.logb 10 c)⁻¹ := by
                rw [Real.inv_logb_mul_base (a := (7 : ℝ)) (b := 8)
                  (by norm_num) (by norm_num) c]
      _ = (Real.logb ((7 * 8) * 9) c)⁻¹ +
              (Real.logb 10 c)⁻¹ := by
                rw [Real.inv_logb_mul_base (a := ((7 : ℝ) * 8)) (b := 9)
                  (by norm_num) (by norm_num) c]
      _ = (Real.logb (((7 * 8) * 9) * 10) c)⁻¹ := by
                rw [Real.inv_logb_mul_base (a := (((7 : ℝ) * 8) * 9)) (b := 10)
                  (by norm_num) (by norm_num) c]
      _ = (Real.logb 5040 c)⁻¹ := by norm_num
  have hself : Real.logb c c = 1 := by
    apply (Real.logb_self_eq_one_iff).2
    dsimp [c]
    norm_num
  simp only [one_div]
  change (Real.logb 2 c)⁻¹ + (Real.logb 3 c)⁻¹ + (Real.logb 4 c)⁻¹ +
      (Real.logb 5 c)⁻¹ + (Real.logb 6 c)⁻¹ -
      (Real.logb 7 c)⁻¹ - (Real.logb 8 c)⁻¹ -
      (Real.logb 9 c)⁻¹ - (Real.logb 10 c)⁻¹ = 1
  calc
    _ = ((Real.logb 2 c)⁻¹ + (Real.logb 3 c)⁻¹ + (Real.logb 4 c)⁻¹ +
          (Real.logb 5 c)⁻¹ + (Real.logb 6 c)⁻¹) -
        ((Real.logb 7 c)⁻¹ + (Real.logb 8 c)⁻¹ +
          (Real.logb 9 c)⁻¹ + (Real.logb 10 c)⁻¹) := by ring
    _ = (Real.logb 720 c)⁻¹ - (Real.logb 5040 c)⁻¹ := by rw [hpos, hneg]
    _ = (Real.logb (720 / 5040) c)⁻¹ := by
      rw [Real.inv_logb_div_base (a := (720 : ℝ)) (b := 5040)
        (by norm_num) (by norm_num) c]
    _ = (Real.logb c c)⁻¹ := by
      congr 2
      dsimp [c]
      norm_num
    _ = 1 := by rw [hself]; norm_num
'''

TARGETS=[
 ("768cc757-f308-474b-ac9c-ce2c4ff41606","WorkbookCorrected.plus_54693","(1 / Real.logb 2 (1 / 7)) + (1 / Real.logb 3 (1 / 7)) + (1 / Real.logb 4 (1 / 7)) + (1 / Real.logb 5 (1 / 7)) + (1 / Real.logb 6 (1 / 7)) - (1 / Real.logb 7 (1 / 7)) - (1 / Real.logb 8 (1 / 7)) - (1 / Real.logb 9 (1 / 7)) - (1 / Real.logb 10 (1 / 7)) = 1"),
 ("26ed6455-5abb-4035-8621-2bdf2ef2037e","WorkbookCorrected.plus_66568","1 / Real.logb 2 (1 / 7) + 1 / Real.logb 3 (1 / 7) + 1 / Real.logb 4 (1 / 7) + 1 / Real.logb 5 (1 / 7) + 1 / Real.logb 6 (1 / 7) - 1 / Real.logb 7 (1 / 7) - 1 / Real.logb 8 (1 / 7) - 1 / Real.logb 9 (1 / 7) - 1 / Real.logb 10 (1 / 7) = 1")
]

def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-twins-retry/1"}; data=None
    if token: h["Authorization"]=f"Bearer {token}"
    if payload is not None: h["Content-Type"]="application/json"; data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read().decode(); return json.loads(raw) if raw else {}

def verify(token,tid,content):
    boundary="----p2m"+uuid.uuid4().hex
    expl="Using Mathlib's reciprocal change-of-base identities, collapse the five positive reciprocal logarithms to base 720 and the four negative terms to base 5040. Their difference collapses to the reciprocal logarithm with base 720/5040 = 1/7. The argument is also 1/7, so the logarithm is 1 and its reciprocal is 1."
    parts=[]
    for n,v in [("theorem_id",tid),("proof_type","prove"),("explanation",expl)]:
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{n}\"\r\n\r\n{v}\r\n".encode())
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"solution.lean\"\r\nContent-Type: text/plain\r\n\r\n".encode()+content.encode()+b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={"Authorization":f"Bearer {token}","Accept":"application/json","Content-Type":f"multipart/form-data; boundary={boundary}"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=60) as r: return json.loads(r.read().decode())
    except urllib.error.HTTPError as e: return {"http_status":e.code,"submit_error":e.read().decode(errors="replace")}

def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    token=api("POST","/agent/refresh",payload={"api_key":key})["access_token"]
    results=[]
    for tid,name,stmt in TARGETS:
        res=verify(token,tid,PROOF.replace("{STATEMENT}",stmt))
        results.append({"target":name,"theorem_id":tid,"submit":res})
        print(name,res)
    pending={r["submit"].get("submission_id"):r for r in results if r["submit"].get("submission_id")}
    final={"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}
    deadline=time.time()+900
    while pending and time.time()<deadline:
        time.sleep(10)
        for sid in list(pending):
            st=api("GET",f"/verify?submission_id={sid}",token=token)
            pending[sid]["verdict"]=st
            if st.get("status") in final:
                print(pending[sid]["target"],st.get("status"),st.get("error_message",""))
                del pending[sid]
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps({"results":results,"pending":list(pending)},indent=2)+"\n")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"results":results,"pending":list(pending)},indent=2)+"\n")

if __name__=="__main__": main()
