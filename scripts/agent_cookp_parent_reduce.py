#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.request, urllib.error, uuid
BASE="https://prove2.me/api/v1"
PARENT="028ccdb8-1f42-4651-94d3-63758b6500fd"
SOLUTION=r'''import Definitions.Def_CookPvsNP_defs
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
EXPL=("Unpack the two PolyTimeComputable hypotheses into finite work alphabets, symbol embeddings, "
      "Cook machines, exponents, and correctness/time guarantees. The witness-level theorem "
      "CookPvsNP.tm_compose_poly_witness merges those concrete witnesses into one finite-alphabet "
      "Cook machine with one polynomial exponent computing the composition. Repacking the resulting "
      "witnesses is exactly the definition of PolyTimeComputable for g after f.")
def refresh():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    req=urllib.request.Request(BASE+"/agent/refresh",data=json.dumps({"api_key":key}).encode(),headers={"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())["access_token"]
def submit(token):
    b="----p2m"+uuid.uuid4().hex
    parts=[]
    for n,v in [("theorem_id",PARENT),("proof_type","prove"),("explanation",EXPL)]:
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="solution.lean"\r\nContent-Type: text/plain\r\n\r\n'.encode()+SOLUTION.encode()+b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={"Authorization":f"Bearer {token}","Accept":"application/json","Content-Type":f"multipart/form-data; boundary={b}"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())
def get(token,sid):
    req=urllib.request.Request(BASE+f"/verify?submission_id={sid}",headers={"Authorization":f"Bearer {token}","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())
def main():
    token=refresh(); sub=None
    for i in range(8):
        try:
            sub=submit(token); break
        except urllib.error.HTTPError as e:
            body=e.read().decode(errors="replace")
            print("submit-error",e.code,body[:2000])
            if e.code not in {500,502,503,504}: raise
            time.sleep(8)
    if not sub: raise RuntimeError("submission did not succeed")
    print("submitted",json.dumps(sub))
    sid=sub["submission_id"]
    for _ in range(160):
        time.sleep(5)
        st=get(token,sid)
        print("status",json.dumps({"status":st.get("status"),"error":st.get("error_message")}))
        if st.get("status") in {"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}:
            print("FINAL",json.dumps(st)); return
if __name__=="__main__":main()
