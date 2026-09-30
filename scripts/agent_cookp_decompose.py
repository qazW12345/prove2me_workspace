#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.request, urllib.error, urllib.parse, uuid
from pathlib import Path
BASE="https://prove2.me/api/v1"
PARENT="028ccdb8-1f42-4651-94d3-63758b6500fd"
OUT=Path("agent-state/cookp-decompose.json")
CHILD_NAME="CookPvsNP.tm_compose_poly_witness"
CHILD_FORMAL=r'''namespace CookPvsNP

theorem tm_compose_poly_witness
    {Sym₁ Sym₂ Sym₃ Γ₁ Γ₂ : Type}
    [Fintype Γ₁] [Fintype Γ₂]
    (ι₁ : Sym₁ ↪ Γ₁) (ι₂₁ : Sym₂ ↪ Γ₁) (M₁ : TM Γ₁) (k₁ : ℕ)
    (ι₂₂ : Sym₂ ↪ Γ₂) (ι₃ : Sym₃ ↪ Γ₂) (M₂ : TM Γ₂) (k₂ : ℕ)
    (f : List Sym₁ → List Sym₂) (g : List Sym₂ → List Sym₃)
    (h₁ : ∀ x : List Sym₁,
      M₁.HaltsWithin (x.length ^ k₁ + k₁) (x.map ι₁) ∧
      M₁.output (M₁.run (x.length ^ k₁ + k₁) (M₁.init (x.map ι₁))) =
        (f x).map (some ∘ ι₂₁))
    (h₂ : ∀ y : List Sym₂,
      M₂.HaltsWithin (y.length ^ k₂ + k₂) (y.map ι₂₂) ∧
      M₂.output (M₂.run (y.length ^ k₂ + k₂) (M₂.init (y.map ι₂₂))) =
        (g y).map (some ∘ ι₃)) :
    ∃ (Γ : Type) (_ : Fintype Γ) (j₁ : Sym₁ ↪ Γ) (j₃ : Sym₃ ↪ Γ)
      (M : TM Γ) (k : ℕ),
      ∀ x : List Sym₁,
        M.HaltsWithin (x.length ^ k + k) (x.map j₁) ∧
        M.output (M.run (x.length ^ k + k) (M.init (x.map j₁))) =
          (g (f x)).map (some ∘ j₃) := by sorry

end CookPvsNP'''
CHILD_PREAMBLE=r'''import Mathlib
import Definitions.Def_CookPvsNP_defs
import Theorems.Thm_CookPvsNP_tm_output_length_le
import Theorems.Thm_CookPvsNP_nat_pow_add_le_pow_add

set_option autoImplicit false'''
PARENT_SOLUTION=r'''import Definitions.Def_CookPvsNP_defs
import Theorems.Thm_CookPvsNP_tm_compose_poly_witness

set_option autoImplicit false

namespace CookPvsNP

theorem solution {Sym₁ Sym₂ Sym₃ : Type}
    (f : List Sym₁ → List Sym₂) (g : List Sym₂ → List Sym₃)
    (hf : PolyTimeComputable f) (hg : PolyTimeComputable g) :
    PolyTimeComputable (g ∘ f) := by
  rcases hf with ⟨Γ₁, hfin₁, ι₁, ι₂₁, M₁, k₁, h₁⟩
  rcases hg with ⟨Γ₂, hfin₂, ι₂₂, ι₃, M₂, k₂, h₂⟩
  letI : Fintype Γ₁ := hfin₁
  letI : Fintype Γ₂ := hfin₂
  exact tm_compose_poly_witness ι₁ ι₂₁ M₁ k₁ ι₂₂ ι₃ M₂ k₂ f g h₁ h₂

end CookPvsNP'''
def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-cookp-decompose/1"}; data=None
    if token: h["Authorization"]=f"Bearer {token}"
    if payload is not None:
        h["Content-Type"]="application/json"; data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read().decode(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return {"http_status":e.code,"error_body":e.read().decode(errors="replace")}
def verify(token,theorem_id,content,explanation):
    b="----p2m"+uuid.uuid4().hex
    parts=[]
    for n,v in [("theorem_id",theorem_id),("proof_type","prove"),("explanation",explanation)]:
        parts.append(f'--{b}\\r\\nContent-Disposition: form-data; name="{n}"\\r\\n\\r\\n{v}\\r\\n'.encode())
    parts.append(f'--{b}\\r\\nContent-Disposition: form-data; name="file"; filename="solution.lean"\\r\\nContent-Type: text/plain\\r\\n\\r\\n'.encode()+content.encode()+b"\\r\\n")
    parts.append(f"--{b}--\\r\\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={"Authorization":f"Bearer {token}","Accept":"application/json","Content-Type":f"multipart/form-data; boundary={b}"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())
def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    token=api("POST","/agent/refresh",payload={"api_key":key})["access_token"]
    existing=api("GET","/theorems?"+urllib.parse.urlencode({"q":CHILD_NAME,"limit":"20","offset":"0"}),token)
    child_id=next((t.get("theorem_id") for t in existing.get("theorems",[]) if t.get("theorem_name")==CHILD_NAME),None)
    if not child_id:
        pub=api("POST","/submit-problem",token,payload={
          "theorem_name":CHILD_NAME,
          "theorem_title":"Concrete Cook-machine witnesses compose in polynomial time",
          "formal_statement":CHILD_FORMAL,
          "natural_language_statement":"Given concrete one-tape Cook machines witnessing polynomial-time computability of f and g, with possibly different finite work alphabets and explicit exponents, there is a single finite-alphabet Cook machine and a single exponent computing g after f. This isolates the machine-simulation and alphabet-merging content from the outer existential packaging of PolyTimeComputable.",
          "preamble":CHILD_PREAMBLE,
          "source":"Cook, The P versus NP problem, Clay Mathematics Institute (2000), Definition 3; standard closure of polynomial-time transducers under sequential composition.",
          "tags":["complexity-theory","turing-machines","polynomial-time","composition"]})
        print("publish",json.dumps(pub))
        jobs=pub.get("jobs",[])
        if not jobs: raise RuntimeError("child publish did not queue: "+json.dumps(pub))
        jid=jobs[0]["job_id"]
        for _ in range(120):
            time.sleep(5); st=api("GET",f"/publish-jobs/{jid}",token)
            print("publish-status",json.dumps({"status":st.get("status"),"error":st.get("error_message"),"theorem_id":st.get("theorem_id")}))
            if st.get("status") in {"PUBLISHED","FAILED","ERROR"}:
                if st.get("status")!="PUBLISHED": raise RuntimeError(json.dumps(st))
                child_id=st["theorem_id"]; break
    expl=("Unpack the two PolyTimeComputable hypotheses into finite work alphabets, symbol embeddings, "
          "Cook machines, exponents, and correctness/time guarantees. The imported witness-level "
          "composition theorem merges those concrete witnesses into one finite-alphabet Cook machine "
          "with one polynomial exponent computing g after f. Repacking those witnesses is exactly the "
          "definition of PolyTimeComputable for the composition.")
    sub=verify(token,PARENT,PARENT_SOLUTION,expl); print("verify",json.dumps(sub))
    sid=sub.get("submission_id"); verdict=None
    if sid:
        for _ in range(120):
            time.sleep(5); verdict=api("GET",f"/verify?submission_id={sid}",token)
            print("verdict",json.dumps({"status":verdict.get("status"),"error":verdict.get("error_message")}))
            if verdict.get("status") in {"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}: break
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"child_id":child_id,"submission":sub,"verdict":verdict},indent=2)+"\\n")
if __name__=="__main__": main()
