#!/usr/bin/env python3
"""Offline differential and staged caller validation for 0x002BDAC0."""
from __future__ import annotations
import hashlib, json, random, struct, sys
from pathlib import Path
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_READ, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
IMAGE=ROOT/'extracted/exefs/code.bin'; IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
BASE=ROOT/'build/agent-work/H2-semantic/h2-slot-getters-0029f248-0029f260/run001/staged/code.h2-slot-getters.bin'
BASE_SHA='b71fece339cc135393f03a4e806bcf5a2d158cfe1ed8402df249c3613d933140'
SOURCE=ROOT/'src/engine/leaf_batch13_c.cpp'
OUT=ROOT/'build/agent-work/H2-semantic/h2-titleconfig-002bdac0-convert/run004'
ADDR=0x002BDAC0; SPAN=108; TEXT=0x00100000; TEMP=0x00800000; STOP=0x0080F000
DATA=0x00900000; DATA_SIZE=0x40000; STACK=0x00A0FF00; NOP=struct.pack('<I',0xE320F000); MASK=0xffffffff

def sha(b): return hashlib.sha256(b).hexdigest()
def compile_source(name, source):
    obj=OUT/name
    r=compile_tu_armv6k(source,obj,ROOT)
    if r.returncode: raise RuntimeError(r.stderr)
    body, rel=extract_elf_functions_detailed(obj)['camp_func_002bdac0']
    if rel: raise AssertionError(f'unexpected relocations: {rel}')
    return body

def machine(image, inject=None, stop=STOP):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,(len(image)+0xfff)&~0xfff); u.mem_write(TEXT,image)
    u.mem_map(0x00800000,0x10000); u.mem_map(DATA,DATA_SIZE); u.mem_map(0x00A00000,0x10000)
    if inject: u.mem_write(inject[0],inject[1])
    state={'done':False,'reads':[],'writes':[],'last_pc':None}
    def code(m,a,size,d):
        state['last_pc']=a
        if a==stop: state['done']=True; m.emu_stop()
    def read(m,k,a,size,v,d): state['reads'].append((a,size,bytes(m.mem_read(a,size))))
    def write(m,k,a,size,v,d): state['writes'].append((a,size,v&MASK))
    u.hook_add(UC_HOOK_CODE,code); u.hook_add(UC_HOOK_MEM_READ,read); u.hook_add(UC_HOOK_MEM_WRITE,write); u._state=state
    return u

def fixture(u,obj,mode,selector,values, table=None):
    # Reset the entire object and a compact table window.
    u.mem_write(obj,bytes(0x200)); row=DATA+0x18000
    u.mem_write(row,bytes(0x100))
    if table is None: table=row-(mode*12&MASK)&MASK
    u.mem_write(obj+0x4c,struct.pack('<I',table))
    for off,val in zip((0,2,4,6),values): u.mem_write(row+off,struct.pack('<h',val))
    return row,table

def execute(u,entry,obj,mode,selector,values,null=False,table_override=None):
    st=u._state; st.update(done=False,reads=[],writes=[],last_pc=None)
    row,table=fixture(u,obj,mode,selector,values,table_override)
    if null: u.mem_write(obj+0x4c,b'\0'*4)
    # Mark fields whose clearing is observable.
    u.mem_write(obj+0x50,b'\xA5'*2); u.mem_write(obj+0x52,b'\xA5'*2)
    u.mem_write(obj+0x54,b'\xA5'); u.mem_write(obj+0x86,b'\xA5'); u.mem_write(obj+0x8a,b'\xA5')
    saved={r:0x11110000+i*0x01010101 for i,r in enumerate((UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11))}
    u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP)
    for r,v in saved.items(): u.reg_write(r,v)
    u.reg_write(UC_ARM_REG_R0,obj); u.reg_write(UC_ARM_REG_R1,mode); u.reg_write(UC_ARM_REG_R2,selector)
    fault=None
    try: u.emu_start(entry,0,count=200)
    except (UcError,OSError) as e: fault=str(e)
    return {'done':st['done'],'fault':fault,'fault_pc':st['last_pc'],'r0':u.reg_read(UC_ARM_REG_R0),
            'saved_ok':all(u.reg_read(r)==v for r,v in saved.items()),'sp':u.reg_read(UC_ARM_REG_SP),
            'reads':tuple(st['reads']),'writes':tuple(st['writes']),'object':bytes(u.mem_read(obj,0x100)),
            'row':bytes(u.mem_read(row,0x40))}

def project(x, entry):
    # Return address and full-width helper-visible memory effects; ignore scratch-register choices.
    reads=tuple(((a-entry if entry<=a<entry+SPAN else a),n,v) for a,n,v in x['reads'])
    return (x['done'],x['fault'] is not None,x['r0'],x['saved_ok'],x['sp'],reads,x['writes'],x['object'],x['row'])

def main():
    OUT.mkdir(parents=True,exist_ok=True); image=IMAGE.read_bytes(); base=BASE.read_bytes()
    if sha(image)!=IMAGE_SHA or sha(base)!=BASE_SHA: raise SystemExit('pinned source image/base mismatch')
    body=compile_source('candidate.o',SOURCE)
    if len(body)>SPAN: raise AssertionError(f'body {len(body)} exceeds {SPAN}')
    padded=body+NOP*(SPAN//4-len(body)//4)
    final=bytearray(image); final[ADDR-TEXT:ADDR-TEXT+SPAN]=padded
    staged=bytearray(base); staged[ADDR-TEXT:ADDR-TEXT+SPAN]=padded
    changed=[i for i,(a,b) in enumerate(zip(base,staged)) if a!=b]
    if any(not (ADDR-TEXT<=i<ADDR-TEXT+SPAN) for i in changed): raise AssertionError('staging escaped function slot')
    ips=encode_ips([(ADDR-TEXT,padded)],len(base))
    if apply_ips(base,ips)!=bytes(staged): raise AssertionError('IPS roundtrip mismatch')
    temp=machine(image,(TEMP,padded)); old=machine(image); finalm=machine(bytes(final)); stagedm=machine(bytes(staged))
    entries=[(old,ADDR),(temp,TEMP),(finalm,ADDR),(stagedm,ADDR)]
    rng=random.Random(0x2bdac0)
    directed=[]
    for mode in (0,1,2,7,0x10000,0x80000001):
      for selector in (0,1,0x100,0xffffffff):
       directed.append((mode,selector,(-32768,-1,32767,1)))
    for _ in range(48): directed.append((rng.choice((0,1,2,7)),rng.getrandbits(32),tuple(rng.choice((-32768,-1,0,1,32767)) for _ in range(4))))
    direct_rows=[]
    for i,(mode,selector,vals) in enumerate(directed):
      results=[execute(u,e,DATA+0x1000,mode,selector,vals) for u,e in entries]
      if any(project(results[0],entries[0][1])!=project(r,e) for r,(_,e) in zip(results[1:],entries[1:])):
       raise AssertionError(f'direct mismatch case {i}: '+repr([project(x,e) for x,(_,e) in zip(results,entries)]))
      direct_rows.append({'index':i,'mode':mode,'selector':selector,'values':vals,'same':True})
    null_rows=[]
    for mode,selector in ((0,0),(1,1),(0xffff,0x100)):
      results=[execute(u,e,DATA+0x1000,mode,selector,(1,2,3,4),True) for u,e in entries]
      if any(project(results[0],entries[0][1])!=project(r,e) for r,(_,e) in zip(results[1:],entries[1:])): raise AssertionError('null-table mismatch')
      if results[0]['writes']: raise AssertionError('null table unexpectedly wrote')
      null_rows.append({'mode':mode,'selector':selector,'no_writes':True})
    # Alias case: first output store overlaps the second table halfword read.
    alias=DATA+0x3000; alias_rows=[]
    for u,e in entries:
      st=u._state; st.update(done=False,reads=[],writes=[],last_pc=None); u.mem_write(alias,bytes(0x200))
      table=alias+0x0c; u.mem_write(alias+0x4c,struct.pack('<I',table)); u.mem_write(alias+0x0c,struct.pack('<hh',0x1234,0x2345))
      u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP); u.reg_write(UC_ARM_REG_R0,alias); u.reg_write(UC_ARM_REG_R1,0); u.reg_write(UC_ARM_REG_R2,0)
      u.emu_start(e,0,count=200)
      alias_rows.append({'r0':u.reg_read(UC_ARM_REG_R0),'fields':bytes(u.mem_read(alias+0x0c,8)).hex(),'writes':tuple(st['writes'])})
    if len({json.dumps(x,sort_keys=True,default=list) for x in alias_rows})!=1: raise AssertionError(f'alias semantics differ: {alias_rows}')
    # Actual TitleConfig_Calc instruction slices that set (r0=work+0x5c,r1=1,r2=0), then BL this helper.
    caller_rows=[]
    for start,stop in ((0x001EAF2C,0x001EAF3C),(0x001EAFC8,0x001EAFD8)):
      calls=[]
      for im in (image,bytes(staged)):
       m=machine(im,stop=stop); work=DATA+0x800; obj=work+0x5c; row=DATA+0x18000
       m.mem_write(work,bytes(0x300)); m.mem_write(row,bytes(0x40)); m.mem_write(obj+0x4c,struct.pack('<I',row));
       for off,val in zip((12,14,16,18),(0x1111,0x2222,0x3333,0x4444)): m.mem_write(row+12+off-12,struct.pack('<h',val))
       # row index 1 uses this entry, selector zero reads +0/+2.
       m.reg_write(UC_ARM_REG_R5,work); m.reg_write(UC_ARM_REG_SP,STACK); m.reg_write(UC_ARM_REG_LR,STOP)
       m.emu_start(start,0,count=100)
       if not m._state['done']: raise AssertionError('caller slice did not reach post-helper stop')
       calls.append({'object':bytes(m.mem_read(obj,0x100)),'r0':m.reg_read(UC_ARM_REG_R0),'r5':m.reg_read(UC_ARM_REG_R5)})
      if calls[0]!=calls[1]: raise AssertionError(f'actual TitleConfig_Calc caller differs: {calls}')
      caller_rows.append({'slice':[hex(start),hex(stop)],'same':True,'object_after':calls[0]['object'].hex()})
    # Build two real negative controls.
    controls=[]
    original=SOURCE.read_text()
    for name,old,new,mode,selector,vals in [
      ('stride-12-to-8','mode * 12u','mode * 8u',1,0,(4,5,6,7)),
      ('full-selector-to-byte','selector == 0 ? 0u : 4u','static_cast<u8>(selector) == 0 ? 0u : 4u',1,0x100,(4,5,6,7)),
      ('second-field-offset','fields[1]','fields[2]',1,0,(4,5,6,7)),
    ]:
      if original.count(old)!=1: raise AssertionError(f'mutation anchor {name} missing')
      mutant=OUT/f'mutant-{name}.cpp'; mutant.write_text(original.replace(old,new,1))
      mb=compile_source(f'mutant-{name}.o',mutant); mu=machine(image,(TEMP+0x1000,mb+NOP*(SPAN//4-len(mb)//4)))
      orig=execute(old_machine:=entries[0][0],ADDR,DATA+0x1000,mode,selector,vals)
      mut=execute(mu,TEMP+0x1000,DATA+0x1000,mode,selector,vals)
      detected=project(orig,ADDR)!=project(mut,TEMP+0x1000)
      controls.append({'name':name,'detected':detected})
      if not detected: raise AssertionError(f'negative control escaped: {name}')
    stage_dir=OUT/'staged'; stage_dir.mkdir(exist_ok=True); imgp=stage_dir/'code.h2-002bdac0.bin'; ipsp=stage_dir/'code.h2-002bdac0.ips'; manp=stage_dir/'manifest.json'
    imgp.write_bytes(staged); ipsp.write_bytes(ips)
    manifest={'base_sha256':sha(base),'original_sha256':sha(image),'staged_sha256':sha(staged),'ips_sha256':sha(ips),'slot':hex(ADDR),'slot_bytes':SPAN,'body_bytes':len(body),'changed_bytes':len(changed),'ips_roundtrip':True,'only_declared_slot_changed':True,'runtime':'not_run'}
    manp.write_text(json.dumps(manifest,indent=2)+'\n')
    report={'image_sha256':sha(image),'base_sha256':sha(base),'source_sha256':sha(SOURCE.read_bytes()),'candidate_body_sha256':sha(body),'candidate_bytes':len(body),'slot_bytes':SPAN,'final_slot_matches_original':padded==image[ADDR-TEXT:ADDR-TEXT+SPAN],
      'direct_cases':len(direct_rows),'null_cases':null_rows,'alias_case':alias_rows,'caller_slices':caller_rows,'negative_controls':controls,
      'staged_sha256':sha(staged),'ips_sha256':sha(ips),'changed_bytes':len(changed),'only_declared_slot_changed':True,'ips_roundtrip':True,'runtime':'not_run'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
