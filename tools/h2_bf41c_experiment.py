#!/usr/bin/env python3
"""Pinned ARM differential for the H2 task-registration lookup."""
from __future__ import annotations
import hashlib, json, random, struct, sys
from pathlib import Path
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
IMAGE=(ROOT/'extracted/exefs/code.bin').read_bytes()
IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
SOURCE=ROOT/'src/engine/leaf_batch32_c.cpp'
OUT=ROOT/'build/agent-work/H2-semantic/h2-bf41c-task-registry-convert/run001'
ENTRY=0x002BF41C; SPAN=68; READY=0x002FC0EC; CANDIDATE=0x00800000; STOP=0x0080F000
TEXT=0x00100000; REGISTRY_GLOBAL=0x004E3CF4; BUCKETS=0x00900000; NODE_BASE=0x00910000
WORK=0x00990000; WORK_GLOBAL=0x0044E2D0; STACK=0x00A0FF00

def sha(b): return hashlib.sha256(b).hexdigest()
def compile_candidate(path=SOURCE,name='leaf_batch32_c.o'):
    OUT.mkdir(parents=True,exist_ok=True); obj=OUT/name
    r=compile_tu_armv6k(path,obj,ROOT)
    if r.returncode: raise RuntimeError(r.stderr)
    body,relocs=extract_elf_functions_detailed(obj)['battle_func_002bf41c']
    if relocs or len(body)>SPAN or len(body)%4: raise AssertionError((len(body),relocs))
    return body
def setup(body=None):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,0x00500000); u.mem_write(TEXT,IMAGE)
    u.mem_map(0x00800000,0x10000); u.mem_map(0x00900000,0x00300000)
    u.mem_write(REGISTRY_GLOBAL,struct.pack('<I',BUCKETS))
    u.mem_write(BUCKETS,bytes(4096*8))
    if body is not None: u.mem_write(CANDIDATE,body)
    state={'done':False,'writes':[],'calls':[]}
    def on_code(uc,a,_size,_data):
        if a==ENTRY or a==READY: state['calls'].append((a,uc.reg_read(UC_ARM_REG_R0)))
        if a==STOP: state['done']=True; uc.emu_stop()
    def on_write(_uc,_kind,a,size,v,_data): state['writes'].append((a,size,v&0xffffffff))
    u.hook_add(UC_HOOK_CODE,on_code); u.hook_add(UC_HOOK_MEM_WRITE,on_write); u._h2_state=state
    return u
def set_chain(u,index,items):
    u.mem_write(BUCKETS+index*8,struct.pack('<I',NODE_BASE if items else 0))
    for i,(handle,_) in enumerate(items):
        addr=NODE_BASE+i*0x100; data=bytearray(0x50)
        struct.pack_into('<I',data,0x28,handle&0xffffffff)
        next_addr=NODE_BASE+(i+1)*0x100 if i+1<len(items) else 0
        struct.pack_into('<I',data,0x4c,next_addr)
        u.mem_write(addr,bytes(data))
def execute(u,address,handle,seed):
    rng=random.Random(seed); regs=(UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
    before={r:rng.getrandbits(32) for r in regs}; st=u._h2_state; st['done']=False; st['writes'].clear(); st['calls'].clear()
    u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP)
    for r,v in before.items(): u.reg_write(r,v)
    u.reg_write(UC_ARM_REG_R0,handle&0xffffffff)
    try: u.emu_start(address,0,count=4000); fault=None
    except (UcError,OSError) as e: fault=str(e)
    saved=regs[3:]
    return {'r0':u.reg_read(UC_ARM_REG_R0),'callee_saved':all(u.reg_read(r)==before[r] for r in saved),'sp':u.reg_read(UC_ARM_REG_SP)==STACK,'writes':tuple(st['writes']),'done':st['done'],'fault':fault}
def equivalent(a,b): return a==b
def run_direct(body):
    ref,cand=setup(),setup(body)
    # Exhaust every bucket index with an exact task-handle hit.
    for i in range(4096):
        handle=((i<<20)|0x54321)&0xffffffff
        set_chain(ref,i,((handle,0),)); set_chain(cand,i,((handle,0),))
        a=execute(ref,ENTRY,handle,i); b=execute(cand,CANDIDATE,handle,i)
        if a!=b or a['r0']!=1 or not a['done'] or a['fault'] or a['writes'] or not a['callee_saved'] or not a['sp']:
            raise AssertionError(f'bucket {i} hit mismatch {a} != {b}')
    cases=[]
    # Empty registry, null task handle, bounds and collisions with first/middle/tail/missing keys.
    for h in (0,1,0xfffff,0x100000,0x100001,0x7fffffff,0x80000000,0xfff00000,0xffffffff):
        for u in (ref,cand): u.mem_write(BUCKETS,bytes(4096*8))
        a=execute(ref,ENTRY,h,0xA000+h); b=execute(cand,CANDIDATE,h,0xA000+h)
        if a!=b or a['r0']!=0 or a['fault'] or a['writes']: raise AssertionError(f'empty {h:#x}: {a} != {b}')
        cases.append(h)
    chain=(0x00123450,0x00123451,0x00123456,0x00123457)
    for u in (ref,cand): set_chain(u,1,tuple((h,0) for h in chain))
    for i,h in enumerate(chain+(0x00123458,)):
        a=execute(ref,ENTRY,h,0xC000+i); b=execute(cand,CANDIDATE,h,0xC000+i)
        expected=int(h in chain)
        if a!=b or a['r0']!=expected: raise AssertionError(f'chain {h:#x}: {a} != {b}')
    # Deterministic randomized 8-node chains in distinct buckets.
    rng=random.Random(20261104)
    for i in range(64):
        idx=rng.randrange(4096); base=(idx<<20); handles=tuple(base|rng.randrange(1<<20) for _ in range(8)); query=handles[rng.randrange(8)] if i%2==0 else base|rng.randrange(1<<20)
        rows=tuple((h,0) for h in handles)
        for u in (ref,cand): set_chain(u,idx,rows)
        a=execute(ref,ENTRY,query,i+700); b=execute(cand,CANDIDATE,query,i+700)
        if a!=b or a['r0']!=int(query in handles): raise AssertionError(f'random list {i}: {a} != {b}')
    controls=[]
    for name,old,new,h in (('bucket-index','handle >> 20','handle >> 19',0x00100001),('handle-offset','node + 0x28','node + 0x2c',0x00100001)):
        text=SOURCE.read_text(encoding='utf-8')
        if text.count(old)!=1: raise AssertionError(f'mutation anchor {name}')
        mutant_src=OUT/f'mutant-{name}.cpp'; mutant_src.write_text(text.replace(old,new,1),encoding='utf-8')
        mutant=compile_candidate(mutant_src,f'mutant-{name}.o')
        mutant_uc=setup(mutant)
        for u in (ref,cand,mutant_uc):
            u.mem_write(BUCKETS,bytes(4096*8)); set_chain(u,1,((h,0),))
        original=execute(ref,ENTRY,h,9000); changed=execute(mutant_uc,CANDIDATE,h,9000)
        if equivalent(original,changed): raise AssertionError(f'mutation missed: {name}')
        controls.append({'name':name,'input':hex(h),'original':original['r0'],'mutant':changed['r0'],'detected':True})
    return {'bucket_indices_exhausted':4096,'empty_and_boundary_inputs':len(cases),'chain_probes':5,'random_chains':64,'negative_controls':controls,'contract':'select bucket handle >> 20 from 4096-entry table (8-byte stride), scan node handle at +0x28 and next at +0x4c, return 1 on equality else 0','abi':'r4-r11 and SP preserved; no writes'}
def run_ready_composition(body):
    image=bytearray(IMAGE); off=ENTRY-0x00100000; image[off:off+SPAN]=body
    patched=bytes(image); cases=[]
    for name,work_ptr,task,rows,want in (
        ('null-work',0,0,(),1),('registered',WORK,0x00123456,((0x00123456,0),),0),
        ('unregistered',WORK,0x00123456,(),1),('null-task-absent',WORK,0,(),1),
        ('null-task-present',WORK,0,((0,0),),0)):
        outcomes=[]
        for code in (IMAGE,patched):
            u=setup(); u.mem_write(TEXT,code)
            u.mem_write(WORK_GLOBAL,struct.pack('<I',work_ptr))
            u.mem_write(WORK,struct.pack('<I',task))
            idx=(task>>20)&0xfff; set_chain(u,idx,rows)
            result=execute(u,READY,0,0xBF41C)
            if result['r0']!=want or result['fault'] or not result['done']:
                raise AssertionError(f'{name} caller result {result}, want {want}')
            result['code_events']=tuple(u._h2_state['calls'])
            outcomes.append(result)
        if outcomes[0]!=outcomes[1]: raise AssertionError(f'{name} original/candidate ready mismatch')
        calls=outcomes[0]['code_events']
        if name=='null-work' and any(a==ENTRY for a,_ in calls): raise AssertionError('null work unexpectedly called task registry')
        if name!='null-work' and not any(a==ENTRY and value==task for a,value in calls): raise AssertionError(f'{name} did not forward task handle: {calls}')
        cases.append({'name':name,'ready':want,'code_events':calls})
    return {'caller':'original TitleConfig_IsReady 0x002FC0EC calls helper at final address','cases':cases}
def main():
    if sha(IMAGE)!=IMAGE_SHA: raise SystemExit('pinned original image hash mismatch')
    body=compile_candidate(); direct=run_direct(body); caller=run_ready_composition(body)
    original=IMAGE[ENTRY-0x00100000:ENTRY-0x00100000+SPAN]
    report={'function':'battle_func_002bf41c','address':hex(ENTRY),'reference_image_sha256':sha(IMAGE),'source_sha256':sha(SOURCE.read_bytes()),'body_sha256':sha(body),'body_size':len(body),'body_hex':body.hex(),'relocations':0,'byte_identical':body==original,'direct':direct,'caller_composition':caller,'runtime':'not_run; bounded offline scheduler-registry fixture only'}
    out=OUT/'report.json'; out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,indent=2)); print(f'report: {out}')
if __name__=='__main__': main()
