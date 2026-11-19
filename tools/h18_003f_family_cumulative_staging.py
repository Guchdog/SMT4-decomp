#!/usr/bin/env python3
"""Compose reviewed 003F initializer subentries onto a pinned H18 image."""
from __future__ import annotations
import argparse,hashlib,json,random,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from tools.h2_calc_code_patch import apply_ips,encode_ips
from tools import h18_003f_family_fit_staging as fit
from tools import h18_003f3274_experiment as f3274
from tools import h18_003f32f4_family as f32f4
from tools import h18_003f3454_family as f3454

IMAGE_BASE=0x00100000
ORIGINAL_SHA="1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
BASE_IMAGE=ROOT/"build/agent-work/H18-semantic/h18-integrated-stage/code.h18-final.bin"
BASE_IPS=ROOT/"build/agent-work/H18-semantic/h18-integrated-stage/code.h18-final.ips"
SLOTS=list(fit.SLOTS)
ADDRS={a for a,_,_ in SLOTS}
CAVE=(0x003FE624,0x003FF000)
PRESERVE_3454=(0x003F3454,0x003F34A0)

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()
def read_sha(p:Path)->str: return sha(p.read_bytes())

def decode_ips_records(patch:bytes)->list[tuple[int,bytes]]:
    if not patch.startswith(b"PATCH"): raise ValueError("bad IPS header")
    pos=5; records=[]
    while True:
        if pos+3>len(patch): raise ValueError("truncated IPS")
        if patch[pos:pos+3]==b"EOF":
            pos+=3
            if pos!=len(patch): raise ValueError("unexpected bytes after IPS EOF")
            return records
        if pos+5>len(patch): raise ValueError("truncated IPS record")
        off=int.from_bytes(patch[pos:pos+3],"big"); n=int.from_bytes(patch[pos+3:pos+5],"big"); pos+=5
        if n:
            if pos+n>len(patch): raise ValueError("truncated IPS payload")
            payload=patch[pos:pos+n]; pos+=n
        else:
            if pos+3>len(patch): raise ValueError("truncated IPS RLE record")
            n=int.from_bytes(patch[pos:pos+2],"big"); value=patch[pos+2]; pos+=3
            if n==0: raise ValueError("zero-length IPS RLE record")
            payload=bytes([value])*n
        records.append((off,payload))

def _overlap(a:int,n:int,b:int,m:int)->bool: return a < b+m and b < a+n

def compose_images(original:bytes,base:bytes,base_ips:bytes,candidates:dict[int,bytes],expected_base_sha:str|None=None)->dict:
    if set(candidates)!=ADDRS: raise ValueError("candidate map must have exactly the reviewed 11 addresses")
    if len(original)!=len(base): raise ValueError("base image length differs from original")
    if sha(original)!=ORIGINAL_SHA: raise ValueError("pinned original identity mismatch")
    if expected_base_sha is not None and sha(base)!=expected_base_sha: raise ValueError("H18 base image hash mismatch")
    if apply_ips(original,base_ips)!=base: raise ValueError("H18 base IPS does not reproduce H18 image")
    old_records=decode_ips_records(base_ips)
    staged=bytearray(base); overlay_records=[]; placements=[]
    allowed=[]
    for addr,extent,name in SLOTS:
        off=addr-IMAGE_BASE; old_slot=original[off:off+extent]; base_slot=base[off:off+extent]
        if len(old_slot)!=extent or base_slot!=old_slot: raise ValueError(f"base slot {name} is not byte-identical to original")
        for ro,rdata in old_records:
            if _overlap(off,extent,ro,len(rdata)): raise ValueError(f"H18 IPS record overlaps target slot {name}")
        body=candidates[addr]
        if not body or len(body)%4: raise ValueError(f"{name}: invalid ARM body size/alignment")
        if len(body)>extent: raise ValueError(f"{name}: candidate exceeds slot")
        overlay_records.append((off,body)); allowed.append((off,len(body)))
        placements.append({"name":name,"vma":hex(addr),"slot_bytes":extent,"body_bytes":len(body),"body_sha256":sha(body),"bit0":addr&1,"aligned":addr%4==0})
        staged[off:off+len(body)]=body
    final=bytes(staged)
    overlay_ips=encode_ips(overlay_records,len(base))
    if apply_ips(base,overlay_ips)!=final: raise AssertionError("overlay IPS roundtrip failed")
    combined_records=old_records+overlay_records
    combined_ips=encode_ips(combined_records,len(original))
    if apply_ips(original,combined_ips)!=final: raise AssertionError("combined original-to-final IPS roundtrip failed")
    changed=[i for i,(x,y) in enumerate(zip(base,final)) if x!=y]
    allowed_set={i for off,n in allowed for i in range(off,off+n)}
    if any(i not in allowed_set for i in changed): raise AssertionError("combined output changed preexisting bytes outside candidate bodies")
    ca,cb=CAVE; cave_off=ca-IMAGE_BASE; cave_end=cb-IMAGE_BASE
    if final[cave_off:cave_end]!=base[cave_off:cave_end]: raise AssertionError("H2 cave changed during cumulative staging")
    pa,pb=PRESERVE_3454; p0=pa-IMAGE_BASE; p1=pb-IMAGE_BASE
    if final[p0:p1]!=base[p0:p1]: raise AssertionError("oversized 0x003f3454 changed")
    return {"image":final,"overlay_ips":overlay_ips,"combined_ips":combined_ips,"placements":placements,
            "base_records":len(old_records),"combined_records":len(combined_records),"changed_bytes_from_base":len(changed),
            "cave_sha256":sha(base[cave_off:cave_end]),"cave_unchanged":True,"3454_unchanged":True,
            "all_base_ips_records_disjoint_from_target_slots":True,"ips_roundtrip":True}

def _extract(image:bytes,addr:int,n:int)->bytes: return image[addr-IMAGE_BASE:addr-IMAGE_BASE+n]

def compile_candidates(out:Path)->tuple[dict[int,bytes],dict]:
    out.mkdir(parents=True,exist_ok=True)
    bodies,info=fit.compile_candidates(out)
    return bodies,info

def validate(output:Path,seed:int=7,samples:int=20)->dict:
    if output.exists(): raise FileExistsError(f"fresh output directory required: {output}")
    output.mkdir(parents=True)
    original=(ROOT/"extracted/exefs/code.bin").read_bytes(); base=BASE_IMAGE.read_bytes(); base_ips=BASE_IPS.read_bytes()
    game=json.loads((ROOT/"config/game_info.json").read_text(encoding="utf-8"))
    if game.get("code_sha256")!=ORIGINAL_SHA: raise ValueError("game_info original hash mismatch")
    (output/"base.replayed.bin").write_bytes(apply_ips(original,base_ips))
    compile_info_path=output/"compiled"; compile_info_path.mkdir(parents=True,exist_ok=True)
    candidates,compile_info=compile_candidates(compile_info_path)
    staged=compose_images(original,base,base_ips,candidates,expected_base_sha="efdb59e33463e964dbb1d9884a92d23dc8e4e4f78390c4e7810414f956a03d12")
    final=staged["image"]
    (output/"code.h18-family-final.bin").write_bytes(final)
    (output/"code.h18-family-overlay.ips").write_bytes(staged["overlay_ips"])
    (output/"code.h18-family-combined.ips").write_bytes(staged["combined_ips"])
    # Exact final-VMA candidate execution, with the H18 base image as the original-side memory image.
    f3274.ORIG_BIN=BASE_IMAGE
    original3274=f3274.original_function(base); candidate3274=_extract(final,0x003F3274,len(candidates[0x003F3274]))
    cases3274,mismatch=f3274.run_pair(original3274,candidate3274,seed,samples)
    if mismatch: raise AssertionError(f"003f3274 final image differential failed: {mismatch}")
    (output/"controls-3274").mkdir()
    controls3274=f3274.compile_negative_controls(f3274.SOURCE.read_text(encoding="utf-8"),original3274,seed,samples,output/"controls-3274")
    if len(controls3274)!=5 or not all(x["detected"] for x in controls3274): raise AssertionError("003f3274 control escaped")
    results={"0x003f3274":{"cases":len(cases3274),"passed":True}}
    src32=f32f4.SOURCE.read_text(encoding="utf-8"); cases32={}
    for e in f32f4.ENTRIES:
        body=_extract(final,e["address"],len(candidates[e["address"]])); rows,first=f32f4.compare_entry(base,e,body,seed,samples)
        if first: raise AssertionError(f"{e['address']:#x} final image differential failed: {first}")
        cases32[hex(e["address"]) ]={"cases":len(rows),"passed":True}
    (output/"controls-32f4").mkdir()
    controls32=f32f4.negative_controls(base,src32,seed,samples,output/"controls-32f4")
    if len(controls32)!=8 or not all(x["detected"] for x in controls32): raise AssertionError("32f4 control escaped")
    results["32f4_family"]=cases32
    # Existing H18 image is the original side; composed H18 image is executed directly from final VMAs.
    fxseed=seed^0x003F34A0; cases_tail={}
    for addr in (0x003F34A0,0x003F34CC):
        rows=[]
        for i in range(samples):
            fx=f3454.fixture(fxseed,i)
            old=f3454.execute(base,None,addr,fx); new=f3454.execute(final,None,addr,fx)
            why=f3454.compare(old,new); rows.append({"index":i,"passed":why is None,"difference":why})
        if not all(x["passed"] for x in rows): raise AssertionError(f"{addr:#x} final image differential failed")
        cases_tail[hex(addr)]={"cases":len(rows),"passed":True}
    results["34a0_34cc"]=cases_tail
    # Final-address mutant checks for the two tail family entries.
    specs=[("34a0_wrong_sentinel","0x00472570u","0x00472574u",0x003F34A0),
           ("34cc_wrong_zero","*reinterpret_cast<u32*>(0x004727A0u) = 0;","*reinterpret_cast<u32*>(0x004727A4u) = 0;",0x003F34CC)]
    controls_tail=[]; src3454=f3454.SOURCE.read_text(encoding="utf-8")
    for i,(name,before,after,addr) in enumerate(specs):
        if src3454.count(before)!=1: raise ValueError(f"mutant anchor not unique: {name}")
        mutant=output/"controls-3454"/f"{name}.cpp"; mutant.parent.mkdir(parents=True,exist_ok=True); mutant.write_text(src3454.replace(before,after,1),encoding="utf-8")
        bad,info=f3454.compile_candidates(mutant.parent,mutant,name); badbody=bad[addr]
        badimg=bytearray(final); off=addr-IMAGE_BASE; badimg[off:off+len(badbody)]=badbody
        fx=f3454.fixture(fxseed^0xABC,i)
        why=f3454.compare(f3454.execute(base,None,addr,fx),f3454.execute(bytes(badimg),None,addr,fx))
        if why is None: raise AssertionError(f"final image control escaped: {name}")
        controls_tail.append({"name":name,"detected":True,"difference":why})
    results["negative_controls"]={"003f3274":controls3274,"32f4_family":controls32,"34a0_34cc":controls_tail}
    # Exercise the excluded 0x003f3454 original through the cumulative composition.
    preserved=[]
    for i in range(samples):
        fx=f3454.fixture(seed^0x003F3454,i)
        old=f3454.execute(base,None,0x003F3454,fx); new=f3454.execute(final,None,0x003F3454,fx)
        why=f3454.compare(old,new)
        if why: raise AssertionError(f"preserved 003f3454 differed: {why}")
        preserved.append(bool(new["calls"] and new["calls"][0]["thumb_state"]))
    if not all(preserved): raise AssertionError("preserved original Thumb transition absent")
    report={"schema_version":1,"task":"h18-003f-family-cumulative-staging","original_sha256":sha(original),
      "base_sha256":sha(base),"base_ips_sha256":sha(base_ips),"final_sha256":sha(final),
      "overlay_ips_sha256":sha(staged["overlay_ips"]),"combined_ips_sha256":sha(staged["combined_ips"]),
      "compile":compile_info,"placements":staged["placements"],"h18_base_ips_records":staged["base_records"],
      "combined_ips_records":staged["combined_records"],"changed_bytes_from_base":staged["changed_bytes_from_base"],
      "cave":{"vma_start":hex(CAVE[0]),"vma_end":hex(CAVE[1]),"unchanged":staged["cave_unchanged"],"sha256":staged["cave_sha256"]},
      "oversized_003f3454":{"unchanged":staged["3454_unchanged"],"execution_cases":len(preserved),"all_passed":True,"thumb_transition":all(preserved)},
      "functional":results,"caller":{"status":"not_run","reason":"No actual startup caller/order was proven in the prior records."},
      "runtime":"not_run","passed":True,"limitations":["Unicorn synthetic-fixture tests do not establish real startup order or caller composition.","The 003f3454 vector iterator remains modeled by the existing harness.","This private cumulative artifact is not production promotion or whole-game equivalence."]}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output-dir',type=Path,required=True); p.add_argument('--seed',type=int,default=7); p.add_argument('--samples',type=int,default=20); a=p.parse_args(argv)
    r=validate(a.output_dir,a.seed,a.samples); print(json.dumps({"passed":r["passed"],"final_sha256":r["final_sha256"],"changed_bytes_from_base":r["changed_bytes_from_base"],"report":str(a.output_dir/'report.json')},indent=2)); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
