#!/usr/bin/env python3
from __future__ import annotations

import json, os, time, urllib.request, urllib.error, uuid
from pathlib import Path

BASE = "https://prove2.me/api/v1"
OUT = Path("agent-state/cleanup-result.json")

TARGETS = [
    {
        "id": "0b2ef069-4e46-4965-bb5f-cb106334dc43",
        "name": "WorkbookCorrected.plus_59205",
        "proof_type": "disprove",
        "explanation": """The Lean statement is false because the exponent in `(2/5) ^ (2/5)` is inferred as a natural number. Hence `2 / 5 = 0` in the exponent and the right-hand side is (1). The target therefore asserts (1 < \log 2). But the standard strict logarithm bound (\log x < x-1) for positive (x \ne 1), applied at (x=2), gives (\log 2 < 1). Thus the stated proposition is false.""",
        "content": r'''import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith

theorem solution : ¬ (Real.log 2 > (2/5) ^ (2/5)) := by
  have h : Real.log 2 < 1 := by
    have h' := Real.log_lt_sub_one_of_pos (x := (2 : ℝ)) (by norm_num) (by norm_num)
    norm_num at h' ⊢
    exact h'
  norm_num
  linarith
'''
    },
    {
        "id": "65cd88b8-088a-4bcb-801b-e82e9faf5838",
        "name": "WorkbookCorrected.plus_15957",
        "proof_type": "prove",
        "explanation": """Write the base-five logarithm as a quotient of natural logarithms. Since (\log 5>0), the desired bound is equivalent to (\log 10 < \tfrac32\log 5). Using (10=2\cdot5), this reduces to (2\log 2<\log 5). But (2\log 2=\log 4), and (\log 4<\log 5) by strict monotonicity of the logarithm on positive reals.""",
        "content": r'''import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Analysis.SpecialFunctions.Log.Basic
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Linarith

theorem solution : Real.logb 5 10 < 3 / 2 := by
  rw [Real.logb]
  have h5 : 0 < Real.log 5 := Real.log_pos (by norm_num)
  rw [div_lt_iff₀ h5]
  rw [show (10 : ℝ) = 2 * 5 by norm_num,
      Real.log_mul (by norm_num) (by norm_num)]
  have h45 : Real.log (4 : ℝ) < Real.log 5 :=
    Real.log_lt_log (by norm_num) (by norm_num)
  rw [show (4 : ℝ) = 2 ^ 2 by norm_num, Real.log_pow] at h45
  norm_num at h45 ⊢
  linarith
'''
    },
    {
        "id": "5087755b-9ec3-4afc-a2ee-8f0d79d46674",
        "name": "WorkbookCorrected.plus_18935",
        "proof_type": "prove",
        "explanation": """Use the product law for logarithms in base (2). We have (\log_2 4=2) and (\log_2 2=1). Therefore (\log_2(4\cdot251)=2+\log_2 251) and (\log_2(2\cdot5)=1+\log_2 5). Substituting these two identities makes the two sides definitionally identical.""",
        "content": r'''import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Tactic.NormNum

theorem solution :
    (Real.logb 2 (4 * 251)) / (Real.logb 2 (2 * 5)) =
      (2 + Real.logb 2 251) / (1 + Real.logb 2 5) := by
  have h2 : Real.logb 2 2 = 1 := by
    simpa using (Real.logb_self_eq_one (show (1 : ℝ) < 2 by norm_num))
  have h4 : Real.logb 2 4 = 2 := by
    calc
      Real.logb 2 4 = Real.logb 2 (2 * 2) := by norm_num
      _ = Real.logb 2 2 + Real.logb 2 2 :=
        Real.logb_mul (by norm_num) (by norm_num)
      _ = 2 := by rw [h2]; norm_num
  calc
    Real.logb 2 (4 * 251) / Real.logb 2 (2 * 5)
        = (Real.logb 2 4 + Real.logb 2 251) /
          (Real.logb 2 2 + Real.logb 2 5) := by
            rw [Real.logb_mul (by norm_num) (by norm_num),
                Real.logb_mul (by norm_num) (by norm_num)]
    _ = (2 + Real.logb 2 251) / (1 + Real.logb 2 5) := by
      rw [h4, h2]
'''
    },
]

RECIP_PROOF = r'''import Mathlib.Analysis.SpecialFunctions.Log.Base
import Mathlib.Tactic.NormNum
import Mathlib.Tactic.Ring

theorem solution : {STATEMENT} := by
  let c : ℝ := 1 / 7
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

targets2 = [
    (
      "768cc757-f308-474b-ac9c-ce2c4ff41606",
      "WorkbookCorrected.plus_54693",
      "(1 / Real.logb 2 (1 / 7)) + (1 / Real.logb 3 (1 / 7)) + (1 / Real.logb 4 (1 / 7)) + (1 / Real.logb 5 (1 / 7)) + (1 / Real.logb 6 (1 / 7)) - (1 / Real.logb 7 (1 / 7)) - (1 / Real.logb 8 (1 / 7)) - (1 / Real.logb 9 (1 / 7)) - (1 / Real.logb 10 (1 / 7)) = 1"
    ),
    (
      "26ed6455-5abb-4035-8621-2bdf2ef2037e",
      "WorkbookCorrected.plus_66568",
      "1 / Real.logb 2 (1 / 7) + 1 / Real.logb 3 (1 / 7) + 1 / Real.logb 4 (1 / 7) + 1 / Real.logb 5 (1 / 7) + 1 / Real.logb 6 (1 / 7) - 1 / Real.logb 7 (1 / 7) - 1 / Real.logb 8 (1 / 7) - 1 / Real.logb 9 (1 / 7) - 1 / Real.logb 10 (1 / 7) = 1"
    ),
]
for tid, name, stmt in targets2:
    TARGETS.append({
        "id": tid, "name": name, "proof_type": "prove",
        "explanation": """Use the reciprocal-change-of-base identity ((\log_a c)^{-1}=\log_c a), equivalently Mathlib's `inv_logb_mul_base` and `inv_logb_div_base`. The five positive terms combine to the reciprocal logarithm with base (2\cdot3\cdot4\cdot5\cdot6=720); the four negative terms combine to the reciprocal logarithm with base (7\cdot8\cdot9\cdot10=5040). Their difference is therefore the reciprocal logarithm with base (720/5040=1/7). Since the argument is also (1/7), that logarithm equals (1), so its reciprocal is (1).""",
        "content": RECIP_PROOF.replace("{STATEMENT}", stmt),
    })

def api(method, path, token=None, payload=None):
    headers={"Accept":"application/json","User-Agent":"prove2me-cleanup-agent/1"}
    data=None
    if token: headers["Authorization"]=f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"]="application/json"
        data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=headers,method=method)
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read().decode()
        return json.loads(raw) if raw else {}

def verify(token, target):
    boundary="----p2m"+uuid.uuid4().hex
    parts=[]
    def field(name,value):
        parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode())
    field("theorem_id",target["id"])
    field("proof_type",target["proof_type"])
    field("explanation",target["explanation"])
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"solution.lean\"\r\nContent-Type: text/plain\r\n\r\n".encode()+target["content"].encode()+b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body=b"".join(parts)
    req=urllib.request.Request(BASE+"/verify",data=body,headers={
        "Authorization":f"Bearer {token}",
        "Accept":"application/json",
        "Content-Type":f"multipart/form-data; boundary={boundary}",
        "User-Agent":"prove2me-cleanup-agent/1",
    },method="POST")
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"submit_error": e.read().decode(errors="replace"), "http_status": e.code}

def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    ref=api("POST","/agent/refresh",payload={"api_key":key})
    token=ref["access_token"]
    results=[]
    for t in TARGETS:
        res=verify(token,t)
        results.append({"target":t["name"],"theorem_id":t["id"],"proof_type":t["proof_type"],"submit":res})
        print(t["name"], json.dumps(res))
    pending={r["submit"].get("submission_id"):r for r in results if r["submit"].get("submission_id")}
    deadline=time.time()+900
    final_status={"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}
    while pending and time.time()<deadline:
        time.sleep(10)
        for sid in list(pending):
            try:
                st=api("GET",f"/verify?submission_id={sid}",token=token)
            except Exception as e:
                continue
            pending[sid]["verdict"]=st
            if st.get("status") in final_status:
                print(pending[sid]["target"], st.get("status"), st.get("error_message",""))
                del pending[sid]
        OUT.parent.mkdir(parents=True,exist_ok=True)
        OUT.write_text(json.dumps({"results":results,"pending":list(pending)},indent=2)+"\n")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"results":results,"pending":list(pending)},indent=2)+"\n")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
