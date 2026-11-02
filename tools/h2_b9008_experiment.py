#!/usr/bin/env python3
"""Final-VMA differential for the shared H2 manager halfword helper."""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips,encode_ips
IMAGE=ROOT/'extracted/exefs/code.bin';IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
SOURCE=ROOT/'src/engine/leaf_batch23_b.cpp';ADDR=0x002B9008;SLOT=36;CODE=0x00100000;CODE_SIZE=0x00380000
GLOBAL=0x0043DCB0;MANAGER=0x00500000;DATA_SIZE=0x2000;COUNTER=MANAGER+0x64A
STACK=0x08000000;STACK_SIZE=0x10000;SP=STACK+0x8000;STOP=STACK+0x9000;INJECT=0x01000000;INJECT_SIZE=0x1000;U32=0xFFFFFFFF

def sha(b):return hashlib.sha256(b).hexdigest()
def compile_body(out,source=SOURCE):
 out.mkdir(parents=True,exist_ok=True);obj=out/'leaf_batch23_b.o';r=compile_tu_armv6k(source,obj,ROOT)
 if r.returncode:raise RuntimeError(r.stderr or 'TU compile failed')
 body,relocs=extract_elf_functions_detailed(obj)['camp_func_002b9008']
 if relocs:raise ValueError(f'unexpected relocations: {relocs}')
 return body,list(r.args),obj

def stage(original,body):
 if len(body)>SLOT:raise ValueError(f'body {len(body)} exceeds {SLOT}-byte slot')
 if len(body)%4:raise ValueError('ARM body alignment')
 payload=body+struct.pack('<I',0xE320F000)*((SLOT-len(body))//4)
 staged=bytearray(original);off=ADDR-CODE;staged[off:off+SLOT]=payload
 return bytes(staged),payload

class Machine:
 def __init__(self,image,initial,seed,input_regs=(0,0,0,0),injected=None):
  self.uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM|unicorn.UC_MODE_LITTLE_ENDIAN)
  self.uc.mem_map(CODE,CODE_SIZE);self.uc.mem_write(CODE,image)
  if injected is not None:
   if len(injected)>INJECT_SIZE:raise ValueError('mutant exceeds injection page')
   self.uc.mem_map(INJECT,INJECT_SIZE);self.uc.mem_write(INJECT,injected)
  self.uc.mem_map(MANAGER,DATA_SIZE);self.uc.mem_map(STACK,STACK_SIZE)
  self.writes=[];self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,self._write)
  self.uc.hook_add(unicorn.UC_HOOK_CODE,self._stop,begin=STOP,end=STOP)
  rng=random.Random(seed);self.manager_bytes=bytes(rng.randrange(256) for _ in range(DATA_SIZE))
  buf=bytearray(self.manager_bytes);struct.pack_into('<h',buf,0x64A,initial);self.manager_bytes=bytes(buf)
  self.uc.mem_write(MANAGER,self.manager_bytes)
  self.uc.mem_write(GLOBAL,struct.pack('<II',0x12345678,MANAGER))
  self.input_regs=input_regs
 def _write(self,uc,_access,address,size,value,_data):self.writes.append((address,size,value&U32))
 @staticmethod
 def _stop(uc,_address,_size,_data):uc.emu_stop()
 def run_at(self,entry):
  regs=[getattr(arm,f'UC_ARM_REG_R{i}') for i in range(13)]
  init=[(0xC1000000+i*0x01010101)&U32 for i in range(13)]
  for r,v in zip(regs,init):self.uc.reg_write(r,v)
  self.uc.reg_write(arm.UC_ARM_REG_R0,self.input_regs[0]&U32)
  for i in range(1,4):self.uc.reg_write(getattr(arm,f'UC_ARM_REG_R{i}'),self.input_regs[i]&U32)
  self.uc.reg_write(arm.UC_ARM_REG_SP,SP);self.uc.reg_write(arm.UC_ARM_REG_LR,STOP)
  fault=None
  try:self.uc.emu_start(entry,0,count=2000)
  except unicorn.UcError as e:fault=str(e)
  after=[self.uc.reg_read(r) for r in regs]
  return {'fault':fault,'r0':self.uc.reg_read(arm.UC_ARM_REG_R0),'sp':self.uc.reg_read(arm.UC_ARM_REG_SP),
   'callee_saved':after[4:12]==init[4:12], 'manager':bytes(self.uc.mem_read(MANAGER,DATA_SIZE)).hex(),
   'global':bytes(self.uc.mem_read(GLOBAL,8)).hex(),'writes':self.writes.copy()}

def execute(image,initial,seed,input_regs,injected=None):
 m=Machine(image,initial,seed,input_regs,injected)
 entry=INJECT if injected is not None else ADDR
 return m.run_at(entry)

def compile_mutant(out,label,before,after):
 text=SOURCE.read_text(encoding='utf-8')
 if text.count(before)!=1:raise ValueError(f'{label} source needle not unique')
 p=out/'mutants'/f'{label}.cpp';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text.replace(before,after),encoding='utf-8')
 body,_args,_obj=compile_body(out/'mutants'/f'{label}-compile',p);return body

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seed',type=int,default=20261118);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True)
 original=IMAGE.read_bytes()
 if sha(original)!=IMAGE_SHA:raise SystemExit('pinned original image hash mismatch')
 body,compiler_args,obj=compile_body(args.out/'compile');staged,payload=stage(original,body);off=ADDR-CODE
 ips=encode_ips([(off,payload)],len(original))
 if apply_ips(original,ips)!=staged:raise AssertionError('IPS replay mismatch')
 (args.out/'staged-image.bin').write_bytes(staged);(args.out/'staged-slot.ips').write_bytes(ips)
 cases=[];signed_values=(-32768,-1,0,9,10,11,12,32767);incoming=(0,1,0xDEADBEEF,MANAGER)
 for i,v in enumerate(signed_values):
  for j,r0 in enumerate(incoming):cases.append({'value':v,'r0':r0,'regs':(r0,0xA0000000+i,0xB0000000+j,0xC0000000+i+j),'case_seed':args.seed+i*101+j})
 mismatches=[];summaries=[]
 for n,c in enumerate(cases):
  ref=execute(original,c['value'],c['case_seed'],c['regs']);got=execute(staged,c['value'],c['case_seed'],c['regs'])
  equal=ref==got
  if not equal:mismatches.append({'case':n,'input':c,'original':ref,'candidate':got})
  expected=c['value']-1 if c['value']>10 else c['value']
  ref_after=struct.unpack('<h',bytes.fromhex(ref['manager'])[0x64A:0x64C])[0]
  got_after=struct.unpack('<h',bytes.fromhex(got['manager'])[0x64A:0x64C])[0]
  behavior_ok=ref_after==expected and got_after==expected and ref['global']==got['global']
  if not behavior_ok:mismatches.append({'case':n,'reason':'expected signed-threshold effect failed','expected':expected,'original':ref,'candidate':got})
  summaries.append({'case':n,'initial':c['value'],'expected_after':expected,'r0_in':hex(c['r0']),'equal':equal,
   'behavior_ok':behavior_ok,'counter_after':got_after,'writes':got['writes'],'raw_r0':hex(got['r0'])})
 mutants={'lower_threshold':('value > 10','value > 9',10),
          'wrong_halfword_offset':('manager_base + 0x4Au','manager_base + 0x48u',11)}
 controls={}
 for label,(before,after,value) in mutants.items():
  mutant=compile_mutant(args.out,label,before,after)
  regs=(0xDEC0ADDE,1,2,3);seed=args.seed+9900+value
  ref=execute(original,value,seed,regs);got=execute(original,value,seed,regs,mutant)
  controls[label]={'detected':ref!=got,'original':ref,'mutant':got}
 fixture_digest=sha(json.dumps(cases,sort_keys=True,separators=(',',':')).encode())
 slot_only=original[:off]==staged[:off] and original[off+SLOT:]==staged[off+SLOT:]
 report={'image_sha256':sha(original),'source_sha256':sha(SOURCE.read_bytes()),'fixture_sha256':fixture_digest,
  'seed':args.seed,'body_bytes':len(body),'slot_bytes':SLOT,'body_sha256':sha(body),
  'body_byte_identical':original[off:off+SLOT]==payload,'relocations':[],
  'entry_bit0':ADDR&1,'compiler_args':compiler_args,'direct_cases':len(cases),'mismatches':mismatches,
  'case_summary':summaries,'mutation_controls':controls,'exact_slot_ips_replay':apply_ips(original,ips)==staged,
  'only_slot_changed':slot_only,'all_passed':len(body)<=SLOT and not mismatches and slot_only and all(x['detected'] for x in controls.values()) and all(x['behavior_ok'] for x in summaries),
  'scope':'valid mapped ordinary memory with global+4 manager pointer; function ignores incoming arguments; no caller-specific scheduler/MMIO assumptions'}
 (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'all_passed':report['all_passed'],'body_bytes':len(body),'direct_cases':len(cases),'mismatches':len(mismatches),'mutations_detected':sum(x['detected'] for x in controls.values()),'report':str(args.out/'report.json')}))
 return 0 if report['all_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
