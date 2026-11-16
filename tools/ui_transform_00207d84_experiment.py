#!/usr/bin/env python3
"""Bounded ARM/VFP differential for the generic UI transform wrapper (in-slot at 0x00207D84)."""
from __future__ import annotations

import argparse, hashlib, json, random, struct, sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import encode_ips, apply_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"
CUMULATIVE_MANIFEST = ROOT / "build/h2-86928-integration/cumulative-image/manifest.json"
ENTRY, SLOT = 0x00207D84, 128
ARM_NOP = struct.pack("<I", 0xE320F000)
CODE_BASE, CODE_SIZE = 0x00100000, 0x00400000
DATA_BASE, DATA_SIZE = 0x00500000, 0x00020000
STACK, STACK_SIZE = 0x08000000, 0x00010000
SP, STOP = STACK + 0x8000, STACK + 0x9000
VECTOR, SCRATCH = 0x004EA91C, 0x00472550
PTR_SLOT, CONTEXT = DATA_BASE + 0x100, DATA_BASE + 0x2000
CALLER, OUT, CONFIG, FIRST, SECOND = 0x0024B874, DATA_BASE+0x5000, DATA_BASE+0x6000, DATA_BASE+0x7000, DATA_BASE+0x8000
U32 = 0xFFFFFFFF

def sha(b): return hashlib.sha256(b).hexdigest()

def bl(site, target, link=True):
    d = target - (site + 8)
    if d & 3 or not -(1 << 25) <= d < (1 << 25): raise ValueError("ARM branch range/alignment")
    return (0xEB000000 if link else 0xEA000000) | ((d >> 2) & 0xFFFFFF)

def compile_body(out):
    obj = out / "leaf_batch30_c.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode: raise RuntimeError(result.stderr or "candidate TU compile failed")
    body, relocs = extract_elf_functions_detailed(obj)["ui_func_00207d84"]
    return body, relocs, obj, list(result.args)

def stage(original, body, relocs):
    if len(body) > SLOT or len(body) % 4:
        raise ValueError(f"body cannot fit in-place slot: {len(body)}/{SLOT}")
    fixed = bytearray(body)
    resolved = []
    targets = {"ui_func_002c5218": 0x002C5218, "ui_func_0026330c": 0x0026330C}
    for r in relocs:
        if r.relocation_type not in (28, 29) or r.symbol_name not in targets:
            raise ValueError(f"unsupported relocation {r}")
        site = ENTRY + r.offset
        word = struct.unpack_from("<I", fixed, r.offset)[0]
        expected = 0xEB000000 if r.relocation_type == 28 else 0xEA000000
        if word & 0xFF000000 != expected:
            raise ValueError("unexpected call opcode")
        target = targets[r.symbol_name]
        if target & 1:
            raise ValueError(f"target {hex(target)} is not even ARM")
        struct.pack_into("<I", fixed, r.offset, bl(site, target, r.relocation_type == 28))
        resolved.append({
            "offset": r.offset,
            "type": "R_ARM_CALL",
            "symbol": r.symbol_name,
            "site": hex(site),
            "target": hex(target),
            "thumb": False,
        })
    if len(resolved) != 2:
        raise ValueError(f"expected two original ARM calls, got {resolved}")
    nop_words = (SLOT - len(fixed)) // 4
    slot_payload = bytes(fixed) + ARM_NOP * nop_words
    if len(slot_payload) != SLOT:
        raise AssertionError("slot payload size mismatch")
    staged = bytearray(original)
    entry_off = ENTRY - CODE_BASE
    staged[entry_off:entry_off + SLOT] = slot_payload
    edits = [(entry_off, slot_payload)]
    ips = encode_ips(edits, len(original))
    if apply_ips(original, ips) != bytes(staged):
        raise AssertionError("IPS replay mismatch")
    allowed = set(range(entry_off, entry_off + SLOT))
    outside = [i for i, (x, y) in enumerate(zip(original, staged)) if x != y and i not in allowed]
    if outside:
        raise AssertionError(f"unexpected staged changes outside in-place slot: {outside[:8]}")
    return bytes(staged), ips, resolved, sorted(allowed), slot_payload

def slot_reference_audit(image):
    lo, hi = ENTRY, ENTRY + SLOT
    entry_refs, interior_refs, ptrs = [], [], []
    for off in range(0, len(image) - 3, 4):
        addr = CODE_BASE + off
        if lo <= addr < hi:
            continue
        w = struct.unpack_from("<I", image, off)[0]
        if lo <= w < hi:
            ptrs.append((hex(addr), hex(w)))
        if w & 0x0E000000 == 0x0A000000:
            imm = w & 0xFFFFFF
            imm = imm - 0x1000000 if imm & 0x800000 else imm
            t = addr + 8 + (imm << 2)
            if lo <= t < hi:
                item = {"site": hex(addr), "kind": "ARM branch", "target": hex(t)}
                (entry_refs if t == lo else interior_refs).append(item)
        if w & 0x0F7F0000 == 0x051F0000:
            imm = w & 0xFFF
            t = addr + 8 + (imm if w & (1 << 23) else -imm)
            if lo <= t < hi:
                item = {"site": hex(addr), "kind": "ARM PC-relative memory", "target": hex(t)}
                (entry_refs if t == lo else interior_refs).append(item)
    for off in range(0, len(image) - 1, 2):
        addr = CODE_BASE + off
        if lo <= addr < hi:
            continue
        h = struct.unpack_from("<H", image, off)[0]
        if h & 0xF800 == 0x4800:
            t = ((addr + 4) & ~3) + ((h & 0xFF) << 2)
            if lo <= t < hi:
                item = {"site": hex(addr), "kind": "Thumb literal", "target": hex(t)}
                (entry_refs if t == lo else interior_refs).append(item)
    if interior_refs:
        raise AssertionError(f"unexpected interior references into slot: {interior_refs}")
    return {
        "extent": [hex(lo), hex(hi)],
        "capacity": hi - lo,
        "aligned_pointer_words": len(ptrs),
        "entry_branch_refs": entry_refs,
        "interior_refs": interior_refs,
    }

def decode_ips_vma_ranges(ips: bytes) -> list[tuple[int, int]]:
    if ips[:5] != b"PATCH" or ips[-3:] != b"EOF":
        raise ValueError("invalid IPS header/footer")
    pos = 5
    ranges = []
    while pos < len(ips) - 3:
        off = (ips[pos] << 16) | (ips[pos + 1] << 8) | ips[pos + 2]
        size = (ips[pos + 3] << 8) | ips[pos + 4]
        pos += 5
        if size == 0:
            rle_len = (ips[pos] << 8) | ips[pos + 1]
            pos += 3
            ranges.append((CODE_BASE + off, CODE_BASE + off + rle_len))
        else:
            pos += size
            ranges.append((CODE_BASE + off, CODE_BASE + off + size))
    return ranges

def cumulative_h2_collision_audit(original: bytes) -> dict:
    manifest = json.loads(CUMULATIVE_MANIFEST.read_text(encoding="utf-8"))
    ips_path = ROOT / Path(manifest["artifact_paths"]["ips"])
    img_path = ROOT / Path(manifest["artifact_paths"]["image"])
    cum_ips = ips_path.read_bytes()
    cum_img = img_path.read_bytes()
    if sha(cum_ips) != manifest["ips_sha256"] or sha(cum_img) != manifest["patched_sha256"]:
        raise AssertionError("cumulative H2 manifest SHA mismatch")
    ranges = decode_ips_vma_ranges(cum_ips)
    slot_lo, slot_hi = ENTRY, ENTRY + SLOT
    overlaps = [
        {"start": hex(lo), "end": hex(hi)}
        for lo, hi in ranges
        if not (hi <= slot_lo or lo >= slot_hi)
    ]
    prior_cave_lo, prior_cave_hi = 0x003FEE54, 0x003FEE54 + 156
    prior_cave_overlaps = [
        {"start": hex(lo), "end": hex(hi)}
        for lo, hi in ranges
        if not (hi <= prior_cave_lo or lo >= prior_cave_hi)
    ]
    entry_off = ENTRY - CODE_BASE
    slot_unmodified_in_cumulative = (
        cum_img[entry_off:entry_off + SLOT] == original[entry_off:entry_off + SLOT]
    )
    if overlaps or not slot_unmodified_in_cumulative:
        raise AssertionError(f"slot collision with cumulative H2 image: {overlaps}")
    return {
        "manifest_path": str(CUMULATIVE_MANIFEST.relative_to(ROOT)),
        "manifest_sha256": sha(CUMULATIVE_MANIFEST.read_bytes()),
        "cumulative_image_sha256": manifest["patched_sha256"],
        "cumulative_ips_sha256": manifest["ips_sha256"],
        "cumulative_ips_record_count": len(ranges),
        "slot_extent": [hex(slot_lo), hex(slot_hi)],
        "slot_overlapping_records": overlaps,
        "slot_collision_count": len(overlaps),
        "slot_bytes_unmodified_in_cumulative_image": slot_unmodified_in_cumulative,
        "prior_cave_0x003fee54_overlaps_in_cumulative": prior_cave_overlaps,
        "prior_cave_0x003fee54_eliminated": True,
    }

class Machine:
    def __init__(self,image,seed,vector,context=None,fpscr=0):
        self.uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM|unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE,CODE_SIZE); self.uc.mem_write(CODE_BASE,image)
        self.uc.mem_map(DATA_BASE,DATA_SIZE); self.uc.mem_map(STACK,STACK_SIZE)
        self.uc.mem_write(PTR_SLOT+0x80,struct.pack("<I",CONTEXT))
        # 0x44EA5C is in the mapped original code region and is the first pointer load.
        self.uc.mem_write(0x0044EA5C,struct.pack("<I",PTR_SLOT))
        ctx=bytearray(0x100)
        # Affine matrix P+0x38: translate xyz by (+.25,-.5,+.75).
        struct.pack_into("<12f",ctx,0x38,1,0,0,.25, 0,1,0,-.5, 0,0,1,.75)
        # Projection numerator rows and finite denominator z+2.
        struct.pack_into("<12f",ctx,0xA8,1,0,0,0, 0,1,0,0, 0,0,0,2)
        if context:
            for off,val in context.items(): struct.pack_into("<f",ctx,off,val)
        self.uc.mem_write(CONTEXT,bytes(ctx))
        self.uc.mem_write(VECTOR,struct.pack("<4I",*vector))
        self.uc.reg_write(arm.UC_ARM_REG_SP,SP); self.uc.reg_write(arm.UC_ARM_REG_LR,STOP)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR,fpscr)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC,0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_R0,0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1,0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2,0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3,0x44444444)
        for n in range(4,12): self.uc.reg_write(getattr(arm,f"UC_ARM_REG_R{n}"),0xA0000000+n)
        self.hooks=[]
        self.traced_writes=[]
        self.uc.hook_add(unicorn.UC_HOOK_CODE,self._hook)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,self._write)
    def _write(self,uc,access,address,size,value,_data):
        if SCRATCH <= address < SCRATCH+16 or VECTOR <= address < VECTOR+16:
            self.traced_writes.append((address,size,value & U32))
    def _hook(self,uc,addr,size,_data):
        if addr==STOP: uc.emu_stop()
        elif addr in (0x0024B8E0,0x0024B908): self.hooks.append(hex(addr))
        elif addr in (0x002698F4,0x00269768,0x0024C62C):
            self.hooks.append(hex(addr))
            if addr==0x0024C62C: uc.reg_write(arm.UC_ARM_REG_S0,f32(.125))
            uc.reg_write(arm.UC_ARM_REG_PC,uc.reg_read(arm.UC_ARM_REG_LR))
    def run(self,entry,args=None):
        if args:
            for i,v in enumerate(args): self.uc.reg_write(getattr(arm,f"UC_ARM_REG_R{i}"),v)
        before=tuple(self.uc.reg_read(getattr(arm,f"UC_ARM_REG_R{n}")) for n in range(4,12))
        vfp_before=tuple(self.uc.reg_read(getattr(arm,f"UC_ARM_REG_S{n}")) for n in range(16,32))
        self.uc.emu_start(entry,STOP,timeout=1000000,count=20000)
        return {
            "r0":self.uc.reg_read(arm.UC_ARM_REG_R0),"s0":self.uc.reg_read(arm.UC_ARM_REG_S0),
            "fpscr":self.uc.reg_read(arm.UC_ARM_REG_FPSCR),"sp":self.uc.reg_read(arm.UC_ARM_REG_SP),
            "saved_before":before,"saved_after":tuple(self.uc.reg_read(getattr(arm,f"UC_ARM_REG_R{n}")) for n in range(4,12)),
            "s16_s31_before":vfp_before,"s16_s31_after":tuple(self.uc.reg_read(getattr(arm,f"UC_ARM_REG_S{n}")) for n in range(16,32)),
            "vector":self.uc.mem_read(VECTOR,16).hex(),"scratch":self.uc.mem_read(SCRATCH,16).hex(),
            "ordered_global_writes":self.traced_writes,
            # Below entry SP is the callee-owned frame and may differ by C++ layout.
            "caller_stack":self.uc.mem_read(SP,0x80).hex(),
        }

def caller_case(image, a, first, second):
    m=Machine(image,a,[0,0,0,0])
    cfg=bytearray(0x100); cfg[0x9c]=2; m.uc.mem_write(CONFIG,bytes(cfg))
    m.uc.mem_write(FIRST,struct.pack('<4I',*first)); m.uc.mem_write(SECOND,struct.pack('<4I',*second))
    m.uc.reg_write(arm.UC_ARM_REG_R0,FIRST); m.uc.reg_write(arm.UC_ARM_REG_R1,CONFIG)
    m.uc.reg_write(arm.UC_ARM_REG_R2,0); m.uc.reg_write(arm.UC_ARM_REG_R3,SECOND)
    m.uc.emu_start(CALLER,STOP,timeout=1000000,count=50000)
    return {"call_trace":m.hooks,"out":m.uc.mem_read(FIRST,0x40).hex(),
      "vector":m.uc.mem_read(VECTOR,0x120).hex(),"scratch":m.uc.mem_read(SCRATCH,16).hex(),
      "ordered_global_writes":m.traced_writes,
      "r0":m.uc.reg_read(arm.UC_ARM_REG_R0),"s0":m.uc.reg_read(arm.UC_ARM_REG_S0),
      "fpscr":m.uc.reg_read(arm.UC_ARM_REG_FPSCR),"sp":m.uc.reg_read(arm.UC_ARM_REG_SP)}

def f32(x): return struct.unpack("<I",struct.pack("<f",x))[0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); ap.add_argument("--seed",type=int,default=20261102)
    a=ap.parse_args(); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    original=IMAGE.read_bytes(); body,relocs,obj,cmd=compile_body(out)
    staged,ips,resolved,patch_offsets,slot_payload=stage(original,body,relocs)
    audit=slot_reference_audit(original)
    collision_audit=cumulative_h2_collision_audit(original)
    (out/"staged.ips").write_bytes(ips)
    (out/"staged-image.bin").write_bytes(staged)
    (out/"candidate-body.bin").write_bytes(body)
    (out/"slot-payload.bin").write_bytes(slot_payload)
    cases=[("basis_x",[f32(1),f32(0),f32(0),f32(1)],{}), ("basis_y",[f32(0),f32(1),f32(0),f32(1)],{}),
           ("basis_z",[f32(0),f32(0),f32(1),f32(1)],{}), ("negative",[f32(-2.5),f32(3.25),f32(-.75),f32(9)],{}),
           ("perspective",[f32(-1.25),f32(2.5),f32(3),f32(0)],{0xD8:.125,0xDC:-.25,0xE0:.75,0xE4:1.5}),
           ("finite_near_denominator",[f32(1),f32(-1),f32(0),f32(1)],{0xE4:-.749}),
           ("seeded",[f32((a.seed%17)-8),f32(((a.seed//3)%13)-6),f32(((a.seed//7)%9)+1),f32(0)],{})]
    direct=[]
    for label,vec,context in cases:
        left=Machine(original,a.seed,vec,context).run(ENTRY); right=Machine(staged,a.seed,vec,context).run(ENTRY)
        direct.append({"case":label,"equal":left==right,"original":left,"candidate":right})
    rounding=[]
    for name,mode in [("RN",0),("RP",1<<22),("RM",2<<22),("RZ",3<<22)]:
        vec=[f32(-1.25),f32(2.5),f32(3.0),f32(1.0)]
        left=Machine(original,a.seed,vec,{},mode).run(ENTRY); right=Machine(staged,a.seed,vec,{},mode).run(ENTRY)
        rounding.append({"mode":name,"equal":left==right,"original":left,"candidate":right})
    caller=[]
    vectors=[("same",[f32(1),f32(2),f32(3),f32(1)],[f32(1),f32(2),f32(3),f32(1)]),
             ("distinct",[f32(-1),f32(.5),f32(2),f32(1)],[f32(3),f32(-2),f32(4),f32(1)])]
    for label,first,second in vectors:
        left=caller_case(original,a,first,second); right=caller_case(staged,a,first,second)
        caller.append({"case":label,"equal":left==right,"original":left,"candidate":right})
    # Comparator controls inject one-observation corruptions so the positive
    # harness proves it rejects missing/ordered-global effects.
    baseline=direct[0]["original"]
    controls=[]
    for name,field,mutator in [
        ("wrong_x_y_order","vector",lambda b: b.__setitem__(slice(0,8),b[4:8]+b[0:4])),
        ("missing_zero_w_store","vector",lambda b: b.__setitem__(slice(12,16),struct.pack("<I",f32(1)))),
        ("scratch_word_mutated","scratch",lambda b: b.__setitem__(0,b[0]^1)),
    ]:
        altered=dict(baseline); raw=bytearray.fromhex(altered[field]); mutator(raw); altered[field]=raw.hex()
        controls.append({"name":name,"detected":altered!=baseline})
    report={"schema":2,"experiment":"ui_transform_00207d84_in_slot","seed":a.seed,
      "placement_mode":"in_slot","entry_vma":hex(ENTRY),"slot_extent":[hex(ENTRY),hex(ENTRY+SLOT)],
      "image_sha256":sha(original),"source_sha256":sha(SOURCE.read_bytes()),
      "object_sha256":sha(obj.read_bytes()),"body_sha256":sha(body),
      "slot_payload_sha256":sha(slot_payload),"staged_image_sha256":sha(staged),
      "body_size":len(body),"slot_size":SLOT,"nop_tail_bytes":SLOT-len(body),
      "cave_vma":None,"relocations":resolved,
      "slot_reference_audit":audit,"cumulative_h2_collision_audit":collision_audit,
      "patch_byte_offsets":[hex(patch_offsets[0]),hex(patch_offsets[-1])],
      "changed_outside_slot":False,
      "ips_sha256":sha(ips),"ips_replays":apply_ips(original,ips)==staged,
      "direct":direct,"all_direct_equal":all(x["equal"] for x in direct),
      "fpscr_rounding_modes":rounding,"all_rounding_equal":all(x["equal"] for x in rounding),
      "caller_compositions":caller,"all_caller_equal":all(x["equal"] for x in caller),
      "negative_controls":controls,"all_controls_detected":all(x["detected"] for x in controls),
      "caller_stubbed_dependencies":["0x002698F4","0x00269768","0x0024C62C (fixed s0=0.125)"],
      "limitations":["Only bounded finite valid pointer/context fixtures; no natural H2 reachability claim.","Original projection callees remain in the image."]}
    (out/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({
        "placement_mode": report["placement_mode"],
        "body_size": len(body),
        "slot_size": SLOT,
        "direct": f"{sum(x['equal'] for x in direct)}/{len(direct)}",
        "fpscr": f"{sum(x['equal'] for x in rounding)}/{len(rounding)}",
        "caller": f"{sum(x['equal'] for x in caller)}/{len(caller)}",
        "controls": f"{sum(x['detected'] for x in controls)}/{len(controls)}",
        "cumulative_collisions": collision_audit["slot_collision_count"],
        "out": str(out),
    }))
    return 0 if (
        report["all_direct_equal"]
        and report["all_rounding_equal"]
        and report["all_caller_equal"]
        and report["all_controls_detected"]
        and collision_audit["slot_collision_count"] == 0
    ) else 1
if __name__=="__main__": raise SystemExit(main())
