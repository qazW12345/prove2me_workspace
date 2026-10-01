#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from collections import Counter
from pathlib import Path

BASE = "https://prove2.me/api/v1"
PARENT20_ID = "8d2d08ed-fda7-4e9b-b521-cfa49347ded2"
OUT = Path("agent-state/collatz-residual-recursive-decompose.json")
TERMINAL = {"ACCEPTED","SKETCH_ACCEPTED","CE","WA","SORRY","FAILED","ERROR"}

S13 = {679,1191,2663,3687,4199,4455,5191,5607,5959,6215,6375,6631,6983,7079,7399,7495,7847,7911,8103}
S15 = {839,1095,2119,2279,2727,2983,3303,4007,6503,6759,7783,9959,10055,11079,11943,12967,14439,16743,16871,17735,17767,19623,20199,21223,23399,24647,24679,25703,25831,26087,26535,27111,27975,28999,29863,30311,30887}
S16 = {359,1351,2407,2791,2887,3239,3815,4775,5863,6247,7015,8263,8551,9319,9543,10151,10727,11431,12007,12615,12775,13671,13927,14503,15207,16455,17127,17223,17479,17511,18343,18919,19111,19367,19687,20807,21735,22119,22695,22887,23143,25415,25671,26343,26439,27303,27559,27879,28327,31079,31335,33255,34151,34535,34631,36519,37607,37735,40039,41063,41447,42215,42343,42471,43111,43335,44359,45223,45799,46247,46407,48295,49255,50407,50663,51271,51431,52071,52551,53159,53319,54375,54439,55207,56935,57671,58983,59463,59559,59623,60231,61351,62119,62279,63335,63591,64167,64871,65127}

EXPECTED_C19_SHA = "3aae89c2132def3afa3c5c0bc69a5b338412850d3c38f171cd0dbe48ff62bd71"
EXPECTED_C20_SHA = "e40282d8355fab0d83578df1c8ce5a2e76f292d0f48def05282f879b02791139"


def api(method: str, path: str, *, token: str | None = None, payload=None):
    headers = {"Accept":"application/json","User-Agent":"prove2me-collatz-recursive-decompose/1"}
    body = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if payload is not None:
        headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode()
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {e.code}: {raw[:5000]}") from e


def q(x): return urllib.parse.quote(str(x), safe="")


def v2(n: int) -> int:
    k = 0
    while n % 2 == 0:
        k += 1
        n //= 2
    return k


def step(n: int):
    x = 3*n + 1
    a = v2(x)
    return x >> a, a


def certificate(rep: int, K: int):
    x = rep
    total = 0
    exps = []
    for t in range(1, 128):
        x, a = step(x)
        total += a
        exps.append(a)
        if total + 1 > K:
            return None
        if 3**t < 2**total and x < rep:
            return (t, total, x, tuple(exps))
    return None


def old_residual(r: int) -> bool:
    return (
        r % 128 in {39,71,103}
        and r % 256 not in {39,199}
        and r % 1024 not in {423,583,999}
        and r % 4096 not in {231,615,935,1703,3143,3559,3911}
        and r % 8192 not in S13
        and r % 32768 not in S15
        and r % 65536 not in S16
    )


def sha(values):
    import hashlib
    return hashlib.sha256(",".join(map(str, values)).encode()).hexdigest()


def compute():
    frontier = [r for r in range(1<<16) if old_residual(r)]
    assert len(frontier) == 395
    batches = {}
    remaining = {}
    for K in range(17, 23):
        prev = 16 if K == 17 else K-1
        frontier = [y for x in frontier for y in (x, x + (1<<prev))]
        by_shape = {}
        rest = []
        for r in frontier:
            c = certificate(r, K)
            if c is None:
                rest.append(r)
            else:
                by_shape.setdefault((c[0],c[1]), []).append(r)
        for vals in by_shape.values():
            vals.sort()
        batches[K] = by_shape
        remaining[K] = sorted(rest)
        frontier = rest

    c19 = batches[19][(11,18)]
    c20 = batches[20][(11,19)]
    assert sha(c19) == EXPECTED_C19_SHA
    assert sha(c20) == EXPECTED_C20_SHA
    assert {k:len(v) for k,v in batches[21].items()} == {(11,20):194,(12,20):525}
    assert {k:len(v) for k,v in batches[22].items()} == {(11,21):194,(12,21):525,(13,21):1570}
    assert len(remaining[20]) == 5738
    assert len(remaining[21]) == 10757
    assert len(remaining[22]) == 19225
    return batches, remaining


def finset_literal(vals, width=100):
    lines, cur = [], "  "
    for v in vals:
        tok = str(v) + ", "
        if len(cur) + len(tok) > width and cur.strip():
            lines.append(cur.rstrip())
            cur = "  " + tok
        else:
            cur += tok
    if cur.strip():
        lines.append(cur.rstrip(", "))
    return "{\n" + "\n".join(lines) + "\n}"


def find_exact(token, name, status=None):
    params = {"q":name,"limit":"100","offset":"0"}
    if status: params["status"] = status
    path = "/theorems?"+urllib.parse.urlencode(params)
    last = None
    for attempt in range(10):
        try:
            page = api("GET",path,token=token)
            for item in page.get("theorems",[]):
                if item.get("theorem_name") == name or item.get("definition_name") == name:
                    return item
            return None
        except RuntimeError as exc:
            last = exc
            msg = str(exc)
            if "HTTP 500" not in msg and "HTTP 502" not in msg and "HTTP 503" not in msg and "HTTP 504" not in msg:
                raise
            print("catalog-search-retry", json.dumps({"name":name,"attempt":attempt+1,"error":msg[:500]}))
            time.sleep(min(5 + 3*attempt, 30))
    raise last


def poll_job(token, jid):
    for _ in range(180):
        time.sleep(5)
        st = api("GET",f"/publish-jobs/{jid}",token=token)
        print("publish-status", json.dumps({"name":st.get("theorem_name") or st.get("definition_name"),"status":st.get("status"),"error":st.get("error_message"),"id":st.get("theorem_id")}))
        if st.get("status") in {"PUBLISHED","FAILED","ERROR"}:
            return st
    raise RuntimeError("publish job timed out: "+jid)


def ensure_definition(token, env, name, title, vals, modulus, t, S):
    existing = find_exact(token,name,status="Definition")
    if existing:
        return existing.get("theorem_id") or existing.get("id")
    code = (
        "import Mathlib.Data.Finset.Insert\n\n"
        "set_option maxRecDepth 200000\n\n"
        f"def {name} : Finset ℕ := {finset_literal(vals)}"
    )
    resp = api("POST","/submit-definition",token=token,payload={
        "definition_name":name,
        "definition_title":title,
        "definition":code,
        "natural_language_statement":(
            f"The finite set of {len(vals)} residue representatives modulo $2^{{{modulus.bit_length()-1}}}={modulus}$ "
            f"that first become uniformly certifiable at this refinement stage with accelerated Syracuse descent time "
            f"$t={t}$ and total stripped exponent $S={S}$. The set is computed exactly from the residual branch descending "
            f"from `syracuse_descent_residual_seven_mod32_mod1048576`."
        ),
        "source":"Computational residue refinement of https://prove2.me/theorems/8d2d08ed-fda7-4e9b-b521-cfa49347ded2 using https://prove2.me/theorems/cd79de19-4613-42b0-afc9-48de75023e4a (Terras uniformity).",
        "tags":["number-theory","collatz","syracuse","2-adic","certificate-set"],
        "env":env,
    })
    jid = resp.get("job_id")
    if not jid:
        raise RuntimeError("definition did not queue: "+json.dumps(resp))
    st = poll_job(token,jid)
    if st.get("status") != "PUBLISHED":
        raise RuntimeError("definition publish failed: "+json.dumps(st))
    return st.get("theorem_id")


def ensure_problem(token, env, name, title, formal, natural, preamble, source, tags):
    existing = find_exact(token,name)
    if existing:
        actual = (existing.get("formal_statement") or "").strip()
        if actual and actual != formal.strip():
            raise RuntimeError(f"existing theorem {name} has different formal statement")
        return existing.get("theorem_id") or existing.get("id")
    resp = api("POST","/submit-problem",token=token,payload={
        "theorem_name":name,
        "theorem_title":title,
        "formal_statement":formal,
        "natural_language_statement":natural,
        "preamble":preamble,
        "source":source,
        "tags":tags,
        "env":env,
    })
    jobs = resp.get("jobs",[])
    if not jobs:
        raise RuntimeError("problem did not queue: "+json.dumps(resp))
    st = poll_job(token,jobs[0]["job_id"])
    if st.get("status") != "PUBLISHED":
        raise RuntimeError("problem publish failed: "+json.dumps(st))
    return st.get("theorem_id")


def add_hypotheses(formal, new_hyps, new_name):
    s = formal.strip()
    s = re.sub(r"^theorem\s+\S+", "theorem "+new_name, s, count=1)
    if not s.endswith(":= by sorry"):
        raise RuntimeError("unexpected formal statement suffix")
    s = s[:-len(":= by sorry")].rstrip()
    marker = ") :\n"
    idx = s.rfind(marker)
    if idx < 0:
        marker = ") : "
        idx = s.rfind(marker)
    if idx < 0:
        raise RuntimeError("could not find conclusion boundary")
    insert = "\n" + "\n".join("    "+h for h in new_hyps)
    return s[:idx+1] + insert + s[idx+1:] + " := by sorry"


def solution_from_parent(parent_formal, imports, proof):
    s = parent_formal.strip()
    s = re.sub(r"^theorem\s+\S+", "theorem solution", s, count=1)
    if not s.endswith(":= by sorry"):
        raise RuntimeError("unexpected parent suffix")
    s = s[:-len(":= by sorry")].rstrip()
    return "\n".join(imports) + "\n\nset_option autoImplicit false\nset_option maxRecDepth 200000\n\n" + s + " := by\n" + proof + "\n"


def verify(token, theorem_id, content, explanation):
    b = "----p2m"+uuid.uuid4().hex
    parts=[]
    for n,v in [("theorem_id",theorem_id),("proof_type","prove"),("explanation",explanation)]:
        parts.append(f'--{b}\r\nContent-Disposition: form-data; name="{n}"\r\n\r\n{v}\r\n'.encode())
    parts.append(f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="solution.lean"\r\nContent-Type: text/plain\r\n\r\n'.encode()+content.encode()+b"\r\n")
    parts.append(f"--{b}--\r\n".encode())
    req=urllib.request.Request(BASE+"/verify",data=b"".join(parts),headers={"Authorization":f"Bearer {token}","Accept":"application/json","Content-Type":f"multipart/form-data; boundary={b}"},method="POST")
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode())


def wait_verdict(token,sid):
    for _ in range(180):
        time.sleep(5)
        st=api("GET",f"/verify?submission_id={sid}",token=token)
        print("verify-status",json.dumps({"id":sid,"status":st.get("status"),"error":st.get("error_message")}))
        if st.get("status") in TERMINAL:
            return st
    raise RuntimeError("verification timed out")


def main():
    key=os.environ["PROVE2ME_API_KEY"].strip()
    refreshed=api("POST","/agent/refresh",payload={"api_key":key})
    token=refreshed["access_token"]
    parent20=api("GET",f"/theorems/{PARENT20_ID}",token=token)
    assert parent20.get("theorem_name")=="syracuse_descent_residual_seven_mod32_mod1048576"
    env=parent20["mathlib_rev"]

    batches, remaining = compute()
    report={"platform_version":refreshed.get("version"),"parent20":PARENT20_ID,"definitions":{},"children":{},"sketches":{}}

    stages = [
      (21,2097152,[(11,20),(12,20)]),
      (22,4194304,[(11,21),(12,21),(13,21)]),
    ]

    parent = parent20
    parent_id = PARENT20_ID
    parent_arg_names = ["n","h","h256","h1024","h4096","h8192","h32768","h65536","h524288","h1048576"]

    for K, modulus, shapes in stages:
        defs=[]
        children=[]
        for t,S in shapes:
            vals=batches[K][(t,S)]
            dname=f"syracuseSevenMod32New{K}Step{t}Classes"
            did=ensure_definition(
                token,env,dname,
                f"New Syracuse residual classes at $2^{{{K}}}$ with descent time {t}",
                vals,modulus,t,S)
            report["definitions"][dname]={"id":did,"count":len(vals),"t":t,"S":S}
            defs.append((t,S,dname,vals))

            cname=f"syracuse_descent_new{K}_step{t}_seven_mod32"
            preamble=(
                "import Definitions.Def_syracuseStep\n"
                f"import Definitions.Def_{dname}\n"
                "import Mathlib.Logic.Function.Iterate\n"
                "set_option autoImplicit false\n"
                "set_option maxRecDepth 200000"
            )
            formal=(
                f"theorem {cname} (n : ℕ)\n"
                f"    (h : n % {modulus} ∈ {dname}) :\n"
                f"    syracuseStep^[{t}] n < n := by sorry"
            )
            natural=(
                f"Let $T$ be the accelerated Syracuse map. If $n$ belongs modulo $2^{{{K}}}$ to the named "
                f"{len(vals)}-class certificate set, then the fixed iterate $T^{{{t}}}(n)$ is strictly smaller than $n$. "
                f"Every canonical representative in this set has total stripped exponent $S={S}$; the exact computation "
                f"satisfies $S+1\\le {K}$ and $3^{{{t}}}<2^{{{S}}}$, so Terras uniformity transfers the representative "
                f"descent to its complete residue class. This is a finite certificate leaf split from the hard residual branch."
            )
            cid=ensure_problem(token,env,cname,
                f"Syracuse descent at step {t} on {len(vals)} new classes modulo $2^{{{K}}}$",
                formal,natural,preamble,
                f"Derived from {parent_id} by exact residue refinement; Terras uniformity: https://prove2.me/theorems/cd79de19-4613-42b0-afc9-48de75023e4a.",
                ["number-theory","collatz","syracuse","stopping-time","finite-certificate"])
            report["children"][cname]={"id":cid,"count":len(vals),"t":t,"S":S}
            children.append((t,dname,cname,cid))

        residual_name=f"syracuse_descent_residual_seven_mod32_mod{modulus}"
        new_hyps=[f"(h{K}_{t} : n % {modulus} ∉ {dname})" for t,S,dname,vals in defs]
        residual_formal=add_hypotheses(parent["formal_statement"],new_hyps,residual_name)
        residual_preamble="\n".join(
            ["import Definitions.Def_syracuseStep","import Mathlib.Logic.Function.Iterate"]+
            [f"import Definitions.Def_{dname}" for _,_,dname,_ in defs]+
            ["set_option autoImplicit false","set_option maxRecDepth 200000"]
        )
        density_parent=len(remaining[K-1])*2
        removed=sum(len(v) for v in batches[K].values())
        residual_natural=(
            f"Continue the hard Syracuse residual branch one binary refinement deeper, from modulus $2^{{{K-1}}}$ "
            f"to $2^{{{K}}}={modulus}$. Exclude the {removed} newly certified classes, grouped into fixed-descent-time "
            f"certificate sets, and assert that every remaining input still eventually descends. There are "
            f"{len(remaining[K])} unresolved classes out of {density_parent} lifts of the preceding residual, so this "
            f"step removes {removed/density_parent:.2%} of that residual density while preserving the genuinely hard complement."
        )
        rid=ensure_problem(token,env,residual_name,
            f"Residual Syracuse descent modulo $2^{{{K}}}$ after the new finite certificate batches",
            residual_formal,residual_natural,residual_preamble,
            f"Recursive residual refinement of {parent_id}; complementary to the finite Terras-certificate children published at modulus 2^{K}.",
            ["number-theory","collatz","syracuse","stopping-time","residual"])
        report["children"][residual_name]={"id":rid,"remaining":len(remaining[K]),"modulus":modulus}

        imports=[f"import Theorems.Thm_{cname}" for _,_,cname,_ in children]
        imports.append(f"import Theorems.Thm_{residual_name}")
        imports += [f"import Definitions.Def_{dname}" for _,_,dname,_ in defs]
        imports += ["import Definitions.Def_syracuseStep","import Mathlib.Logic.Function.Iterate"]
        proof_lines=[]
        indent="  "
        new_arg_names=[]
        for idx,(t,dname,cname,cid) in enumerate(children):
            hname=f"hcase_{K}_{t}"
            proof_lines.append(indent+f"by_cases {hname} : n % {modulus} ∈ {dname}")
            proof_lines.append(indent+f"· exact ⟨{t}, {cname} n {hname}⟩")
            proof_lines.append(indent+"· ")
            indent += "  "
            new_arg_names.append(hname)
        # repair nested final bullet formatting: replace trailing placeholder with exact on same level
        # Build recursively instead for clean Lean syntax.
        def nested(i, ind):
            if i==len(children):
                args=" ".join(parent_arg_names+new_arg_names)
                return [ind+f"exact {residual_name} {args}"]
            t,dname,cname,cid=children[i]
            hname=f"hcase_{K}_{t}"
            lines=[ind+f"by_cases {hname} : n % {modulus} ∈ {dname}",
                   ind+f"· exact ⟨{t}, {cname} n {hname}⟩",
                   ind+"· "+nested(i+1,ind+"  ")[0].lstrip()]
            tail=nested(i+1,ind+"  ")[1:]
            lines.extend(tail)
            return lines
        # simpler explicit nesting generator
        def build(i, ind):
            if i == len(children):
                args=" ".join(parent_arg_names+[f"hcase_{K}_{x[0]}" for x in children])
                return [ind+f"exact {residual_name} {args}"]
            t,dname,cname,cid=children[i]
            hname=f"hcase_{K}_{t}"
            lines=[ind+f"by_cases {hname} : n % {modulus} ∈ {dname}",
                   ind+f"· exact ⟨{t}, {cname} n {hname}⟩",
                   ind+"·"]
            lines += build(i+1, ind+"  ")
            return lines
        proof="\n".join(build(0,"  "))
        sol=solution_from_parent(parent["formal_statement"],imports,proof)
        expl=(
            f"Partition the parent residual at modulus $2^{{{K}}}$ by the newly discovered finite certificate sets. "
            f"Each membership case is discharged by its fixed-time child theorem. If none of those memberships holds, "
            f"the hypotheses are exactly those of `{residual_name}`, which is the remaining hard complement. "
            f"The finite children remove {removed} of the {density_parent} lifted parent classes at this stage."
        )
        sub=verify(token,parent_id,sol,expl)
        verdict=wait_verdict(token,sub["submission_id"])
        report["sketches"][parent.get("theorem_name")]=verdict
        if verdict.get("status") not in {"SKETCH_ACCEPTED","ACCEPTED"}:
            OUT.parent.mkdir(parents=True,exist_ok=True)
            OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
            raise RuntimeError("parent sketch failed: "+json.dumps(verdict))

        parent=api("GET",f"/theorems/{rid}",token=token)
        parent_id=rid
        parent_arg_names += [f"h{K}_{t}" for t,S in shapes]

    report["final_residual"]={
        "id":parent_id,
        "name":parent.get("theorem_name"),
        "remaining_mod_2_22":len(remaining[22]),
        "current_residual20_lifts_mod_2_22":len(remaining[20])*4,
        "fraction_current_residual_removed":1-len(remaining[22])/(len(remaining[20])*4),
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps(report["final_residual"],indent=2))


if __name__=="__main__":
    main()
