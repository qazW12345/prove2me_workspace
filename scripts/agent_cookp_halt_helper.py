#!/usr/bin/env python3
from __future__ import annotations
import json, os, time, urllib.request, urllib.error, urllib.parse, uuid
BASE="https://prove2.me/api/v1"
NAME="CookPvsNP.tm_run_eq_of_halting"
FORMAL=r'''namespace CookPvsNP

theorem tm_run_eq_of_halting {Γ : Type} (M : TM Γ) (c : Cfg Γ M.Q)
    (h : M.IsHalting c) (n : ℕ) : M.run n c = c := by sorry

end CookPvsNP'''
PRE=r'''import Mathlib
import Definitions.Def_CookPvsNP_defs

set_option autoImplicit false'''
SOL=r'''import Definitions.Def_CookPvsNP_defs

set_option autoImplicit false

theorem solution {Γ : Type} (M : CookPvsNP.TM Γ) (c : CookPvsNP.Cfg Γ M.Q)
    (h : M.IsHalting c) (n : ℕ) : M.run n c = c := by
  unfold CookPvsNP.TM.run
  apply Function.iterate_fixed
  simp [CookPvsNP.TM.step, h]
'''
def api(method,path,token=None,payload=None):
    h={"Accept":"application/json"}; data=None
    if token:h["Authorization"]=f"Bearer {token}"
    if payload is not None:h["Content-Type"]="application/json";data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    with urllib.request.urlopen(req,timeout=60) as r:
        raw=r.read().decode();return json.loads(raw) if raw else {}
def verify(token,tid):
    b="----p2m"+uuid.uuid4().hex;parts=[]
    for n,v in [("theorem_id",tid),("proof_type","prove"),("explanation","A halting Cook configuration is a fixed point of the machine step function by definition. Every finite iterate of a function fixes any fixed point, so every later run remains exactly at the same configuration.")]:
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="solution.lean"\r\nContent-Type: text/plain\r\n\r\n'.encode()+SOL.encode()+b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={"Authorization":f"Bearer {token}","Content-Type":f"multipart/form-data; boundary={b}","Accept":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())
def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    token=api("POST","/agent/refresh",payload={"api_key":key})["access_token"]
    q=api("GET","/theorems?"+urllib.parse.urlencode({"q":NAME,"limit":"20","offset":"0"}),token)
    tid=next((t["theorem_id"] for t in q.get("theorems",[]) if t.get("theorem_name")==NAME),None)
    if not tid:
        pub=api("POST","/submit-problem",token,payload={
          "theorem_name":NAME,"theorem_title":"Halting Cook configurations are fixed by every run iterate",
          "formal_statement":FORMAL,"natural_language_statement":"If a configuration of a Cook-style deterministic Turing machine is already halting, then running the machine for any further finite number of steps leaves that configuration unchanged.",
          "preamble":PRE,"tags":["complexity-theory","turing-machines","simulation"]})
        jid=pub["jobs"][0]["job_id"];print("publish",pub)
        for _ in range(160):
            time.sleep(5);st=api("GET",f"/publish-jobs/{jid}",token);print("pub",st.get("status"),st.get("error_message",""))
            if st.get("status")=="PUBLISHED":tid=st["theorem_id"];break
            if st.get("status") in {"FAILED","ERROR"}:raise RuntimeError(json.dumps(st))
    sub=verify(token,tid);print("submit",sub);sid=sub["submission_id"]
    for _ in range(160):
        time.sleep(5);st=api("GET",f"/verify?submission_id={sid}",token);print("verify",st.get("status"),st.get("error_message",""))
        if st.get("status") in {"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}:break
if __name__=="__main__":main()
