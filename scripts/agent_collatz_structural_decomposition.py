#!/usr/bin/env python3
"""Publish a structural Prove2Me decomposition of the original seven-mod-32 residual.

Alternative to the residue-by-residue sieve:
  * child A: any coefficient contraction within 301,993 Terras steps forces descent;
  * child B: the coefficient-noncontracting 301,993-step tail still eventually descends.

The original parent follows by a single by_cases on the contraction predicate.
"""
from __future__ import annotations
import json, os, re, time, urllib.error, urllib.parse, urllib.request, uuid
from pathlib import Path

BASE="https://prove2.me/api/v1"
PARENT_ID="b5094e6b-1347-43fe-ac3d-adbf79509f5e"
HORIZON=301993
OUT=Path("agent-state/collatz-structural-decomposition.json")
TERMINAL={"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}

STEP_DEF="sevenMod32TerrasStep"
ODD_DEF="sevenMod32TerrasOddSteps"
CONTRACT_DEF="sevenMod32ContractsWithin"
EASY_NAME="syracuse_descent_seven_mod32_if_contracts_within_301993"
HARD_NAME="syracuse_descent_seven_mod32_after_301993_noncontracting_steps"

def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-seven-mod32-structural/1"}; data=None
    if token:h["Authorization"]=f"Bearer {token}"
    if payload is not None:
        h["Content-Type"]="application/json";data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read().decode();return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {raw[:5000]}") from e

def job_history(token):
    found={};offset=0
    for _ in range(20):
        page=api("GET","/publish-jobs?"+urllib.parse.urlencode({"limit":"100","offset":str(offset)}),token)
        items=page if isinstance(page,list) else page.get("jobs",page.get("publish_jobs",[]))
        if not items:break
        for j in items:
            name=j.get("theorem_name") or j.get("definition_name") or j.get("name")
            if name and j.get("status")=="PUBLISHED" and name not in found:found[name]=j
        if len(items)<100:break
        offset+=len(items)
    return found

def poll_many(token,pending):
    pending=dict(pending);done={}
    for _ in range(360):
        if not pending:return done
        time.sleep(5)
        for jid,name in list(pending.items()):
            st=api("GET",f"/publish-jobs/{jid}",token)
            print("publish",json.dumps({"name":name,"status":st.get("status"),"error":st.get("error_message"),"id":st.get("theorem_id")}))
            if st.get("status")=="PUBLISHED":
                done[name]=st;del pending[jid]
            elif st.get("status") in {"FAILED","ERROR"}:
                raise RuntimeError("publication failed: "+json.dumps(st))
    raise RuntimeError("publication timeout: "+repr(pending))

def ensure_definition(token,env,name,title,code,natural,history):
    if name in history:return history[name].get("theorem_id")
    resp=api("POST","/submit-definition",token,payload={
      "definition_name":name,"definition_title":title,"definition":code,
      "natural_language_statement":natural,
      "source":"Structural analysis of Prove2Me theorem "+PARENT_ID,
      "tags":["number-theory","collatz","syracuse","stopping-time"],"env":env})
    jid=resp.get("job_id")
    if not jid:raise RuntimeError("definition queue failed: "+json.dumps(resp))
    return poll_many(token,{jid:name})[name].get("theorem_id")

def add_hypothesis(formal,hyp,new_name):
    s=re.sub(r"^theorem\s+\S+","theorem "+new_name,formal.strip(),count=1)
    if not s.endswith(":= by sorry"):raise RuntimeError("unexpected parent suffix")
    s=s[:-len(":= by sorry")].rstrip()
    idx=s.rfind(") :\n")
    if idx<0:raise RuntimeError("conclusion boundary not found")
    return s[:idx+1]+"\n    "+hyp+s[idx+1:]+" := by sorry"

def ensure_problem(token,env,name,title,formal,natural,preamble,history,tags):
    if name in history:return history[name].get("theorem_id")
    resp=api("POST","/submit-problem",token,payload={
      "theorem_name":name,"theorem_title":title,"formal_statement":formal,
      "natural_language_statement":natural,"preamble":preamble,
      "source":"Structural decomposition of https://prove2.me/theorems/"+PARENT_ID,
      "tags":tags,"env":env})
    jobs=resp.get("jobs",[])
    if not jobs:raise RuntimeError("problem queue failed: "+json.dumps(resp))
    return poll_many(token,{jobs[0]["job_id"]:name})[name].get("theorem_id")

def verify(token,theorem_id,content,explanation):
    b="----p2m"+uuid.uuid4().hex;parts=[]
    for n,v in [("theorem_id",theorem_id),("proof_type","prove"),("explanation",explanation)]:
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="solution.lean"\r\nContent-Type: text/plain\r\n\r\n'.encode()+content.encode()+b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={
      "Authorization":f"Bearer {token}","Accept":"application/json",
      "Content-Type":f"multipart/form-data; boundary={b}"},method="POST")
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
    parent=api("GET",f"/theorems/{PARENT_ID}",token)
    assert parent.get("theorem_name")=="syracuse_descent_residual_seven_mod32_mod65536"
    env=parent["mathlib_rev"];history=job_history(token)

    defs={}
    defs[STEP_DEF]=ensure_definition(token,env,STEP_DEF,
      "Terras shortcut step for the seven-mod-32 structural decomposition",
      """def sevenMod32TerrasStep (n : ℕ) : ℕ :=
  if n % 2 = 0 then n / 2 else (3 * n + 1) / 2""",
      "The ordinary Terras shortcut map: halve an even input once, or apply (3n+1)/2 to an odd input.",history)
    history[STEP_DEF]={"theorem_id":defs[STEP_DEF],"status":"PUBLISHED"}

    defs[ODD_DEF]=ensure_definition(token,env,ODD_DEF,
      "Odd-step count along Terras iteration",
      """import Definitions.Def_sevenMod32TerrasStep

def sevenMod32TerrasOddSteps : ℕ → ℕ → ℕ
  | 0, _ => 0
  | t + 1, n =>
      (if n % 2 = 1 then 1 else 0) +
        sevenMod32TerrasOddSteps t (sevenMod32TerrasStep n)""",
      "Counts odd Terras steps among the first t iterations of the Terras shortcut map.",history)
    history[ODD_DEF]={"theorem_id":defs[ODD_DEF],"status":"PUBLISHED"}

    defs[CONTRACT_DEF]=ensure_definition(token,env,CONTRACT_DEF,
      "Coefficient contraction within a finite Terras horizon",
      """import Definitions.Def_sevenMod32TerrasOddSteps

def sevenMod32ContractsWithin (H n : ℕ) : Prop :=
  ∃ T : ℕ, T ≤ H ∧ 3 ^ sevenMod32TerrasOddSteps T n < 2 ^ T""",
      "There is a Terras time T at most H where the multiplicative coefficient 3^j/2^T is strictly below one.",history)
    history[CONTRACT_DEF]={"theorem_id":defs[CONTRACT_DEF],"status":"PUBLISHED"}

    common_pre="""import Definitions.Def_syracuseStep
import Definitions.Def_sevenMod32TerrasStep
import Definitions.Def_sevenMod32TerrasOddSteps
import Definitions.Def_sevenMod32ContractsWithin
import Mathlib.Logic.Function.Iterate
import Mathlib.Data.Finset.Insert
set_option autoImplicit false
set_option maxRecDepth 100000"""

    easy_formal=add_hypothesis(parent["formal_statement"],
      f"(hcontract : sevenMod32ContractsWithin {HORIZON} n)",EASY_NAME)
    hard_formal=add_hypothesis(parent["formal_statement"],
      f"(hnocontract : ¬ sevenMod32ContractsWithin {HORIZON} n)",HARD_NAME)

    easy_id=ensure_problem(token,env,EASY_NAME,
      "Seven-mod-32 residual descends if the coefficient contracts within 301993 Terras steps",
      easy_formal,
      """Assume the original seven-mod-32 residual hypotheses. If the Terras multiplicative coefficient becomes contracting at some time T ≤ 301993, prove that an accelerated Syracuse iterate is smaller than the starting value.

A reproducible computational/analytic certificate is available on the companion GitHub branch: all residual seeds below 7,216,089,271 were exhaustively checked to descend, while the Lean-formal first-contraction seed inequality from msharpe248/collatz bounds every non-descending first contraction through T=301993 below that threshold. This node packages the finite/analytic half of the structural reduction.""",
      common_pre,history,["number-theory","collatz","syracuse","stopping-time","finite-certificate"])
    history[EASY_NAME]={"theorem_id":easy_id,"status":"PUBLISHED"}

    hard_id=ensure_problem(token,env,HARD_NAME,
      "Hard seven-mod-32 tail after 301993 coefficient-noncontracting Terras steps",
      hard_formal,
      """Assume the original seven-mod-32 residual hypotheses and that the Terras multiplicative coefficient never contracts during the first 301993 ordinary Terras steps. Prove eventual accelerated Syracuse descent.

This is the structural hard core exposed by survivor analysis. Any counterexample to the original residual theorem must lie here: it must sustain a supercritical coefficient prefix for more than 301993 Terras steps. The companion analysis further shows that an infinite positive survivor would need an aperiodic critical 2-adic itinerary with slack tending to infinity but sublinear along a subsequence.""",
      common_pre,history,["number-theory","collatz","syracuse","stopping-time","hard-residual"])
    history[HARD_NAME]={"theorem_id":hard_id,"status":"PUBLISHED"}

    # Build parent proof using the original exact binder list by replacing theorem name.
    s=re.sub(r"^theorem\s+\S+","theorem solution",parent["formal_statement"].strip(),count=1)
    if not s.endswith(":= by sorry"):raise RuntimeError("parent suffix")
    s=s[:-len(":= by sorry")].rstrip()
    # Extract binder names in declaration order, excluding n is included.
    prefix=s.split(") :",1)[0]
    args=re.findall(r"\(([A-Za-z0-9_]+)\s*:",prefix)
    if not args or args[0]!="n":raise RuntimeError("could not recover parent binders: "+repr(args))
    argstr=" ".join(args)
    solution=f"""import Theorems.Thm_{EASY_NAME}
import Theorems.Thm_{HARD_NAME}
import Definitions.Def_sevenMod32ContractsWithin
import Definitions.Def_syracuseStep
import Mathlib.Logic.Function.Iterate
import Mathlib.Data.Finset.Insert

set_option autoImplicit false
set_option maxRecDepth 100000

{s} := by
  by_cases hc : sevenMod32ContractsWithin {HORIZON} n
  · exact {EASY_NAME} {argstr} hc
  · exact {HARD_NAME} {argstr} hc
"""
    sub=verify(token,PARENT_ID,solution,
      f"Split on whether the Terras coefficient contracts within {HORIZON} steps. The contracting case is exactly {EASY_NAME}; its negation is exactly {HARD_NAME}.")
    verdict=wait_verify(token,sub["submission_id"])
    if verdict.get("status") not in {"SKETCH_ACCEPTED","ACCEPTED"}:
        raise RuntimeError("parent structural sketch failed: "+json.dumps(verdict))

    report={"platform_version":ref.get("version"),"parent_id":PARENT_ID,"horizon":HORIZON,
      "definitions":defs,"children":{"easy":easy_id,"hard":hard_id},"parent_verdict":verdict}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report,indent=2))

if __name__=="__main__":main()
