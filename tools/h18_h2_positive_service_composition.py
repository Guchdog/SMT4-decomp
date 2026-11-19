#!/usr/bin/env python3
"""Offline positive-record composition through original 0x00138934."""
from __future__ import annotations
import argparse, hashlib, json, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
IMAGE_PATH=ROOT/'extracted/exefs/code.bin'; IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
BF_SRC=ROOT/'src/engine/leaf_batch41_b.cpp'; NEST_SRC=ROOT/'src/engine/leaf_batch13_c.cpp'
BF_ADDR=0x2bf030; BF_SIZE=120; NEST_ADDR=0x2bdac0; NEST_SIZE=108
SERVICE=0x138934; NEST_CALL_RETURN=0x138980; STOP=0x80f000
TEXT=0x100000; DATA=0x900000; MANAGER=0x910000; RECORDS=0x920000; ROWS=0x930000; STACK=0x81ff00
NOP=struct.pack('<I',0xe320f000)
def sha(data): return hashlib.sha256(data).hexdigest()
def compile_fn(src,out,symbol):
 r=compile_tu_armv6k(src,out,ROOT)
 if r.returncode: raise RuntimeError(f'compile failed {src}: {r.stderr}')
 funcs=extract_elf_functions_detailed(out)
 if symbol not in funcs: raise AssertionError(f'{symbol} absent from {out}')
 body,rel=funcs[symbol]
 if rel: raise AssertionError(f'{symbol} has relocations: {rel}')
 if len(body)%4: raise AssertionError(f'{symbol} body size is not ARM-word aligned: {len(body)}')
 return body,sha(out.read_bytes())
def execute(image,bf_body=None,nest_body=None,index_value=1,selector=0):
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,0x500000); u.mem_write(TEXT,image)
 if bf_body is not None: u.mem_write(BF_ADDR,bf_body+NOP*((BF_SIZE-len(bf_body))//4))
 if nest_body is not None: u.mem_write(NEST_ADDR,nest_body+NOP*((NEST_SIZE-len(nest_body))//4))
 u.mem_map(0x800000,0x20000); u.mem_map(DATA,0x50000)
 obj=DATA+0x100; u.mem_write(obj,bytes(0x200)); u.mem_write(obj+0x48,struct.pack('<I',MANAGER)); u.mem_write(obj+0x4c,struct.pack('<I',ROWS))
 mgr=bytearray(0x100); struct.pack_into('<H',mgr,8,28); struct.pack_into('<I',mgr,0x1c,RECORDS); u.mem_write(MANAGER,bytes(mgr))
 rec=bytearray(28); struct.pack_into('<I',rec,0,index_value); rec[4]=selector&0xff; u.mem_write(RECORDS,bytes(rec))
 row=bytearray(0x80); struct.pack_into('<hhhh',row,12,0x1234,-2,0x2345,-3); u.mem_write(ROWS,bytes(row))
 u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP); u.reg_write(UC_ARM_REG_R0,obj); u.reg_write(UC_ARM_REG_R1,0)
 saved={r:0x45670000+i for i,r in enumerate((UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11))}
 for r,v in saved.items(): u.reg_write(r,v)
 trace={'bf':0,'service':0,'nested':0,'stop':False,'service_args':None,'nested_args':None}
 def hook(m,a,size,d):
  if a==BF_ADDR: trace['bf']+=1
  if a==SERVICE:
   trace['service']+=1; trace['service_args']=[m.reg_read(UC_ARM_REG_R0),m.reg_read(UC_ARM_REG_R1)]
  if a==NEST_ADDR:
   trace['nested']+=1; trace['nested_args']=[m.reg_read(UC_ARM_REG_R0),m.reg_read(UC_ARM_REG_R1),m.reg_read(UC_ARM_REG_R2)]
  if a==NEST_CALL_RETURN: trace['stop']=True; m.emu_stop()
  if a==STOP: m.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook); u.emu_start(BF_ADDR,0,count=5000)
 if not trace['stop']: raise AssertionError(f'positive path did not return from nested helper: {trace}')
 return {'trace':trace,'r0':u.reg_read(UC_ARM_REG_R0),'sp':u.reg_read(UC_ARM_REG_SP),'registers_at_nested_return':{str(r):u.reg_read(r) for r in saved},'object':bytes(u.mem_read(obj,0x100)).hex(),'rows':bytes(u.mem_read(ROWS,0x80)).hex()}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
 image=IMAGE_PATH.read_bytes()
 if sha(image)!=IMAGE_SHA: raise SystemExit('pinned original SHA mismatch')
 bfo,bfh=compile_fn(BF_SRC,out/'leaf_batch41_b.o','camp_func_002bf030'); neo,neh=compile_fn(NEST_SRC,out/'leaf_batch13_c.o','camp_func_002bdac0')
 old=execute(image); bf_only=execute(image,bfo); nested_only=execute(image,None,neo); both=execute(image,bfo,neo)
 expected_args=[DATA+0x100,RECORDS]
 if old['trace']['service_args']!=expected_args or old['trace']['nested_args']!=[DATA+0x100,1,0]: raise AssertionError(f'original positive branch has unexpected ABI args: {old["trace"]}')
 for name,row in [('bf_only',bf_only),('nested_only',nested_only),('both',both)]:
  if row!=old: raise AssertionError(f'{name} differs from original: {row} != {old}')
 nonzero=execute(image,bfo,neo,index_value=1,selector=1)
 if nonzero['trace']['nested']!=1 or nonzero['trace']['nested_args']!=[DATA+0x100,1,1]: raise AssertionError('nonzero nested selector did not reach helper with expected ABI')
 # Mutation swaps the zero/nonzero table-pair selection in the nested candidate.
 src=NEST_SRC.read_text(encoding='utf-8'); needle='const u32 first_offset = selector == 0 ? 0u : 4u;'
 if src.count(needle)!=1: raise AssertionError('negative-control mutation anchor not unique')
 mut_src=out/'mutant_nested_selector.cpp'; mut_src.write_text(src.replace(needle,'const u32 first_offset = selector == 0 ? 4u : 0u;'))
 mut_body,mh=compile_fn(mut_src,out/'mutant_nested.o','camp_func_002bdac0'); mutant=execute(image,bfo,mut_body)
 detected=mutant!=old
 if not detected: raise AssertionError('nested-selector negative control escaped')
 report={'reference_sha256':sha(image),'sources':{'bf030':sha(BF_SRC.read_bytes()),'bdac0':sha(NEST_SRC.read_bytes())},'objects':{'bf030':bfh,'bdac0':neh,'mutant':mh},'addresses':{'bf030':hex(BF_ADDR),'service':hex(SERVICE),'nested':hex(NEST_ADDR),'nested_return':hex(NEST_CALL_RETURN)},'positive_fixture':{'record_first_word':1,'record_selector_byte':0,'scan_count':1,'manager_n':28,'nested_index':1,'nested_selector':0,'row_values':['0x1234','-2','0x2345','-3']},'original':old,'bf_candidate_only':bf_only,'nested_candidate_only':nested_only,'both_candidates':both,'nonzero_nested_selector':nonzero,'negative_control':{'name':'swap nested zero/nonzero selector pair','detected':detected,'result':mutant},'passed':True,'limitations':['Execution stops immediately after the nested helper returns at 0x00138980; later service logic and dependencies are excluded.','The fixture is synthetic ordinary RAM; it does not establish a natural caller or complete H2 transition.','Original service 0x00138934 is retained; only 0x002bf030 and 0x002bdac0 are replaced in candidate variants.']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
