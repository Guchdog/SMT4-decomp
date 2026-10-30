#!/usr/bin/env python3
"""Bounded actual ARM branch sites and preceding-entry fallthrough; offline only."""
import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import unicorn as u
from unicorn.arm_const import UC_ARM_REG_PC,UC_ARM_REG_LR,UC_ARM_REG_SP,UC_ARM_REG_R0,UC_ARM_REG_CPSR
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment_support import load_pinned_reference
from tools.h2_apt_utility4_entry_experiment import SOURCE,ADDRESS,WRAPPER,TEXT,STACK,DATA,SP,REGS,make_case,sha
from tools.h2_apt_utility4_layout_experiment import CAVE,branch,verify_blob,compose

BL=(0x2c0f6c,0x2c1260,0x2c1304)
B=(0x106f00,0x10700c,0x2a8164,0x2c5638)
FALL=0x2c0ee0
STOP=0x01000000
HELPERS=(0x2bb7a0,0x2bb774)

def expected_site_bytes(start):
    return branch(start,ADDRESS,start in BL) if start != FALL else None

def execute(image,start,case):
    m=u.Uc(u.UC_ARCH_ARM,u.UC_MODE_ARM)
    m.mem_map(TEXT,(len(image)+4095)&~4095);m.mem_write(TEXT,image)
    m.mem_map(STACK,0x2000);m.mem_write(STACK,case["stack"])
    m.mem_map(DATA,0x1000);m.mem_write(DATA,case["data"])
    m.mem_map(STOP,0x1000)
    m.reg_write(UC_ARM_REG_CPSR,0x10|case["flags"])
    for r,v in zip(REGS,case["regs"]):m.reg_write(r,v)
    m.reg_write(UC_ARM_REG_SP,SP);m.reg_write(UC_ARM_REG_LR,STOP)
    trace=[]
    def hook(machine,address,size,unused):
        if address in HELPERS:
            trace.append({"target":hex(address),"r0":machine.reg_read(UC_ARM_REG_R0)})
            machine.reg_write(UC_ARM_REG_PC,machine.reg_read(UC_ARM_REG_LR))
        elif address==WRAPPER:
            sp=machine.reg_read(UC_ARM_REG_SP)
            trace.append({"target":hex(address),"args":[machine.reg_read(r) for r in REGS[:4]]+list(struct.unpack("<2I",machine.mem_read(sp,8))),"sp_align":sp%8,"thumb":bool(machine.reg_read(UC_ARM_REG_CPSR)&0x20)})
            machine.reg_write(UC_ARM_REG_R0,case["ret"])
            machine.reg_write(UC_ARM_REG_PC,machine.reg_read(UC_ARM_REG_LR))
    m.hook_add(u.UC_HOOK_CODE,hook)
    end=start+4 if start in BL else STOP
    fault=None
    try: m.emu_start(start,end,count=200)
    except u.UcError as exc: fault=str(exc)
    return {"pc":m.reg_read(UC_ARM_REG_PC),"sp":m.reg_read(UC_ARM_REG_SP),"r0":m.reg_read(UC_ARM_REG_R0),
            "preserved":[m.reg_read(r) for r in REGS[4:12]],"data":bytes(m.mem_read(DATA,0x1000)).hex(),
            "live_stack":bytes(m.mem_read(SP,0x1000)).hex(),"trace":trace,"fault":fault}

def mismatches(original,patched,start,case):
    end=start+4 if start in BL else STOP
    expected=([{"target":hex(HELPERS[0]),"r0":0},{"target":hex(HELPERS[1]),"r0":1}] if start==FALL else [])
    expected.append({"target":hex(WRAPPER),"args":[4,0,0,0,0,0],"sp_align":0,"thumb":False})
    differences=[]
    for name,res in (("original",original),("patched",patched)):
        for key,want in (("pc",end),("fault",None),("sp",SP),("r0",case["ret"]),
                         ("preserved",case["regs"][4:12]),("data",case["data"].hex()),
                         ("live_stack",case["stack"][0x1000:].hex()),("trace",expected)):
            if res[key]!=want: differences.append(name+":"+key)
    for key in original:
        if original[key]!=patched[key]: differences.append("differential:"+key)
    return differences

def experiment(code,output):
    output.mkdir(parents=True,exist_ok=False)
    reference=load_pinned_reference(code,ROOT/"config/game_info.json",ROOT/"config/functions.csv").image
    source_hash=sha(SOURCE);obj=output/"candidate.o"
    build=compile_tu_armv6k(SOURCE,obj,ROOT)
    if build.returncode:raise RuntimeError(build.stderr)
    body,relocs=extract_elf_functions_detailed(obj)["candidate_002c0efc"]
    verify_blob(body,relocs)
    patched=compose(reference,body)
    for site in BL+B:
        off=site-TEXT
        if reference[off:off+4]!=expected_site_bytes(site):
            raise ValueError("unexpected caller instruction "+hex(site))
    failures=[];counts={}
    for start in BL+B+(FALL,):
        counts[hex(start)]=0
        for seed in (7,2026):
            rng=random.Random(seed^start)
            for value in (0,1,0x7fffffff,0x80000000,0xffffffff):
                case=make_case(rng,value)
                err=mismatches(execute(reference,start,case),execute(patched,start,case),start,case)
                if err:failures.append({"start":hex(start),"seed":seed,"value":hex(value),"errors":err})
                else:counts[hex(start)]+=1
    case=make_case(random.Random(9),0x80000000)
    baseline=execute(reference,B[0],case)
    wrong_link=bytearray(patched); wrong_link[ADDRESS-TEXT:ADDRESS-TEXT+4]=branch(ADDRESS,CAVE,True)
    link_errors=mismatches(baseline,execute(bytes(wrong_link),B[0],case),B[0],case)
    wrong_body=bytearray(patched);wrong_body[CAVE-TEXT+24:CAVE-TEXT+28]=bytes.fromhex("0500a0e3")
    body_errors=mismatches(baseline,execute(bytes(wrong_body),B[0],case),B[0],case)
    if sha(SOURCE)!=source_hash:raise ValueError("source drift")
    passed=not failures and bool(link_errors) and "patched:trace" in body_errors
    report={"passed":passed,"cases_per_site":counts,"failures":failures,
            "negative_controls":{"branch_bl_instead_of_b":link_errors,"command_5_body":body_errors},
            "reference_sha256":sha(code),"patched_sha256":hashlib.sha256(patched).hexdigest(),
            "source_sha256":source_hash,"object_sha256":sha(obj),"compile_command":build.args,
            "windows":"each actual site instruction to its return continuation; 0x2c0ee0 through fallthrough to synthetic ARM return",
            "limitations":["caller setup and post-return continuation not executed","controlled helper/wrapper hooks do not model real side effects","synthetic Thumb not tested; no real Thumb caller established","provisional reference-image cave only, no runtime permission or final-image occupancy"]}
    (output/"report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({"passed":passed,"counts":counts,"failures":failures,"negative_controls":report["negative_controls"]}))
    return passed

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--code",type=Path,required=True);p.add_argument("--output",type=Path,required=True)
    args=p.parse_args();raise SystemExit(0 if experiment(args.code,args.output) else 1)
