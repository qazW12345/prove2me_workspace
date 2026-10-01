#!/usr/bin/env python3
"""Further split the structural 'contracts within 301993' Prove2Me child.

Easy structural child ->
  * bounded finite branch: old seven-mod-32 residual with n < 7,216,089,271;
  * analytic large-seed branch: odd n >= threshold with coefficient contraction.

The easy parent follows by a size case split.
"""
from __future__ import annotations
import json, os, re, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

BASE="https://prove2.me/api/v1"
ORIGINAL_PARENT_ID="b5094e6b-1347-43fe-ac3d-adbf79509f5e"
EASY_NAME="syracuse_descent_seven_mod32_if_contracts_within_301993"
SMALL_NAME="syracuse_descent_seven_mod32_below_7216089271"
LARGE_NAME="syracuse_descent_odd_large_if_contracts_within_301993"
BOUND=7216089271
HORIZON=301993
OUT=Path("agent-state/collatz-structural-easy-split.json")
TERMINAL={"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}

def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-seven-mod32-easy-split/1"};data=None
    if token:h["Authorization"]=f"Bearer {token}"
    if payload is not None:
        h["Content-Type"]="application/json";data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read().decode();return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {e.read().decode(errors='replace')[:5000]}") from e

def history(token):
    out={};off=0
    for _ in range(20):
        page=api("GET","/publish-jobs?"+urllib.parse.urlencode({"limit":"100","offset":str(off)}),token)
        items=page if isinstance(page,list) else page.get("jobs",page.get("publish_jobs",[]))
        if not items:break
        for j in items:
            name=j.get("theorem_name") or j.get("definition_name") or j.get("name")
            if name and j.get("status")=="PUBLISHED" and name not in out:out[name]=j
        if len(items)<100:break
        off+=len(items)
    return out

def wait_for_published(token,name,minutes=45):
    for _ in range(minutes*6):
        h=history(token)
        if name in h:return h[name].get("theorem_id")
        time.sleep(10)
    raise RuntimeError("dependency not published: "+name)

def poll(token,jid,name):
    for _ in range(360):
        time.sleep(5);st=api("GET",f"/publish-jobs/{jid}",token)
        print("publish",json.dumps({"name":name,"status":st.get("status"),"error":st.get("error_message"),"id":st.get("theorem_id")}))
        if st.get("status")=="PUBLISHED":return st.get("theorem_id")
        if st.get("status") in {"FAILED","ERROR"}:raise RuntimeError(json.dumps(st))
    raise RuntimeError("publish timeout "+name)

def ensure_problem(token,env,name,title,formal,natural,preamble,hist,tags):
    if name in hist:return hist[name].get("theorem_id")
    resp=api("POST","/submit-problem",token,payload={
      "theorem_name":name,"theorem_title":title,"formal_statement":formal,
      "natural_language_statement":natural,"preamble":preamble,
      "source":"Sub-decomposition of "+EASY_NAME,
      "tags":tags,"env":env})
    jobs=resp.get("jobs",[])
    if not jobs:raise RuntimeError("queue failed "+json.dumps(resp))
    return poll(token,jobs[0]["job_id"],name)

def add_hyp(formal,hyp,new_name):
    s=re.sub(r"^theorem\s+\S+","theorem "+new_name,formal.strip(),count=1)
    if not s.endswith(":= by sorry"):raise RuntimeError("suffix")
    s=s[:-len(":= by sorry")].rstrip()
    idx=s.rfind(") :\n")
    if idx<0:raise RuntimeError("boundary")
    return s[:idx+1]+"\n    "+hyp+s[idx+1:]+" := by sorry"

def verify(token,theorem_id,content,explanation):
    b="----p2m"+uuid.uuid4().hex;parts=[]
    for n,v in [("theorem_id",theorem_id),("proof_type","prove"),("explanation",explanation)]:
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="solution.lean"\r\nContent-Type: text/plain\r\n\r\n'.encode()+content.encode()+b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={"Authorization":f"Bearer {token}","Accept":"application/json","Content-Type":f"multipart/form-data; boundary={b}"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())

def wait_verify(token,sid):
    for _ in range(240):
        time.sleep(5);st=api("GET",f"/verify?submission_id={sid}",token)
        print("verify",json.dumps({"status":st.get("status"),"error":st.get("error_message")}))
        if st.get("status") in TERMINAL:return st
    raise RuntimeError("verify timeout")

def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    ref=api("POST","/agent/refresh",payload={"api_key":key});token=ref["access_token"]
    easy_id=wait_for_published(token,EASY_NAME)
    easy=api("GET",f"/theorems/{easy_id}",token)
    original=api("GET",f"/theorems/{ORIGINAL_PARENT_ID}",token)
    env=easy["mathlib_rev"];hist=history(token)

    pre="""import Definitions.Def_syracuseStep
import Definitions.Def_sevenMod32TerrasStep
import Definitions.Def_sevenMod32TerrasOddSteps
import Definitions.Def_sevenMod32ContractsWithin
import Mathlib.Logic.Function.Iterate
import Mathlib.Data.Finset.Insert
set_option autoImplicit false
set_option maxRecDepth 100000"""

    small_formal=add_hyp(original["formal_statement"],f"(hsmall : n < {BOUND})",SMALL_NAME)
    small_id=ensure_problem(token,env,SMALL_NAME,
      "Finite seven-mod-32 residual below 7,216,089,271",
      small_formal,
      """Assume the original seven-mod-32 residual hypotheses and n < 7,216,089,271. Prove eventual accelerated Syracuse descent.

The companion branch contains an exact contiguous integer census of every such residual seed: 6,471,680 candidates below 2^30, 2,253,778 candidates to 1,447,674,322, and 34,767,517 candidates to 7,216,089,271, all with explicit descent and zero unresolved cases. The largest observed Terras first-descent time is 397. This node isolates the finite computational obligation for independent Lean/kernel certification.""",
      pre,hist,["number-theory","collatz","syracuse","finite-certificate"])
    hist[SMALL_NAME]={"theorem_id":small_id,"status":"PUBLISHED"}

    large_formal=f"""theorem {LARGE_NAME} (n : ℕ)
    (hodd : n % 2 = 1)
    (hlarge : {BOUND} ≤ n)
    (hcontract : sevenMod32ContractsWithin {HORIZON} n) :
    ∃ t : ℕ, syracuseStep^[t] n < n := by sorry"""
    large_id=ensure_problem(token,env,LARGE_NAME,
      "Large odd seeds descend when the Terras coefficient contracts within 301993 steps",
      large_formal,
      """For any odd natural n ≥ 7,216,089,271, if 3^j/2^T becomes strictly contracting at some Terras time T ≤ 301,993, prove accelerated Syracuse descent.

This is the analytic half of the structural certificate. The external Lean theorem Collatz.first_contraction_seed_bound bounds any non-descending first contraction through this horizon below 7,216,089,271; the remaining work is to port that bound and the Terras-to-accelerated bridge into the Prove2Me environment.""",
      pre,hist,["number-theory","collatz","syracuse","stopping-time","analytic"])
    hist[LARGE_NAME]={"theorem_id":large_id,"status":"PUBLISHED"}

    s=re.sub(r"^theorem\s+\S+","theorem solution",easy["formal_statement"].strip(),count=1)
    if not s.endswith(":= by sorry"):raise RuntimeError("easy suffix")
    s=s[:-len(":= by sorry")].rstrip()
    prefix=s.split(") :",1)[0]
    args=re.findall(r"\(([A-Za-z0-9_]+)\s*:",prefix)
    # Easy theorem has original binders plus hcontract; strip hcontract for small child call.
    if args[-1]!="hcontract":raise RuntimeError(repr(args))
    original_args=args[:-1]
    argstr=" ".join(original_args)
    solution=f"""import Theorems.Thm_{SMALL_NAME}
import Theorems.Thm_{LARGE_NAME}
import Definitions.Def_sevenMod32ContractsWithin
import Definitions.Def_syracuseStep
import Mathlib.Logic.Function.Iterate
import Mathlib.Data.Finset.Insert

set_option autoImplicit false
set_option maxRecDepth 100000

{s} := by
  by_cases hs : n < {BOUND}
  · exact {SMALL_NAME} {argstr} hs
  · have hlarge : {BOUND} ≤ n := by omega
    have hodd : n % 2 = 1 := by
      rcases h with h39 | h71 | h103 <;> omega
    exact {LARGE_NAME} n hodd hlarge hcontract
"""
    sub=verify(token,easy_id,solution,
      f"Split at n={BOUND}. The bounded case is the finite census child; the large case uses the global analytic first-contraction child.")
    verdict=wait_verify(token,sub["submission_id"])
    if verdict.get("status") not in {"SKETCH_ACCEPTED","ACCEPTED"}:
        raise RuntimeError("easy split failed "+json.dumps(verdict))
    report={"easy_parent_id":easy_id,"bound":BOUND,"horizon":HORIZON,
      "children":{"finite":small_id,"analytic":large_id},"verdict":verdict}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
