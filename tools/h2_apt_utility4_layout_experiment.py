#!/usr/bin/env python3
"""Offline reference-image layout experiment; synthetic ARM caller and wrapper."""
import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import unicorn as u
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_LR
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment_support import load_pinned_reference
from tools.h2_apt_utility4_entry_experiment import (
    SOURCE, ADDRESS, WRAPPER, TEXT, STACK, DATA, SP, REGS, make_case, sha)
from unicorn.arm_const import UC_ARM_REG_SP, UC_ARM_REG_R0, UC_ARM_REG_CPSR

CAVE = 0x003fee54
CALLER = 0x01000000
STOP = CALLER + 4
BASE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
EXPECTED_BLOB = bytes.fromhex("00482de908d04de224c09fe50000a0e300008de504008de50400a0e30010a0e30020a0e30030a0e33cff2fe108d08de20088bde81c5a2b00")

def branch(source, target, link=False):
    delta = target - source - 8
    if source % 4 or target % 4 or not -(1 << 25) <= delta < (1 << 25):
        raise ValueError("unaligned ARM branch or target out of range")
    return struct.pack("<I", (0xeb000000 if link else 0xea000000) | ((delta >> 2) & 0xffffff))

def verify_blob(blob, relocations):
    if relocations or blob != EXPECTED_BLOB:
        raise ValueError("candidate blob/relocations not the inspected PIC body")
    if struct.unpack_from("<I", blob, len(blob) - 4)[0] != WRAPPER:
        raise ValueError("wrong wrapper address/state")
    if WRAPPER & 1:
        raise ValueError("wrapper must be ARM")

def validate_image(base, patched, blob, occupied=()):
    if hashlib.sha256(base).hexdigest() != BASE_SHA:
        raise ValueError("reference hash mismatch")
    if len(base) != len(patched): raise ValueError("length mismatch")
    cave_off, entry_off = CAVE - TEXT, ADDRESS - TEXT
    cave_end = cave_off + len(blob)
    if any(max(CAVE, a) < min(CAVE + len(blob), b) for a,b in occupied):
        raise ValueError("cave overlaps occupied placement")
    if base[cave_off:cave_end] != bytes(len(blob)):
        raise ValueError("reference cave is not zero")
    if patched[0x002c0f28-TEXT:0x002c1320-TEXT] != base[0x002c0f28-TEXT:0x002c1320-TEXT]:
        raise ValueError("next function damaged")
    if patched[entry_off:entry_off+4] != branch(ADDRESS, CAVE):
        raise ValueError("wrong entry branch or state")
    if patched[cave_off:cave_end] != blob:
        raise ValueError("wrong cave payload")
    allowed = set(range(entry_off, entry_off+4)) | set(range(cave_off, cave_end))
    if any(a != b and i not in allowed for i,(a,b) in enumerate(zip(base,patched))):
        raise ValueError("unauthorized byte change")
    if patched[0x002c0ee0-TEXT:entry_off] != base[0x002c0ee0-TEXT:entry_off]:
        raise ValueError("preceding entry damaged")
    if patched[0x002c0f28-TEXT:0x002c1320-TEXT] != base[0x002c0f28-TEXT:0x002c1320-TEXT]:
        raise ValueError("next function damaged")

def compose(base, blob):
    result = bytearray(base)
    e, c = ADDRESS-TEXT, CAVE-TEXT
    result[e:e+4] = branch(ADDRESS,CAVE)
    result[c:c+len(blob)] = blob
    validate_image(base, bytes(result), blob)
    return bytes(result)

def run_arm(image, case):
    machine = u.Uc(u.UC_ARCH_ARM, u.UC_MODE_ARM)
    machine.mem_map(TEXT, (len(image)+4095)&~4095)
    machine.mem_write(TEXT,image)
    machine.mem_map(STACK,0x2000); machine.mem_write(STACK,case["stack"])
    machine.mem_map(DATA,0x1000); machine.mem_write(DATA,case["data"])
    machine.mem_map(CALLER,0x1000)
    machine.mem_write(CALLER,branch(CALLER,ADDRESS,True))
    machine.reg_write(UC_ARM_REG_CPSR,0x10|case["flags"])
    for reg,val in zip(REGS,case["regs"]): machine.reg_write(reg,val)
    machine.reg_write(UC_ARM_REG_SP,SP)
    machine.reg_write(UC_ARM_REG_LR,0xabc000)
    calls=[]
    def hook(m,address,size,userdata):
        if address==WRAPPER:
            sp=m.reg_read(UC_ARM_REG_SP)
            calls.append({"args":[m.reg_read(r) for r in REGS[:4]]+list(struct.unpack("<2I",m.mem_read(sp,8))),
                          "alignment":sp%8,"thumb":bool(m.reg_read(UC_ARM_REG_CPSR)&0x20)})
            m.reg_write(UC_ARM_REG_R0,case["ret"])
            m.reg_write(UC_ARM_REG_PC,m.reg_read(UC_ARM_REG_LR))
    machine.hook_add(u.UC_HOOK_CODE,hook)
    machine.emu_start(CALLER,STOP,count=200)
    return {"pc":machine.reg_read(UC_ARM_REG_PC), "sp":machine.reg_read(UC_ARM_REG_SP),
            "r0":machine.reg_read(UC_ARM_REG_R0),"preserved":[machine.reg_read(r) for r in REGS[4:12]],
            "data":bytes(machine.mem_read(DATA,0x1000)).hex(),
            "live_stack":bytes(machine.mem_read(SP,0x1000)).hex(),"calls":calls}

def errors(left,right,case):
    expected_call=[{"args":[4,0,0,0,0,0],"alignment":0,"thumb":False}]
    out=[]
    for label,res in (("original",left),("patched",right)):
        for key,expected in (("pc",STOP),("sp",SP),("r0",case["ret"]),
                             ("preserved",case["regs"][4:12]),("data",case["data"].hex()),
                             ("live_stack",case["stack"][0x1000:].hex()),("calls",expected_call)):
            if res[key]!=expected: out.append(label+":"+key)
    for key in left:
        if left[key]!=right[key]: out.append("differential:"+key)
    return out

def must_reject(fn):
    try: fn()
    except ValueError as error: return str(error)
    raise AssertionError("negative control was not rejected")

def experiment(code, output):
    output.mkdir(parents=True,exist_ok=False)
    pin=load_pinned_reference(code,ROOT/"config/game_info.json",ROOT/"config/functions.csv")
    base=pin.image
    source_hash=sha(SOURCE)
    obj=output/"candidate.o"
    build=compile_tu_armv6k(SOURCE,obj,ROOT)
    if build.returncode: raise RuntimeError(build.stderr)
    blob,relocs=extract_elf_functions_detailed(obj)["candidate_002c0efc"]
    verify_blob(blob,relocs)
    patched=compose(base,blob)
    (output/"patched-code.bin").write_bytes(patched)
    failures=[]
    for seed in (1,2):
        rng=random.Random(seed)
        values=[0,1,0x7fffffff,0x80000000,0xffffffff]+[rng.getrandbits(32) for _ in range(59)]
        for i,value in enumerate(values):
            case=make_case(rng,value)
            diff=errors(run_arm(base,case),run_arm(patched,case),case)
            if diff: failures.append({"seed":seed,"case":i,"errors":diff})
    e,c=ADDRESS-TEXT,CAVE-TEXT
    oversized=bytearray(patched); oversized[e:e+len(blob)]=blob; oversized[e:e+4]=branch(ADDRESS,CAVE)
    wrong_branch=bytearray(patched); wrong_branch[e:e+4]=branch(ADDRESS,CAVE,True)
    wrong_literal=bytearray(blob); wrong_literal[-4:]=struct.pack("<I",WRAPPER|1)
    wrong_input=bytearray(base); wrong_input[0]^=1
    unauthorized=bytearray(patched); unauthorized[0]^=1
    controls={
      "oversized":must_reject(lambda:validate_image(base,bytes(oversized),blob)),
      "branch_link":must_reject(lambda:validate_image(base,bytes(wrong_branch),blob)),
      "wrong_state":must_reject(lambda:verify_blob(bytes(wrong_literal),())),
      "overlap":must_reject(lambda:validate_image(base,patched,blob,[(CAVE+4,CAVE+8)])),
      "input_drift":must_reject(lambda:validate_image(bytes(wrong_input),patched,blob)),
      "unauthorized":must_reject(lambda:validate_image(base,bytes(unauthorized),blob)),
      "misaligned_branch":must_reject(lambda:branch(ADDRESS,CAVE|1))}
    if sha(SOURCE)!=source_hash: raise ValueError("source changed during run")
    report={"passed":not failures,"cases":128,"seeds":[1,2],"failures":failures,"negative_controls":controls,
            "reference_sha256":sha(code),"source_sha256":source_hash,"object_sha256":sha(obj),
            "patched_sha256":hashlib.sha256(patched).hexdigest(),"branch_hex":branch(ADDRESS,CAVE).hex(),
            "cave":hex(CAVE),"body_hex":blob.hex(),"relocations":len(relocs),"compile_command":build.args,
            "limits":["synthetic ARM BL caller and controlled wrapper only","reference zeros do not prove final composed image cave availability or runtime execute permission","no Thumb, real wrapper/service, emulator or production integration"]}
    (output/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"passed":report["passed"],"cases":128,"failures":failures,"controls":controls}))
    return report["passed"]

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--code",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    raise SystemExit(0 if experiment(a.code,a.output) else 1)
