#!/usr/bin/env python3
"""Compile, stage, and validate fitting 003F initializer candidates at final VMAs."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, random, struct, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.h2_calc_code_patch import encode_ips, apply_ips
from tools import h18_003f3274_experiment as f3274
from tools import h18_003f32f4_family as f32f4
from tools import h18_003f3454_family as f3454

IMAGE_BASE=0x00100000
SPAN=(0x003F31D8,0x003F34F8)
ORIGINAL_SHA="1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SLOTS=[(0x003F3274,0x80,"003f3274"),
       *((e["address"],f32f4.EXTENT,f32f4.ENTRIES[i]["name"]) for i,e in enumerate(f32f4.ENTRIES)),
       (0x003F34A0,0x2C,"003f34a0"),(0x003F34CC,0x2C,"003f34cc")]
EXPECTED_ADDRS={x[0] for x in SLOTS}

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()

def stage_candidates(original:bytes,candidates:dict[int,bytes])->tuple[bytes,bytes,list[dict]]:
    if set(candidates)!=EXPECTED_ADDRS: raise ValueError("candidate set must contain exactly the 11 fitting entries")
    staged=bytearray(original); records=[]; metadata=[]
    previous_end=-1
    for address,extent,name in SLOTS:
        body=candidates[address]
        if not body or len(body)%4: raise ValueError(f"{name}: candidate must be nonempty ARM words")
        if len(body)>extent: raise ValueError(f"{name}: {len(body)} bytes exceed {extent}-byte slot")
        offset=address-IMAGE_BASE; end=offset+len(body)
        if offset<previous_end: raise ValueError("candidate slots overlap")
        if offset<0 or end>len(original): raise ValueError(f"{name}: slot is outside image")
        staged[offset:end]=body; records.append((offset,body)); previous_end=offset+extent
        metadata.append({"name":name,"address":hex(address),"slot_bytes":extent,"candidate_bytes":len(body),"candidate_sha256":sha(body),"bit0":address&1,"arm_word_aligned":address%4==0})
    patch=encode_ips(records,len(original)); replay=apply_ips(original,patch)
    if replay!=bytes(staged): raise AssertionError("IPS replay does not reproduce staged image")
    return bytes(staged),patch,metadata

def validate_patch_scope(original:bytes,staged:bytes,patch:bytes,candidates:dict[int,bytes])->dict:
    if len(original)!=len(staged): raise ValueError("image size changed")
    if apply_ips(original,patch)!=staged: raise ValueError("IPS replay mismatch")
    changed=[i for i,(a,b) in enumerate(zip(original,staged)) if a!=b]
    allowed=set()
    for address,body in candidates.items():
        off=address-IMAGE_BASE; allowed.update(range(off,off+len(body)))
    if any(i not in allowed for i in changed): raise ValueError("changed byte lies outside staged candidate bodies")
    a,b=SPAN
    if staged[a-IMAGE_BASE:b-IMAGE_BASE]==original[a-IMAGE_BASE:b-IMAGE_BASE]: raise ValueError("expected selected entries to change")
    preserve=(0x003F3454,0x003F34A0)
    if staged[preserve[0]-IMAGE_BASE:preserve[1]-IMAGE_BASE]!=original[preserve[0]-IMAGE_BASE:preserve[1]-IMAGE_BASE]: raise ValueError("oversized 0x003f3454 entry changed")
    if staged[0x003F31D8-IMAGE_BASE:0x003F3274-IMAGE_BASE]!=original[0x003F31D8-IMAGE_BASE:0x003F3274-IMAGE_BASE]: raise ValueError("existing 0x003f31d8 entry changed")
    if staged[:a-IMAGE_BASE]!=original[:a-IMAGE_BASE] or staged[b-IMAGE_BASE:]!=original[b-IMAGE_BASE:]: raise ValueError("bytes outside compound span changed")
    return {"changed_bytes":len(changed),"within_candidate_bodies":True,"outside_span_unchanged":True,"entry_003f31d8_unchanged":True,"oversized_003f3454_unchanged":True,"ips_roundtrip":True}

def compile_candidates(out:Path)->tuple[dict[int,bytes],dict]:
    out.mkdir(parents=True,exist_ok=True)
    c3274,obj3274=f3274.compile_symbol(f3274.SOURCE,out/"003f3274.o")
    c32,obj32=f32f4.compile_symbols(f32f4.SOURCE,out/"003f32f4.o")
    compile_3454_dir=out/"compile-3454"; compile_3454_dir.mkdir(parents=True,exist_ok=True)
    c3454,info3454=f3454.compile_candidates(compile_3454_dir)
    candidates={0x003F3274:c3274}
    for e in f32f4.ENTRIES: candidates[e["address"]]=c32[e["name"]]
    candidates[0x003F34A0]=c3454[0x003F34A0]
    candidates[0x003F34CC]=c3454[0x003F34CC]
    info={"3274_object_sha256":obj3274,"32f4_object_sha256":obj32,"3454_compile":info3454,
          "relocations":"all three compile helpers reject any candidate relocation before returning"}
    return candidates,info

def run_validation(output:Path,seed:int=7,samples:int=20)->dict:
    if output.exists(): raise FileExistsError(f"fresh output directory required: {output}")
    output.mkdir(parents=True)
    original=f3274.CODE_BIN.read_bytes()
    if sha(original)!=ORIGINAL_SHA: raise ValueError("pinned original code.bin hash mismatch")
    game=json.loads(f3274.GAME_INFO.read_text(encoding="utf-8"))
    if game.get("code_sha256")!=ORIGINAL_SHA: raise ValueError("game_info reference hash mismatch")
    candidates,compile_info=compile_candidates(output/"compiled")
    staged,patch,placements=stage_candidates(original,candidates)
    scope=validate_patch_scope(original,staged,patch,candidates)
    (output/"staged_code.bin").write_bytes(staged); (output/"candidate.ips").write_bytes(patch)
    # Exercise the bytes extracted from the final staged image at each final VMA.
    functional={}; controls={}
    final3274=staged[0x003F3274-IMAGE_BASE:0x003F3274-IMAGE_BASE+len(candidates[0x003F3274])]
    original3274=f3274.original_function(original)
    rows,mismatch=f3274.run_pair(original3274,final3274,seed,samples)
    if mismatch: raise AssertionError(f"0x003f3274 staged differential mismatch: {mismatch}")
    controls3274_dir=output/"controls-3274"; controls3274_dir.mkdir(parents=True,exist_ok=True)
    ctrl=f3274.compile_negative_controls(f3274.SOURCE.read_text(encoding="utf-8"),original3274,seed,samples,controls3274_dir)
    if not ctrl or not all(x["detected"] for x in ctrl): raise AssertionError("0x003f3274 negative control escaped")
    functional["0x003f3274"]={"cases":len(rows),"passed":True,"candidate_sha256":sha(final3274)}; controls["0x003f3274"]=ctrl
    rows32={}; src32=f32f4.SOURCE.read_text(encoding="utf-8")
    for entry in f32f4.ENTRIES:
        addr=entry["address"]; body=staged[addr-IMAGE_BASE:addr-IMAGE_BASE+len(candidates[addr])]
        cases,first=f32f4.compare_entry(original,entry,body,seed,samples)
        if first: raise AssertionError(f"{addr:#x} staged differential mismatch: {first}")
        rows32[hex(addr)]={"cases":len(cases),"passed":True,"candidate_sha256":sha(body)}
    controls32_dir=output/"controls-32f4"; controls32_dir.mkdir(parents=True,exist_ok=True)
    controls32=f32f4.negative_controls(original,src32,seed,samples,controls32_dir)
    if len(controls32)!=8 or not all(x["detected"] for x in controls32): raise AssertionError("32f4 family negative control escaped")
    functional["32f4_family"]=rows32; controls["32f4_family"]=controls32
    # The two final entries use the original 3454 harness, which starts from a complete image at exact guest VMAs.
    rows3454={}; fx_seed=seed ^ 0x3F34A0
    for addr in (0x003F34A0,0x003F34CC):
        entry=f3454.ENTRIES[addr]; cases=[]
        for i in range(samples):
            fx=f3454.fixture(fx_seed,i)
            old=f3454.execute(original,None,addr,fx); new=f3454.execute(staged,None,addr,fx)
            reason=f3454.compare(old,new)
            cases.append({"index":i,"passed":reason is None,"difference":reason})
        if not all(x["passed"] for x in cases): raise AssertionError(f"{addr:#x} staged image differential failed")
        rows3454[hex(addr)]={"cases":len(cases),"passed":True,"candidate_sha256":sha(staged[addr-IMAGE_BASE:addr-IMAGE_BASE+len(candidates[addr])])}
    # Mutation controls are staged at the same final VMAs, then executed directly from each mutant image.
    specs=[("34a0_wrong_sentinel","0x00472570u","0x00472574u",0x003F34A0),
           ("34cc_wrong_zero","*reinterpret_cast<u32*>(0x004727A0u) = 0;","*reinterpret_cast<u32*>(0x004727A4u) = 0;",0x003F34CC)]
    ctrl3454=[]; source3454=f3454.SOURCE.read_text(encoding="utf-8")
    for i,(name,before,after,addr) in enumerate(specs):
        if source3454.count(before)!=1: raise ValueError(f"negative control anchor not unique: {name}")
        mutant=output/"controls-3454"/f"{name}.cpp"; mutant.parent.mkdir(parents=True,exist_ok=True)
        mutant.write_text(source3454.replace(before,after,1),encoding="utf-8")
        bad,info=f3454.compile_candidates(mutant.parent,mutant,name)
        bad_image=bytearray(staged); body=bad[addr]
        if len(body)>dict((a,n) for a,n,_ in SLOTS)[addr]: raise ValueError("mutant exceeds final slot")
        off=addr-IMAGE_BASE; bad_image[off:off+len(body)]=body
        fx=f3454.fixture(fx_seed^0xABC,i)
        reference=f3454.execute(original,None,addr,fx); mutated=f3454.execute(bytes(bad_image),None,addr,fx)
        reason=f3454.compare(reference,mutated)
        if reason is None: raise AssertionError(f"negative control escaped: {name}")
        ctrl3454.append({"name":name,"detected":True,"difference":reason,"mutant_candidate_sha256":sha(body)})
    functional["34a0_34cc_family"]=rows3454; controls["34a0_34cc_family"]=ctrl3454
    # The excluded oversized entry is byte-identical, and its original tail-call/interworking still runs in the final image.
    preserved=[]
    for i in range(samples):
        fx=f3454.fixture(seed^0x3454,i)
        old=f3454.execute(original,None,0x003F3454,fx); new=f3454.execute(staged,None,0x003F3454,fx)
        reason=f3454.compare(old,new)
        if reason: raise AssertionError(f"preserved 0x003f3454 trace changed: {reason}")
        preserved.append({"index":i,"passed":True,"thumb_transition":bool(new["calls"] and new["calls"][0]["thumb_state"])})
    if not all(x["thumb_transition"] for x in preserved): raise AssertionError("preserved ARM-to-Thumb transition not observed")
    report={"schema_version":1,"task":"h18-003f-family-fit-staging","reference_sha256":sha(original),
            "staged_sha256":sha(staged),"ips_sha256":sha(patch),"source_hashes":{
              "3274":sha(f3274.SOURCE.read_bytes()),"32f4":sha(f32f4.SOURCE.read_bytes()),"3454":sha(f3454.SOURCE.read_bytes())},
            "compile":compile_info,"placements":placements,"scope":scope,"functional":functional,"negative_controls":controls,
            "preserved_003f3454":{"cases":len(preserved),"all_passed":True,"original_bytes_unchanged":True,"thumb_transition_observed":True},
            "caller":{"status":"not_run","note":"Existing static scans found no aligned direct ARM BL/exact pointer to these entries; no startup dispatcher was proven."},
            "runtime":"not_run","passed":True,"limitations":[
              "Unicorn differential only; no real caller composition or startup invocation order is established.",
              "The preserved 0x003f3454 iterator is modeled by the existing runner; its real iterator behavior is not reconstructed.",
              "No production source/ledger integration or emulator scenario was part of this staging task."]}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--output-dir",type=Path,required=True); p.add_argument("--seed",type=int,default=7); p.add_argument("--samples",type=int,default=20); a=p.parse_args(argv)
    r=run_validation(a.output_dir,a.seed,a.samples)
    print(json.dumps({"passed":r["passed"],"staged_sha256":r["staged_sha256"],"placements":len(r["placements"]),"report":str(a.output_dir/"report.json")},indent=2))
    return 0 if r["passed"] else 1
if __name__=="__main__": raise SystemExit(main())
