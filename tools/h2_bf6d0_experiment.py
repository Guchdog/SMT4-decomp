#!/usr/bin/env python3
"""Pinned ARM differential for the H2 manager-slot address helper."""
from __future__ import annotations
import hashlib,json,random,struct,sys
from pathlib import Path
from unicorn import Uc,UcError,UC_ARCH_ARM,UC_MODE_ARM,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
IMAGE=(ROOT/'extracted/exefs/code.bin').read_bytes(); IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
SOURCE=ROOT/'src/engine/leaf_batch27_b.cpp'; OUT=ROOT/'build/agent-work/H2-semantic/h2-bf6d0-manager-slot-convert/run001'
ENTRY=0x002BF6D0; SPAN=64; DEP=0x002B0188; CANDIDATE=0x00800000; STOP=0x0080F000
TEXT=0x00100000; MANAGER=0x00900000; INDIRECT=0x00900100; BASE=0x00900200; STACK=0x00A0FF00

def sha(b): return hashlib.sha256(b).hexdigest()
def compile_candidate(path=SOURCE,name='leaf_batch27_b.o',entry=CANDIDATE,allow_oversize=False):
    OUT.mkdir(parents=True,exist_ok=True); obj=OUT/name
    r=compile_tu_armv6k(path,obj,ROOT)
    if r.returncode: raise RuntimeError(r.stderr)
    body,relocs=extract_elf_functions_detailed(obj)['camp_func_002bf6d0']; fixed=bytearray(body); resolved=[]
    for rel in relocs:
        if rel.relocation_type!=28 or rel.symbol_name!='ui_func_002b0188' or rel.explicit_addend is not None: raise AssertionError(f'unsupported relocation: {rel}')
        place=entry+rel.offset; ins=struct.unpack_from('<I',fixed,rel.offset)[0]
        if ins&0xff000000!=0xeb000000: raise AssertionError(f'bad BL {ins:#x}')
        delta=DEP-(place+8)
        struct.pack_into('<I',fixed,rel.offset,0xeb000000|((delta>>2)&0xffffff))
        resolved.append({'offset':rel.offset,'target':hex(DEP),'type':rel.relocation_type})
    if (len(fixed)>SPAN and not allow_oversize) or len(fixed)%4: raise AssertionError(f'body size {len(fixed)} exceeds slot {SPAN}')
    return bytes(fixed),resolved
def setup(body=None,entry=CANDIDATE,final=False):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,0x00500000); u.mem_write(TEXT,IMAGE)
    u.mem_map(0x00800000,0x10000); u.mem_map(0x00900000,0x10000); u.mem_map(0x00A00000,0x10000)
    u.mem_write(MANAGER+4,struct.pack('<I',INDIRECT)); u.mem_write(INDIRECT,struct.pack('<I',BASE))
    if body is not None:
        if final: u.mem_write(ENTRY,body)
        else: u.mem_write(entry,body)
    st={'done':False,'calls':[],'writes':[]}
    def on_code(uc,address,_size,_data):
        if address==DEP:
            st['calls'].append(uc.reg_read(UC_ARM_REG_R0)); uc.reg_write(UC_ARM_REG_R0,MANAGER); uc.reg_write(UC_ARM_REG_PC,uc.reg_read(UC_ARM_REG_LR))
        elif address==STOP: st['done']=True; uc.emu_stop()
    def on_write(_uc,_kind,address,size,value,_data): st['writes'].append((address,size,value&0xffffffff))
    u.hook_add(UC_HOOK_CODE,on_code); u.hook_add(UC_HOOK_MEM_WRITE,on_write); u._state=st
    return u
def exec_case(u,address,group,index,seed):
    st=u._state; st['done']=False; st['calls'].clear(); st['writes'].clear()
    rng=random.Random(seed); regs=(UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
    before={r:rng.getrandbits(32) for r in regs}; u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP)
    for r,v in before.items(): u.reg_write(r,v)
    u.reg_write(UC_ARM_REG_R0,group&0xffffffff); u.reg_write(UC_ARM_REG_R1,index&0xffffffff)
    try: u.emu_start(address,0,count=1000); fault=None
    except (UcError,OSError) as e: fault=str(e)
    external=tuple(w for w in st['writes'] if not STACK-16<=w[0]<STACK)
    return {'r0':u.reg_read(UC_ARM_REG_R0),'callee_saved':all(u.reg_read(r)==before[r] for r in regs[3:]),'sp':u.reg_read(UC_ARM_REG_SP)==STACK,'helper_args':tuple(st['calls']),'external_writes':external,'done':st['done'],'fault':fault}
def signed32(v): return v-(1<<32) if v&0x80000000 else v
def expected(index):
    n=signed32(index); q=abs(n)//1000 * (-1 if n<0 else 1); rem=n-q*1000
    return (BASE+rem*20)&0xffffffff
def equivalent(a,b): return a==b
def run_differential(body,final_body):
    ref,cand,final=setup(),setup(body),setup(final_body,entry=ENTRY,final=True)
    values=set((0,1,999,1000,1001,1999,2000,0x7fffffff,0x80000000,0xffffffff,0xfffffc18,0xfffffc17))
    values.update(v&0xffffffff for v in range(-1000,1001))
    rng=random.Random(20261105); values.update(rng.getrandbits(32) for _ in range(1024))
    groups=(0,1,0x2f,0x24,0x1d,0xffffffff)
    for i,index in enumerate(sorted(values)):
        group=groups[i%len(groups)]; a=exec_case(ref,ENTRY,group,index,i^0x2bf6d0); b=exec_case(cand,CANDIDATE,group,index,i^0x2bf6d0); f=exec_case(final,ENTRY,group,index,i^0x2bf6d0)
        if a!=b or a!=f: raise AssertionError(f'index {index:#010x}: original={a}, candidate={b}, final={f}')
        if a['r0']!=expected(index) or a['helper_args']!=(group,) or not a['callee_saved'] or not a['sp'] or a['external_writes'] or not a['done'] or a['fault']:
            raise AssertionError(f'contract mismatch {index:#x}: {a} expected {expected(index):#x}')
    controls=[]
    for name,old,new,index in (('remainder','% 1000','% 999',1000),('indirect-offset','manager + 4','manager + 8',1000)):
        text=SOURCE.read_text(encoding='utf-8')
        if text.count(old)!=1: raise AssertionError(f'mutant anchor {name}')
        mutant_src=OUT/f'mutant-{name}.cpp'; mutant_src.write_text(text.replace(old,new,1),encoding='utf-8')
        mutant,_=compile_candidate(mutant_src,f'mutant-{name}.o',CANDIDATE,allow_oversize=True)
        a=exec_case(ref,ENTRY,0x2f,index,8000); b=exec_case(setup(mutant),CANDIDATE,0x2f,index,8000)
        if equivalent(a,b): raise AssertionError(f'negative control missed: {name}')
        controls.append({'name':name,'input':hex(index),'original':hex(a['r0']),'mutant':hex(b['r0']),'detected':True})
    return {'distinct_indices':len(values),'exhaustive_signed_remainder_domain':2001,'directed_u32':12,'seeded_u32':1024,'group_ids':list(map(hex,groups)),'abi':'r4-r11 and SP preserved; no non-stack writes; original spills within SP-8, candidate within SP-16','helper':'0x002B0188 is intercepted identically and receives group in r0','negative_controls':controls}
def main():
    if sha(IMAGE)!=IMAGE_SHA: raise SystemExit('pinned image hash mismatch')
    body,relocs=compile_candidate(); final_body,final_relocs=compile_candidate(name='leaf_batch27_b-final.o',entry=ENTRY)
    report={'function':'camp_func_002bf6d0','address':hex(ENTRY),'reference_image_sha256':sha(IMAGE),'source_sha256':sha(SOURCE.read_bytes()),'body_sha256':sha(body),'body_size':len(body),'body_hex':body.hex(),'relocations':relocs,'final_relocations':final_relocs,'byte_identical':body==IMAGE[ENTRY-0x00100000:ENTRY-0x00100000+SPAN],'direct':run_differential(body,final_body),'caller_composition':'not_run; direct helper boundary is mocked identically for the pinned original/candidate','runtime':'not_run; offline helper contract only'}
    out=OUT/'report.json'; out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,indent=2)); print(f'report: {out}')
if __name__=='__main__': main()
