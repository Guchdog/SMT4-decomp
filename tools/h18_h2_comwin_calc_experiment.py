#!/usr/bin/env python3
"""Offline differential for callback sub-entry 0x0011b094."""
from __future__ import annotations
import argparse, hashlib, json, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
IMAGE_PATH=ROOT/'extracted/exefs/code.bin'; IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
SOURCE=ROOT/'experiments/semantic_equivalence/h18_h2_comwin_calc.cpp'
ADDR=0x0011b094; SPAN=148; WIDGET=0x002bf9f0; GLOBAL=0x0043e0f8
TEXT=0x00100000; WORK=0x00900000; STACK=0x0081ff00; STOP=0x0080f000
NOP=struct.pack('<I',0xe320f000); MASK=0xffffffff
CALLEE=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
def sha(data): return hashlib.sha256(data).hexdigest()
def compile_source(path,out):
 r=compile_tu_armv6k(path,out,ROOT)
 if r.returncode: raise RuntimeError(r.stderr)
 funcs=extract_elf_functions_detailed(out)
 body,rel=funcs['h18_h2_comwin_calc_candidate']
 if rel: raise AssertionError(f'unexpected relocations: {rel}')
 if len(body)>SPAN or len(body)%4: raise AssertionError(f'candidate size/alignment invalid: {len(body)}')
 return body
def execute(image,body,fixture):
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,0x500000); u.mem_write(TEXT,image)
 if body is not None: u.mem_write(ADDR,body+NOP*((SPAN-len(body))//4))
 u.mem_map(0x800000,0x20000); u.mem_map(WORK,0x1000)
 raw=bytearray((i*53+fixture['state']*17+fixture['counter'])&255 for i in range(0x200))
 struct.pack_into('<I',raw,8,fixture['state']&MASK); struct.pack_into('<I',raw,0x0c,fixture['counter']&MASK)
 u.mem_write(WORK,bytes(raw)); u.mem_write(GLOBAL,struct.pack('<I',WORK))
 u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP)
 for i,r in enumerate(CALLEE): u.reg_write(r,0x11220000+i)
 u.reg_write(UC_ARM_REG_R0,0xdeadbeef); u.reg_write(UC_ARM_REG_R1,0x22334455); u.reg_write(UC_ARM_REG_R2,0x55667788); u.reg_write(UC_ARM_REG_R3,0x99aabbcc)
 saved={r:u.reg_read(r) for r in CALLEE}; trace={'calls':[],'returned':False}
 def hook(m,pc,size,data):
  if pc==WIDGET:
   arg=m.reg_read(UC_ARM_REG_R0); call={'arg':arg,'result':fixture['helper_result']&MASK}
   trace['calls'].append(call)
   # Explicit optional helper writes exercise caller reload/store ordering.
   for off,value in fixture.get('helper_writes',{}).items():
    value=int(value,0) if isinstance(value,str) else value
    m.mem_write(arg-(0x3c if arg==WORK+0x3c else 0xc8)+int(off,0),struct.pack('<I',value&MASK))
   m.reg_write(UC_ARM_REG_R0,fixture['helper_result']&MASK)
   m.reg_write(UC_ARM_REG_PC,m.reg_read(UC_ARM_REG_LR))
  elif pc==STOP:
   trace['returned']=True; m.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook); u.emu_start(ADDR,0,count=2000)
 if not trace['returned']: raise AssertionError(f'callback failed to return, state={fixture}')
 return {'return':u.reg_read(UC_ARM_REG_R0),'sp':u.reg_read(UC_ARM_REG_SP),'callee_saved':{str(r):u.reg_read(r) for r in CALLEE},'callee_saved_preserved':all(u.reg_read(r)==v for r,v in saved.items()),'work':bytes(u.mem_read(WORK,0x200)).hex(),'trace':trace}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args(); out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
 image=IMAGE_PATH.read_bytes()
 if sha(image)!=IMAGE_SHA: raise SystemExit('pinned image SHA mismatch')
 body=compile_source(SOURCE,out/'candidate.o')
 # The callback body is interior to a compound 0x0011ae10 span. Keep this validation private.
 pool={hex(a):hex(struct.unpack_from('<I',image,a-TEXT)[0]) for a in (0x11b0b4,0x11b0b8,0x11b0bc,0x11b0c0,0x11b0c4,0x11b124)}
 expected={'0x11b0b4':'0x11b110','0x11b0b8':'0x11b0c8','0x11b0bc':'0x11b0ec','0x11b0c0':'0x11b110','0x11b0c4':'0x11b100','0x11b124':'0x43e0f8'}
 if pool!=expected: raise AssertionError(f'entry literal/jump table boundary mismatch: {pool}')
 fixtures=[]
 for state in (0,1,2,3,4,5,0xffffffff):
  for result in (0,1,0xffffffff):
   fixtures.append({'state':state,'counter':0x12345678,'helper_result':result})
 fixtures += [
  {'state':1,'counter':0xfffffffe,'helper_result':1},
  {'state':1,'counter':40,'helper_result':0,'helper_writes':{'0xc':'0xfffffffe','0x8':9}},
  {'state':1,'counter':40,'helper_result':1,'helper_writes':{'0xc':77,'0x8':9}},
  {'state':2,'counter':40,'helper_result':0,'helper_writes':{'0xc':'0xffffffff','0x8':4}},
  {'state':4,'counter':40,'helper_result':0,'helper_writes':{'0xc':2,'0x8':7}},
  {'state':4,'counter':40,'helper_result':1,'helper_writes':{'0xc':2,'0x8':7}},
 ]
 rows=[]
 for i,f in enumerate(fixtures):
  old=execute(image,None,f); new=execute(image,body,f)
  if old!=new: raise AssertionError(f'differential mismatch case {i} {f}: {old} != {new}')
  rows.append({'case':i,'fixture':f,'matched':True,'helper_calls':old['trace']['calls']})
 # Mutate the state-1 condition; a result=1 positive case must distinguish it.
 source=SOURCE.read_text(encoding='utf-8'); needle='if (widget_calc(const_cast<uint8_t*>(work + 0x3cu)) != 0) {'
 if source.count(needle)!=2: raise AssertionError('mutation anchor count changed')
 mutant_src=out/'mutant.cpp'; mutant_src.write_text(source.replace(needle,'if (widget_calc(const_cast<uint8_t*>(work + 0x3cu)) == 0) {',1))
 mutant_body=compile_source(mutant_src,out/'mutant.o'); control={'state':1,'counter':3,'helper_result':1}
 negative=execute(image,None,control); mutant=execute(image,mutant_body,control); detected=negative!=mutant
 if not detected: raise AssertionError('state transition negative control escaped')
 report={'reference_sha256':sha(image),'source_sha256':sha(SOURCE.read_bytes()),'candidate_body_sha256':sha(body),'candidate_bytes':len(body),'overlapping_span':{'owner':'InfoWin_DrawUp','start':'0x0011ae10','size':792,'subentry':'0x0011b094','subentry_size':SPAN,'patched_or_ledger_changed':False},'literal_table_words':pool,'fixtures':len(fixtures),'results':rows,'negative_control':{'name':'invert state-1 helper result gate','detected':detected,'original':negative,'mutant':mutant},'helper_model':'At 0x002bf9f0 the runner records r0, optionally applies explicit writes relative to the widget work base, returns the configured r0, and resumes at LR. No helper implementation effects are inferred.','caller':{'registration':'ComWin_Init registers callback address 0x0011b094 under ComWin Calc per static reconstruction record.','runtime_or_init_composition':'not_run'},'passed':True,'limitations':['Synthetic work object and explicit helper stub; widget internals, object lifetime and actual UI scheduling are not covered.','Direct callback invocation uses a synthetic LR; registration setup and natural task caller composition were not executed.','0x0011b094 lies inside the 792-byte InfoWin_DrawUp ledger/source span. This task makes no production span, source placeholder, ledger or IPS change.']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'passed':True,'candidate_bytes':len(body),'fixtures':len(fixtures),'negative_control':detected,'literal_table_words':pool},indent=2))
if __name__=='__main__': main()
