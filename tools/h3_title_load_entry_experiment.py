#!/usr/bin/env python3
"""Offline differential for the H3 title load-entry slice with two declared HLEs."""
from __future__ import annotations
import hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.h3_candidate_support import relocate_h3_entry
from tools.semantic_experiment import require_unicorn
import unicorn
from unicorn import arm_const as arm
CODE=ROOT/'extracted/exefs/code.bin'
OBJ=ROOT/'build/agent-work/H3-semantic/h3-title-entry/direct-call-obj/h3_title_load_entry_candidate.o'
TEXT=0x00100000; TEXT_SIZE=0x00480000; INJECT=0x01000000; DATA=0x02000000; STACK=0x08000000; SP=STACK+0x2000
MANAGER=0x0044DE28; WORK=DATA+0x100; POINT=DATA+0x800; RETURN=INJECT+0x8000
CALC=0x00202950; GET_POINT=0x002BF6D0; U32=0xffffffff

def run(entry:int,candidate:bytes|None,x:int,y:int,seed:int):
    uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM); uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    uc.mem_map(TEXT,TEXT_SIZE,7); uc.mem_write(TEXT,CODE.read_bytes())
    uc.reg_write(arm.UC_ARM_REG_FPEXC,0x40000000)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2,0x00F00000)
    uc.mem_map(INJECT,0x10000,7); uc.mem_map(DATA,0x10000,3); uc.mem_map(STACK,0x4000,3)
    if candidate is not None: uc.mem_write(INJECT,candidate)
    manager=bytearray(0x20); struct.pack_into('<I',manager,4,WORK); uc.mem_write(MANAGER,bytes(manager))
    poison=bytes(((i*53+seed*17)&255) for i in range(0x400)); uc.mem_write(WORK,poison)
    point=bytearray(0xC); struct.pack_into('<H',point,6,0x4321); struct.pack_into('<hh',point,8,x,y); uc.mem_write(POINT,bytes(point))
    trace=[]
    def hook(emu,address,size,user):
        if address==RETURN: emu.emu_stop(); return
        if address in (CALC,GET_POINT):
            regs=[emu.reg_read(getattr(arm,f'UC_ARM_REG_R{i}')) for i in range(4)]
            trace.append((address,tuple(regs[:2])))
            if address==CALC: ret=0xCA1C0001
            else: ret=POINT
            emu.reg_write(arm.UC_ARM_REG_R0,ret)
            emu.reg_write(arm.UC_ARM_REG_PC,emu.reg_read(arm.UC_ARM_REG_LR))
    uc.hook_add(unicorn.UC_HOOK_CODE,hook)
    uc.reg_write(arm.UC_ARM_REG_SP,SP); uc.reg_write(arm.UC_ARM_REG_LR,RETURN)
    try: uc.emu_start(entry,RETURN,count=10000)
    except unicorn.UcError as exc: raise RuntimeError(f"emu error {exc} at pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}") from exc
    if uc.reg_read(arm.UC_ARM_REG_PC)!=RETURN: raise RuntimeError(f'entry failed to return, pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}')
    return bytes(uc.mem_read(MANAGER,8)),bytes(uc.mem_read(WORK,0x400)),trace

def main():
    image=CODE.read_bytes(); raw,relocs=extract_elf_functions_detailed(OBJ)['h3_title_load_entry_candidate']; cand,relocation_rows=relocate_h3_entry(raw,relocs,INJECT)
    cases=[('zero',0,0),('signed-minmax',-32768,32767),('negative',-1,-2),('positive',12345,23456)]
    results=[]
    for i,(name,x,y) in enumerate(cases):
        orig=run(0x0030A9A4,None,x,y,i+1); repl=run(INJECT,cand,x,y,i+1)
        if orig!=repl: raise SystemExit(f'FAIL {name}: memory_equal={orig[:2]==repl[:2]}, original_trace={orig[2]}, candidate_trace={repl[2]}')
        results.append({'case':name,'x':x,'y':y,'manager_work_prefix_sha256':hashlib.sha256(orig[0]).hexdigest(),'work_sha256':hashlib.sha256(orig[1]).hexdigest(),'calls':[{'address':hex(a),'args':[hex(v) for v in r]} for a,r in orig[2]]})
    mutated=bytearray(cand); original_insn=struct.unpack_from('<I',mutated,0x40)[0]; struct.pack_into('<I',mutated,0x40,(original_insn & ~0xF) | 6)
    control=run(INJECT,bytes(mutated),0,0,1)
    baseline=run(0x0030A9A4,None,0,0,1)
    if control[:2]==baseline[:2]: raise SystemExit('negative control was not detected')
    print(json.dumps({'status':'passed','negative_control':'x halfword read offset changed from +8 to +6; detected','relocations':relocation_rows,'scope':'0x0030A9A4 with original 0x00202950 and 0x002BF6D0 replaced by deterministic stubs','code_sha256':hashlib.sha256(image).hexdigest(),'candidate_sha256':hashlib.sha256(cand).hexdigest(),'cases':results},indent=2))
if __name__=='__main__': main()
