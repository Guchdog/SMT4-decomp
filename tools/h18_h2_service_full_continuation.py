#!/usr/bin/env python3
"""Full-return offline composition through positive H2 service fields."""
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
SERVICE=0x138934; STOP=0x80f000; TEXT=0x100000; STACK=0x81ff00
OBJ=0x900100; MANAGER=0x910000; RECORDS=0x920000; ROWS=0x930000
ARRAY_A=0x940000; ARRAY_B=0x950000; SENTINELS=0x960000
NOP=struct.pack('<I',0xe320f000)
def sha(b): return hashlib.sha256(b).hexdigest()
def compile_fn(src,out,symbol):
 r=compile_tu_armv6k(src,out,ROOT)
 if r.returncode: raise RuntimeError(f'compile failed {src}: {r.stderr}')
 body,rel=extract_elf_functions_detailed(out)[symbol]
 if rel: raise AssertionError(f'{symbol} relocations: {rel}')
 if len(body)%4: raise AssertionError(f'{symbol} body not ARM-aligned: {len(body)}')
 return body,sha(out.read_bytes())
def fixture(image,bf,nest,fields):
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,0x500000); u.mem_write(TEXT,image)
 if bf is not None: u.mem_write(BF_ADDR,bf+NOP*((BF_SIZE-len(bf))//4))
 if nest is not None: u.mem_write(NEST_ADDR,nest+NOP*((NEST_SIZE-len(nest))//4))
 u.mem_map(0x800000,0x20000); u.mem_map(OBJ&~0xfff,0x70000)
 u.mem_write(OBJ,bytes(0x200)); u.mem_write(OBJ+0x48,struct.pack('<I',MANAGER)); u.mem_write(OBJ+0x4c,struct.pack('<I',ROWS))
 u.mem_write(OBJ+0x58,struct.pack('<I',ARRAY_A)); u.mem_write(OBJ+0x64,struct.pack('<I',ARRAY_B))
 mgr=bytearray(0x100); struct.pack_into('<H',mgr,6,16); struct.pack_into('<H',mgr,8,28); struct.pack_into('<I',mgr,0x18,SENTINELS); struct.pack_into('<I',mgr,0x1c,RECORDS); u.mem_write(MANAGER,bytes(mgr))
 rec=bytearray(28); struct.pack_into('<I',rec,0,1); rec[4]=0
 for off,val in ((8,fields[0]),(12,fields[1]),(20,fields[2])): struct.pack_into('<i',rec,off,val)
 rec[16]=fields[3]; rec[24]=fields[4]; u.mem_write(RECORDS,bytes(rec))
 row=bytearray(0x80); struct.pack_into('<hhhh',row,12,0x1234,-2,0x2345,-3); u.mem_write(ROWS,bytes(row))
 a=bytearray(0x100); struct.pack_into('<I',a,12,0xa1a2a3a4); struct.pack_into('<I',a,16,0xb1b2b3b4); u.mem_write(ARRAY_A,bytes(a))
 b=bytearray(0x100); struct.pack_into('<I',b,12,0xc1c2c3c4); struct.pack_into('<I',b,16,0xd1d2d3d4); u.mem_write(ARRAY_B,bytes(b))
 # One preceding -1 marker makes ordinal selector 1 select slot one (value 7).
 st=bytearray(16)
 for off,val in ((0,-1),(4,7),(8,8),(12,9)): struct.pack_into('<h',st,off,val)
 u.mem_write(SENTINELS,bytes(st))
 u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP); u.reg_write(UC_ARM_REG_R0,OBJ); u.reg_write(UC_ARM_REG_R1,0)
 saved={r:0x45670000+i for i,r in enumerate((UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11))}
 for r,v in saved.items(): u.reg_write(r,v)
 trace={'bf':0,'service':0,'nested':0,'nested_return':0,'field_a':0,'field_b':0,'field_c':0,'service_args':None,'nested_args':None,'returned':False}
 pcs={0x138980:'nested_return',0x1389a4:'field_a',0x1389fc:'field_b',0x138a48:'field_c'}
 def hook(m,pc,size,data):
  if pc==BF_ADDR: trace['bf']+=1
  if pc==SERVICE: trace['service']+=1; trace['service_args']=[m.reg_read(UC_ARM_REG_R0),m.reg_read(UC_ARM_REG_R1)]
  if pc==NEST_ADDR: trace['nested']+=1; trace['nested_args']=[m.reg_read(UC_ARM_REG_R0),m.reg_read(UC_ARM_REG_R1),m.reg_read(UC_ARM_REG_R2)]
  if pc in pcs: trace[pcs[pc]]+=1
  if pc==STOP: trace['returned']=True; m.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook); u.emu_start(BF_ADDR,0,count=10000)
 if not trace['returned']: raise AssertionError(f'service failed to return: {trace}')
 return {'trace':trace,'r0':u.reg_read(UC_ARM_REG_R0),'sp':u.reg_read(UC_ARM_REG_SP),'callee_saved_restored':all(u.reg_read(r)==v for r,v in saved.items()),'object':bytes(u.mem_read(OBJ,0x100)).hex(),'rows':bytes(u.mem_read(ROWS,0x80)).hex(),'array_a':bytes(u.mem_read(ARRAY_A,0x100)).hex(),'array_b':bytes(u.mem_read(ARRAY_B,0x100)).hex(),'sentinels':bytes(u.mem_read(SENTINELS,16)).hex()}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); args=ap.parse_args(); out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
 image=IMAGE_PATH.read_bytes()
 if sha(image)!=IMAGE_SHA: raise SystemExit('pinned original SHA mismatch')
 bf,bfh=compile_fn(BF_SRC,out/'leaf_batch41_b.o','camp_func_002bf030'); nest,nh=compile_fn(NEST_SRC,out/'leaf_batch13_c.o','camp_func_002bdac0')
 # Each tuple is (record+8, record+0xc, record+0x14, signed selector bytes +0x10/+0x18).
 scenarios={'all_positive':(1,1,1,0,1),'first_later_only':(-1,1,-1,0,0),'second_later_only':(-1,-1,1,0,1),'third_later_only':(1,-1,-1,0,0),'all_later_skipped':(-1,-1,-1,0,0)}
 results={}
 for name,fields in scenarios.items():
  old=fixture(image,None,None,fields); bf_only=fixture(image,bf,None,fields); nest_only=fixture(image,None,nest,fields); both=fixture(image,bf,nest,fields)
  for variant,row in [('bf_only',bf_only),('nested_only',nest_only),('both',both)]:
   if row!=old: raise AssertionError(f'{name}/{variant} differs from original')
  if old['trace']['nested_args']!=[OBJ,1,0] or old['trace']['returned'] is not True: raise AssertionError(f'{name}: nested ABI/return missing')
  expected={'all_positive':(1,1,1),'first_later_only':(1,0,0),'second_later_only':(0,1,0),'third_later_only':(0,0,1),'all_later_skipped':(0,0,0)}[name]
  if (old['trace']['field_a'],old['trace']['field_b'],old['trace']['field_c'])!=expected: raise AssertionError(f'{name}: wrong later field branch trace {old["trace"]}')
  if name=='all_positive' and (old['r0']!=7 or not old['callee_saved_restored']): raise AssertionError('full positive continuation did not return expected result/ABI')
  results[name]={'original':old,'bf_candidate_only':bf_only,'nested_candidate_only':nest_only,'both_candidates':both}
 # Negative control mutates a later record gate; expected to skip branch A and diverge.
 src=NEST_SRC.read_text(encoding='utf-8'); needle='const u32 first_offset = selector == 0 ? 0u : 4u;'
 if src.count(needle)!=1: raise AssertionError('negative-control anchor not unique')
 mutant_src=out/'mutant_nested_selector.cpp'; mutant_src.write_text(src.replace(needle,'const u32 first_offset = selector == 0 ? 4u : 0u;'))
 mutant,mh=compile_fn(mutant_src,out/'mutant_nested.o','camp_func_002bdac0'); mutated=fixture(image,bf,mutant,scenarios['all_positive']); detected=mutated!=results['all_positive']['original']
 if not detected: raise AssertionError('nested selector negative control escaped')
 report={'reference_sha256':sha(image),'source_sha256':{'bf030':sha(BF_SRC.read_bytes()),'bdac0':sha(NEST_SRC.read_bytes())},'object_sha256':{'bf030':bfh,'bdac0':nh,'mutant':mh},'scenario_fields':{'all_positive':{'record+8':1,'record+0xc':1,'record+0x10':0,'record+0x14':1,'record+0x18':1},'first_later_only':{'record+8':-1,'record+0xc':1,'record+0x14':-1},'second_later_only':{'record+8':-1,'record+0xc':-1,'record+0x14':1},'third_later_only':{'record+8':1,'record+0xc':-1,'record+0x14':-1},'all_later_skipped':{'record+8':-1,'record+0xc':-1,'record+0x14':-1}},'results':results,'negative_control':{'name':'swap nested zero/nonzero selector pair','detected':detected,'mutant':mutated},'passed':True,'limits':['The service returns to a synthetic LR after its complete body; the setup is a synthetic composition, not a natural H2 caller or runtime object capture.','External array pointers and sentinel table are controlled valid fixtures; malformed addresses, real table lengths, natural table contents and lifecycle are unverified.','Original service 0x00138934 remains unchanged; production candidate substitutions are limited to 0x002bf030 and 0x002bdac0.']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
if __name__=='__main__': main()
