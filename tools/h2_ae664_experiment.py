#!/usr/bin/env python3
"""Pinned ARM differential for the ASD control-code mapping helper."""
from __future__ import annotations
import hashlib, json, random, struct, sys
from pathlib import Path
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools import h2_2b787c_experiment as line_count
from tools import h2_ae6b0_experiment as control_predicate
IMAGE=(ROOT/'extracted/exefs/code.bin').read_bytes()
IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
SOURCE=ROOT/'src/engine/leaf_batch28_b.cpp'
OUT=ROOT/'build/agent-work/H2-semantic/h2-ae664-convert/run001'
ENTRY=0x002AE664; SPAN=76; CANDIDATE=0x00800000; STOP=0x0080F000
TEXT=0x00100000; TABLE=0x00464DA8; STACK=0x00A0FF00; NOP=struct.pack('<I',0xE320F000)
def sha(b): return hashlib.sha256(b).hexdigest()
def compile_candidate(path=SOURCE,name='leaf_batch28_b.o'):
    OUT.mkdir(parents=True,exist_ok=True); obj=OUT/name
    result=compile_tu_armv6k(path,obj,ROOT)
    if result.returncode: raise RuntimeError(result.stderr)
    body,relocs=extract_elf_functions_detailed(obj)['func_002ae664']
    if relocs or len(body)>SPAN or len(body)%4: raise AssertionError((len(body),relocs))
    return body
def table_bytes(entries, sentinel_value=0):
    if len(entries)>=256: raise ValueError('table fixture needs sentinel slot')
    b=bytearray(256*16)
    for i,(key,value) in enumerate(entries):
        struct.pack_into('<H',b,i*16,key&0xffff); struct.pack_into('<I',b,i*16+4,value&0xffffffff)
    struct.pack_into('<H',b,len(entries)*16,0xF890)
    struct.pack_into('<I',b,len(entries)*16+4,sentinel_value&0xffffffff)
    return bytes(b)
def setup(body,entries,raw_table=None):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,0x00500000); u.mem_write(TEXT,IMAGE)
    u.mem_map(0x00800000,0x10000); u.mem_map(0x00A00000,0x10000)
    u.mem_write(TABLE,raw_table if raw_table is not None else table_bytes(entries))
    if body is not None: u.mem_write(CANDIDATE,body)
    state={'done':False,'writes':[]}
    def on_code(uc,a,_size,_data):
        if a==STOP: state['done']=True; uc.emu_stop()
    def on_write(_uc,_kind,a,size,value,_data): state['writes'].append((a,size,value&0xffffffff))
    u.hook_add(UC_HOOK_CODE,on_code); u.hook_add(UC_HOOK_MEM_WRITE,on_write)
    u._h2_state=state
    return u
def execute(u,address,code,seed):
    rng=random.Random(seed); initial={r:rng.getrandbits(32) for r in (UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3,UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)}
    state=u._h2_state; state['done']=False; state['writes'].clear()
    u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP)
    for r,v in initial.items(): u.reg_write(r,v)
    u.reg_write(UC_ARM_REG_R0,code&0xffffffff)
    try: u.emu_start(address,0,count=20000); fault=None
    except (UcError,OSError) as e: fault=str(e)
    saved=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
    writes=tuple(state['writes'])
    return {'r0':u.reg_read(UC_ARM_REG_R0),'preserved':all(u.reg_read(r)==initial[r] for r in saved),'sp':u.reg_read(UC_ARM_REG_SP)==STACK,'stack_writes':tuple(w for w in writes if STACK-4 <= w[0] < STACK),'external_writes':tuple(w for w in writes if not (STACK-4 <= w[0] < STACK)),'fault':fault,'done':state['done']}
def equivalent(a,b):
    return all(a[k]==b[k] for k in ('r0','preserved','sp','external_writes','fault','done'))
def expected(code,entries):
    for key,value in entries:
        if key==0xF890: break
        if key==code: return value&0xffffffff
    return 0
def run_direct(body):
    entries=((0,0),(1,0xffffffff),(0x41,0x12345678),(0xF801,1),(0xF803,3),(0xF88F,0x80000000),(0xF803,0xDEADBEEF))
    a,b=setup(None,entries),setup(body,entries)
    directed=(0x10000,0x10001,0x7fffffff,0x80000000,0xfffff801,0xffffffff)
    values=set(range(65536)); values.update(directed); rng=random.Random(20261103); values.update(rng.getrandbits(32) for _ in range(256))
    for i,code in enumerate(sorted(values)):
        ref=execute(a,ENTRY,code,i^0x2AE664); got=execute(b,CANDIDATE,code,i^0x2AE664)
        if not equivalent(ref,got) or ref['r0']!=expected(code,entries) or not ref['preserved'] or not ref['sp'] or ref['external_writes'] or ref['fault'] or not ref['done']:
            raise AssertionError(f'{code:#x}: {ref} != {got}; want={expected(code,entries):#x}')
    layouts={'sentinel-first':(), 'late-match':tuple((0x1000+i,i+1) for i in range(31))+((0xFF00,0xA5A5A5A5),), 'duplicate-first-wins':((0xF803,0x13579BDF),(4,4),(0xF803,0x2468ACE0))}
    for rows in layouts.values():
        x,y=setup(None,rows),setup(body,rows)
        for j,code in enumerate((0xFF00,0xF803,0xF890,0x2222)):
            ref=execute(x,ENTRY,code,0x6600+j); got=execute(y,CANDIDATE,code,0x6600+j)
            if not equivalent(ref,got) or ref['r0']!=expected(code,rows): raise AssertionError(f'layout mismatch {code:#x}')
    controls=[]
    for name,old,new,code,entries2,raw in (
        ('key-match','if (key == code)','if (key == code + 1u)',0xF802,entries,None),
        ('sentinel','if (key == 0xf890)','if (key == 0xf891)',0xF890,(),table_bytes((),0xDEADBEEF))):
        text=SOURCE.read_text(encoding='utf-8')
        if text.count(old)!=1: raise AssertionError(f'mutation anchor {name}')
        mutant_src=OUT/f'mutant-{name}.cpp'; mutant_src.write_text(text.replace(old,new,1),encoding='utf-8')
        mutant=compile_candidate(mutant_src,f'mutant-{name}.o')
        orig=execute(setup(None,entries2,raw),ENTRY,code,1234)
        changed=execute(setup(mutant,entries2,raw),CANDIDATE,code,1234)
        if equivalent(orig,changed): raise AssertionError(f'negative control undetected: {name}')
        controls.append({'name':name,'input':hex(code),'original':orig['r0'],'mutant':changed['r0'],'detected':True})
    return {'distinct_cases':len(values),'halfword_domain':65536,'directed_u32':len(directed),'seeded_u32':256,'table_layouts':list(layouts),'contract':'first matching u16 key before 0xF890 sentinel returns u32 value at +4; no match returns 0','abi':'r4-r11 and SP preserved; no non-stack writes (original spills r4 to SP-4, candidate uses no stack)','negative_controls':controls}
def run_compositions(body):
    if (SPAN-len(body))%4: raise AssertionError('unaligned patch tail')
    image=bytearray(IMAGE); off=ENTRY-0x00100000; image[off:off+SPAN]=body+NOP*((SPAN-len(body))//4)
    predicate=control_predicate.compile_candidate()
    predicate_meta={'0x002AE6B0':{'source_sha256':sha(control_predicate.SOURCE.read_bytes()),'body_sha256':sha(predicate),'body_size':len(predicate)}}
    pred_off=0x002AE6B0-0x00100000; image[pred_off:pred_off+24]=predicate
    image=bytes(image)
    cases=line_count.make_cases()
    for i,case in enumerate(cases):
        a=line_count.run_helper(case,image=IMAGE); b=line_count.run_helper(case,image=image)
        if a!=b: raise AssertionError(f'line-count case {i}/{case.name}: {a} != {b}')
    parents=[]
    for selector in (11,19):
        a=line_count.run_parent_composition(selector,None,image=IMAGE); b=line_count.run_parent_composition(selector,None,image=image)
        if a!=b: raise AssertionError(f'titleConfig selector {selector} composition mismatch')
        parents.append({'selector':selector,'done':b['done'],'object_20':b['object_20']})
    return {'line_count_cases':len(cases),'route':'original 0x002B787C through converted 0x002AE664 and 0x002AE6B0','title_config_compositions':parents,'integrated_helpers':predicate_meta,'harness_sha256':{'h2_2b787c_experiment.py':sha((ROOT/'tools/h2_2b787c_experiment.py').read_bytes()),'h2_86928_experiment.py':sha((ROOT/'tools/h2_86928_experiment.py').read_bytes()),'h2_ae6b0_experiment.py':sha((ROOT/'tools/h2_ae6b0_experiment.py').read_bytes())}}
def main():
    if sha(IMAGE)!=IMAGE_SHA: raise SystemExit('pinned image hash mismatch')
    body=compile_candidate(); direct=run_direct(body); composition=run_compositions(body)
    original=IMAGE[ENTRY-0x00100000:ENTRY-0x00100000+SPAN]
    report={'function':'func_002ae664','address':hex(ENTRY),'reference_image_sha256':sha(IMAGE),'source_sha256':sha(SOURCE.read_bytes()),'body_sha256':sha(body),'body_size':len(body),'body_hex':body.hex(),'relocations':0,'byte_identical':body==original,'direct':direct,'caller_composition':composition,'runtime':'not_run; offline evidence only'}
    out=OUT/'report.json'; out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); print(json.dumps(report,indent=2)); print(f'report: {out}')
if __name__=='__main__': main()
