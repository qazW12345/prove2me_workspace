#!/usr/bin/env python3
from __future__ import annotations
import json, os, re, time, urllib.error, urllib.parse, urllib.request, uuid
from collections import Counter
from pathlib import Path

BASE="https://prove2.me/api/v1"
PARENT24_ID="45a0800b-e750-4c32-bc04-98c579509977"
OUT=Path("agent-state/collatz-residual-depth25.json")
CHUNK=800
TERMINAL={"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}

S13={679,1191,2663,3687,4199,4455,5191,5607,5959,6215,6375,6631,6983,7079,7399,7495,7847,7911,8103}
S15={839,1095,2119,2279,2727,2983,3303,4007,6503,6759,7783,9959,10055,11079,11943,12967,14439,16743,16871,17735,17767,19623,20199,21223,23399,24647,24679,25703,25831,26087,26535,27111,27975,28999,29863,30311,30887}
S16={359,1351,2407,2791,2887,3239,3815,4775,5863,6247,7015,8263,8551,9319,9543,10151,10727,11431,12007,12615,12775,13671,13927,14503,15207,16455,17127,17223,17479,17511,18343,18919,19111,19367,19687,20807,21735,22119,22695,22887,23143,25415,25671,26343,26439,27303,27559,27879,28327,31079,31335,33255,34151,34535,34631,36519,37607,37735,40039,41063,41447,42215,42343,42471,43111,43335,44359,45223,45799,46247,46407,48295,49255,50407,50663,51271,51431,52071,52551,53159,53319,54375,54439,55207,56935,57671,58983,59463,59559,59623,60231,61351,62119,62279,63335,63591,64167,64871,65127}

def api(method,path,token=None,payload=None):
    h={"Accept":"application/json","User-Agent":"prove2me-collatz-deeper/1"}; data=None
    if token: h["Authorization"]=f"Bearer {token}"
    if payload is not None:
        h["Content-Type"]="application/json"; data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read().decode(); return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw=e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {raw[:4000]}") from e

def v2(n):
    k=0
    while n%2==0: k+=1; n//=2
    return k
def step(n):
    x=3*n+1; a=v2(x); return x>>a,a
def cert(rep,K):
    x=rep; s=0
    for t in range(1,128):
        x,a=step(x); s+=a
        if s+1>K: return None
        if 3**t<2**s and x<rep: return (t,s)
    return None
def old_residual(r):
    return (r%128 in {39,71,103}
      and r%256 not in {39,199}
      and r%1024 not in {423,583,999}
      and r%4096 not in {231,615,935,1703,3143,3559,3911}
      and r%8192 not in S13 and r%32768 not in S15 and r%65536 not in S16)

def compute():
    frontier=[r for r in range(1<<16) if old_residual(r)]
    batches={}; remaining={}
    for K in range(17,26):
        frontier=[y for x in frontier for y in (x,x+(1<<(K-1)))]
        by={}; rest=[]
        for r in frontier:
            c=cert(r,K)
            if c is None: rest.append(r)
            else: by.setdefault(c,[]).append(r)
        for vals in by.values(): vals.sort()
        batches[K]=by; remaining[K]=sorted(rest); frontier=rest
    assert len(remaining[24])==66646
    assert {k:len(v) for k,v in batches[25].items()}=={(11,24):194,(12,24):525,(13,24):1570,(14,24):3387,(15,24):9690}
    assert len(remaining[25])==117926
    return batches,remaining

def chunks(vals,n=CHUNK):
    if not vals: return []
    count=(len(vals)+n-1)//n
    # balanced chunks, each <= n
    q,r=divmod(len(vals),count); out=[]; i=0
    for j in range(count):
        m=q+(1 if j<r else 0)
        out.append(vals[i:i+m]); i+=m
    return out

def finset(vals,width=100):
    lines=[]; cur="  "
    for v in vals:
        tok=str(v)+", "
        if len(cur)+len(tok)>width and cur.strip():
            lines.append(cur.rstrip()); cur="  "+tok
        else: cur+=tok
    if cur.strip(): lines.append(cur.rstrip(", "))
    return "{\n"+"\n".join(lines)+"\n}"

def job_history(token):
    found={}
    offset=0
    for _ in range(10):
        page=api("GET","/publish-jobs?"+urllib.parse.urlencode({"limit":"100","offset":str(offset)}),token)
        items=page if isinstance(page,list) else page.get("jobs",page.get("publish_jobs",[]))
        if not items: break
        for j in items:
            name=j.get("theorem_name") or j.get("definition_name") or j.get("name")
            if name and j.get("status")=="PUBLISHED" and name not in found:
                found[name]=j
        if len(items)<100: break
        offset+=len(items)
    return found

def poll_many(token,pending):
    pending=dict(pending); done={}
    for _ in range(360):
        if not pending: return done
        time.sleep(5)
        for jid,name in list(pending.items()):
            st=api("GET",f"/publish-jobs/{jid}",token)
            status=st.get("status")
            print("publish",json.dumps({"name":name,"status":status,"error":st.get("error_message"),"id":st.get("theorem_id")}))
            if status=="PUBLISHED":
                done[name]=st; del pending[jid]
            elif status in {"FAILED","ERROR"}:
                raise RuntimeError("publication failed: "+json.dumps(st))
    raise RuntimeError("publication polling timed out: "+repr(pending))

def queue_definitions(token,env,specs,history):
    ids={}; pending={}
    for s in specs:
        name=s["name"]
        if name in history:
            ids[name]=history[name].get("theorem_id"); continue
        resp=api("POST","/submit-definition",token,payload={
          "definition_name":name,"definition_title":s["title"],"definition":s["code"],
          "natural_language_statement":s["natural"],"source":s["source"],
          "tags":["number-theory","collatz","syracuse","2-adic","certificate-set"],"env":env})
        jid=resp.get("job_id")
        if not jid: raise RuntimeError("definition queue failure: "+json.dumps(resp))
        pending[jid]=name
    for name,st in poll_many(token,pending).items(): ids[name]=st.get("theorem_id")
    return ids

def queue_problems(token,env,specs,history):
    ids={}; new=[]
    for s in specs:
        if s["name"] in history: ids[s["name"]]=history[s["name"]].get("theorem_id")
        else:
            new.append({
              "theorem_name":s["name"],"theorem_title":s["title"],"formal_statement":s["formal"],
              "natural_language_statement":s["natural"],"preamble":s["preamble"],"source":s["source"],
              "tags":["number-theory","collatz","syracuse","stopping-time","finite-certificate"]})
    pending={}
    if new:
        resp=api("POST","/submit-problem",token,payload={"problems":new,"env":env})
        if resp.get("errors"): raise RuntimeError("problem queue errors: "+json.dumps(resp))
        for j in resp.get("jobs",[]): pending[j["job_id"]]=j["name"]
        if len(pending)!=len(new): raise RuntimeError("problem job count mismatch: "+json.dumps(resp))
    for name,st in poll_many(token,pending).items(): ids[name]=st.get("theorem_id")
    return ids

def add_hypotheses(formal,new_hyps,new_name):
    s=re.sub(r"^theorem\s+\S+","theorem "+new_name,formal.strip(),count=1)
    if not s.endswith(":= by sorry"): raise RuntimeError("unexpected theorem suffix")
    s=s[:-len(":= by sorry")].rstrip()
    idx=s.rfind(") :\n")
    if idx<0: raise RuntimeError("conclusion boundary not found")
    return s[:idx+1]+"\n"+"\n".join("    "+h for h in new_hyps)+s[idx+1:]+" := by sorry"

def ensure_problem(token,env,name,title,formal,natural,preamble,source,history,tags):
    if name in history: return history[name].get("theorem_id")
    resp=api("POST","/submit-problem",token,payload={"theorem_name":name,"theorem_title":title,
      "formal_statement":formal,"natural_language_statement":natural,"preamble":preamble,
      "source":source,"tags":tags,"env":env})
    jobs=resp.get("jobs",[])
    if not jobs: raise RuntimeError("problem did not queue: "+json.dumps(resp))
    done=poll_many(token,{jobs[0]["job_id"]:name})
    return done[name].get("theorem_id")

def verify(token,theorem_id,content,explanation):
    b="----p2m"+uuid.uuid4().hex; parts=[]
    for n,v in [("theorem_id",theorem_id),("proof_type","prove"),("explanation",explanation)]:
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="solution.lean"\r\nContent-Type: text/plain\r\n\r\n'.encode()+content.encode()+b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={"Authorization":f"Bearer {token}","Accept":"application/json","Content-Type":f"multipart/form-data; boundary={b}"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:return json.loads(r.read().decode())

def wait_verify(token,sid):
    for _ in range(240):
        time.sleep(5); st=api("GET",f"/verify?submission_id={sid}",token)
        print("verify",json.dumps({"status":st.get("status"),"error":st.get("error_message")}))
        if st.get("status") in TERMINAL:return st
    raise RuntimeError("verification timeout")

def solution(parent_formal,imports,case_specs,residual_name,parent_args,new_hnames,modulus):
    s=re.sub(r"^theorem\s+\S+","theorem solution",parent_formal.strip(),count=1)
    if not s.endswith(":= by sorry"): raise RuntimeError("bad parent formal")
    s=s[:-len(":= by sorry")].rstrip()
    def build(i,ind):
        if i==len(case_specs):
            return [ind+"exact "+residual_name+" "+" ".join(parent_args+new_hnames)]
        t,dname,cname,hname=case_specs[i]
        return [ind+f"by_cases {hname} : n % {modulus} ∈ {dname}",
                ind+f"· exact ⟨{t}, {cname} n {hname}⟩",
                ind+"·"]+build(i+1,ind+"  ")
    proof="\n".join(build(0,"  "))
    return "\n".join(imports)+"\n\nset_option autoImplicit false\nset_option maxRecDepth 200000\n\n"+s+" := by\n"+proof+"\n"

def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    ref=api("POST","/agent/refresh",payload={"api_key":key}); token=ref["access_token"]
    parent=api("GET",f"/theorems/{PARENT24_ID}",token); env=parent["mathlib_rev"]
    assert parent.get("theorem_name")=="syracuse_descent_residual_seven_mod32_mod16777216"
    batches,remaining=compute(); history=job_history(token)

    stages={25:[(11,24),(12,24),(13,24),(14,24),(15,24)]}
    stage_specs={}
    def_specs=[]; problem_specs=[]
    for K,shapes in stages.items():
        modulus=1<<K; cases=[]
        for t,S in shapes:
            family=batches[K][(t,S)]
            parts=chunks(family)
            for idx,vals in enumerate(parts,1):
                suffix=f"Chunk{idx:02d}"
                dname=f"syracuseSevenMod32New{K}Step{t}{suffix}Classes"
                cname=f"syracuse_descent_new{K}_step{t}_chunk{idx:02d}_seven_mod32"
                code="import Mathlib.Data.Finset.Insert\n\nset_option maxRecDepth 200000\n\ndef "+dname+" : Finset ℕ := "+finset(vals)
                def_specs.append({"name":dname,"title":f"New Syracuse $2^{{{K}}}$ step-{t} certificate classes, chunk {idx}",
                    "code":code,
                    "natural":f"Chunk {idx} of {len(parts)} of the newly certifiable residue classes modulo $2^{{{K}}}={modulus}$ with accelerated Syracuse descent time $t={t}$ and total stripped exponent $S={S}$. This chunk contains {len(vals)} exact residue representatives and is kept moderate in size for reusable Lean compilation.",
                    "source":f"Exact refinement of the seven-mod-32 Syracuse residual tree at modulus 2^{K}, using Terras uniformity."})
                pre=("import Definitions.Def_syracuseStep\n"+f"import Definitions.Def_{dname}\n"+
                     "import Mathlib.Logic.Function.Iterate\nset_option autoImplicit false\nset_option maxRecDepth 200000")
                formal=f"theorem {cname} (n : ℕ)\n    (h : n % {modulus} ∈ {dname}) :\n    syracuseStep^[{t}] n < n := by sorry"
                problem_specs.append({"name":cname,"title":f"Syracuse step-{t} descent on chunk {idx}/{len(parts)} at $2^{{{K}}}$",
                    "formal":formal,
                    "natural":f"For any natural number whose residue modulo $2^{{{K}}}$ belongs to the named {len(vals)}-element chunk, the accelerated Syracuse iterate $T^{{{t}}}(n)$ is strictly smaller than $n$. Every representative in this chunk has total stripped exponent $S={S}$, with $S+1\\le {K}$ and $3^{{{t}}}<2^{{{S}}}$, so the fixed representative certificate transfers to the full residue class.",
                    "preamble":pre,
                    "source":"Computational certificate child of the Prove2Me Collatz residual tree; uniformity theorem https://prove2.me/theorems/cd79de19-4613-42b0-afc9-48de75023e4a."})
                cases.append((t,S,dname,cname,len(vals),idx))
        stage_specs[K]=cases

    def_ids=queue_definitions(token,env,def_specs,history)
    history.update({n:{"theorem_id":i,"status":"PUBLISHED"} for n,i in def_ids.items()})
    problem_ids=queue_problems(token,env,problem_specs,history)
    history.update({n:{"theorem_id":i,"status":"PUBLISHED"} for n,i in problem_ids.items()})

    report={"platform_version":ref.get("version"),"definitions":def_ids,"finite_children":problem_ids,"stages":{},"sketches":{}}
    parent_id=PARENT24_ID
    parent_prefix=parent["formal_statement"].split(":= by sorry",1)[0]
    parent_args=re.findall(r"\(([A-Za-z0-9_]+)\s*:",parent_prefix)
    inherited_defs=[]
    for d in re.findall(r"(syracuseSevenMod32New[A-Za-z0-9_]+Classes)",parent["formal_statement"]):
        if d not in inherited_defs:
            inherited_defs.append(d)

    for K in (25,):
        modulus=1<<K; cases=stage_specs[K]
        current_defs=[x[2] for x in cases]
        new_hyps=[]; case_specs=[]; hnames=[]
        for t,S,dname,cname,count,idx in cases:
            hname=f"h{K}_{t}_{idx:02d}"
            new_hyps.append(f"({hname} : n % {modulus} ∉ {dname})")
            hcase=f"hcase_{K}_{t}_{idx:02d}"
            case_specs.append((t,dname,cname,hcase)); hnames.append(hcase)

        residual_name=f"syracuse_descent_residual_seven_mod32_mod{modulus}"
        formal=add_hypotheses(parent["formal_statement"],new_hyps,residual_name)
        preamble="\n".join(
          ["import Definitions.Def_syracuseStep","import Mathlib.Logic.Function.Iterate"]+
          [f"import Definitions.Def_{d}" for d in inherited_defs+current_defs]+
          ["set_option autoImplicit false","set_option maxRecDepth 200000"])
        removed=sum(x[4] for x in cases); denom=len(remaining[K-1])*2
        rid=ensure_problem(token,env,residual_name,
          f"Residual Syracuse descent modulo $2^{{{K}}}$ after chunked certificate removal",
          formal,
          f"Refine the hard residual from modulus $2^{{{K-1}}}$ to $2^{{{K}}}={modulus}$ and remove {removed} newly certified classes, represented by {len(cases)} moderate reusable certificate chunks. The unresolved complement contains {len(remaining[K])} of the {denom} lifted parent classes, removing {removed/denom:.2%} of this stage's residual density.",
          preamble,
          f"Recursive exact refinement of Prove2Me residual theorem {parent_id}; finite children are Terras-style uniform descent certificates.",
          history,
          ["number-theory","collatz","syracuse","stopping-time","residual"])
        history[residual_name]={"theorem_id":rid,"status":"PUBLISHED"}

        imports=[f"import Theorems.Thm_{x[3]}" for x in cases]+[f"import Theorems.Thm_{residual_name}"]
        imports += [f"import Definitions.Def_{d}" for d in inherited_defs+current_defs]
        imports += ["import Definitions.Def_syracuseStep","import Mathlib.Logic.Function.Iterate"]
        sol=solution(parent["formal_statement"],imports,case_specs,residual_name,parent_args,hnames,modulus)
        expl=(f"Partition the parent residual at modulus $2^{{{K}}}$ into {len(cases)} explicit finite certificate chunks and their complement. "
              f"Membership in a chunk gives a fixed-time descent via the corresponding child theorem. If no membership holds, all exclusion hypotheses of "
              f"`{residual_name}` hold, so the residual child supplies eventual descent. This removes {removed} of {denom} lifted parent classes.")
        sub=verify(token,parent_id,sol,expl); verdict=wait_verify(token,sub["submission_id"])
        report["sketches"][parent.get("theorem_name")]=verdict
        if verdict.get("status") not in {"SKETCH_ACCEPTED","ACCEPTED"}:
            OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
            raise RuntimeError("sketch failed: "+json.dumps(verdict))
        report["stages"][str(K)]={"residual_id":rid,"residual_name":residual_name,"remaining":len(remaining[K]),"removed":removed,"chunks":len(cases)}
        parent=api("GET",f"/theorems/{rid}",token); parent_id=rid
        parent_args += [f"h{K}_{x[0]}_{x[5]:02d}" for x in cases]
        inherited_defs += current_defs

    report["final"]={"residual_id":parent_id,"name":parent.get("theorem_name"),"remaining_mod_2_25":len(remaining[25]),
      "fraction_parent24_removed":1-len(remaining[25])/(len(remaining[24])*2)}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report["final"],indent=2))

if __name__=="__main__": main()
