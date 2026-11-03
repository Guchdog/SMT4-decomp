#!/usr/bin/env python3
"""Offline final-VMA differential for the paired H2 signed-byte getters."""
from __future__ import annotations

import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips,encode_ips
from tools import h2_11c5ec_experiment as reader

IMAGE_PATH=ROOT/'extracted/exefs/code.bin'
SOURCE=ROOT/'src/engine/leaf_batch21_b.cpp'
IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
CODE_BASE=0x00100000
CODE_SIZE=0x00380000
STACK=0x08000000
STACK_SIZE=0x10000
SP=STACK+0x8000
STOP=STACK+0x9000
NOP=struct.pack('<I',0xE320F000)
TARGETS={
 'func_002bb978':(0x002BB978,16,0x0044E362,0x0011C6B0),
 'func_002bc9c8':(0x002BC9C8,16,0x0044E381,0x0011C6C0),
}
SAVED=[getattr(arm,f'UC_ARM_REG_R{i}') for i in range(4,12)]

def sha(data:bytes)->str:return hashlib.sha256(data).hexdigest()

def compile_bodies(out:Path,source:Path=SOURCE):
 out.mkdir(parents=True,exist_ok=True); obj=out/'leaf_batch21_b.o'
 result=compile_tu_armv6k(source,obj,ROOT)
 if result.returncode:raise RuntimeError(result.stderr or 'production TU compile failed')
 funcs=extract_elf_functions_detailed(obj)
 bodies={}
 for name,(address,span,_global,_caller) in TARGETS.items():
  body,relocs=funcs[name]
  if relocs:raise AssertionError(f'{name} has unexpected relocations: {relocs}')
  if len(body)>span or (span-len(body))%4:raise AssertionError(f'{name} body {len(body)} does not fit {span}-byte slot')
  bodies[name]=body
 return bodies,obj

def stage(image:bytes,bodies:dict[str,bytes]):
 patches=[]; slots={}
 for name,(address,span,_global,_caller) in TARGETS.items():
  body=bodies[name]; slot=body+NOP*((span-len(body))//4); offset=address-CODE_BASE
  patches.append((offset,slot)); slots[name]=slot
 staged=bytearray(image)
 for offset,payload in patches:staged[offset:offset+len(payload)]=payload
 ips=encode_ips(patches,len(image))
 if apply_ips(image,ips)!=bytes(staged):raise AssertionError('two-slot IPS replay failed')
 changed=[i for i,(a,b) in enumerate(zip(image,staged)) if a!=b]
 allowed=[(address-CODE_BASE,address-CODE_BASE+span) for address,span,_,_ in TARGETS.values()]
 if any(not any(lo<=i<hi for lo,hi in allowed) for i in changed):raise AssertionError('staging changed bytes outside getter slots')
 return bytes(staged),slots,ips

def invoke(image:bytes,address:int,global_address:int,value:int):
 uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM|unicorn.UC_MODE_LITTLE_ENDIAN)
 uc.mem_map(CODE_BASE,CODE_SIZE);uc.mem_write(CODE_BASE,image)
 uc.mem_map(STACK,STACK_SIZE);uc.mem_write(global_address,bytes([value&0xff]))
 uc.reg_write(arm.UC_ARM_REG_SP,SP);uc.reg_write(arm.UC_ARM_REG_LR,STOP)
 for i,r in enumerate(SAVED):uc.reg_write(r,0xAB000000+i*0x01010101)
 before=[uc.reg_read(r) for r in SAVED]
 uc.hook_add(unicorn.UC_HOOK_CODE,lambda m,a,_s,_d:m.emu_stop() if a==STOP else None,begin=STOP,end=STOP)
 fault=None
 try:uc.emu_start(address,0,count=1000)
 except unicorn.UcError as exc:fault=str(exc)
 return {'fault':fault,'r0':uc.reg_read(arm.UC_ARM_REG_R0),'sp':uc.reg_read(arm.UC_ARM_REG_SP),'callee_saved':[uc.reg_read(r) for r in SAVED]==before}

def run_parent(image:bytes,index:int,flag_a:int,flag_b:int):
 case=reader.make_case(index,0,1,3,flag_a,flag_b,1,0xBB978+index)
 machine=reader.Machine(image,case['count'],case['record']);machine.setup(case)
 calls=[]
 for address in (0x002BB978,0x002BC9C8):
  machine.uc.hook_add(unicorn.UC_HOOK_CODE,lambda _m,a,_s,_d,calls=calls:calls.append(a),begin=address,end=address)
 result=machine.invoke(reader.ADDRESS,case['context'],False)
 expected=[0x002BB978]
 if flag_a!=0:expected.append(0x002BC9C8)
 if calls!=expected:raise AssertionError(f'flag call trace {calls} != {expected} for {flag_a:#x},{flag_b:#x}')
 return result,calls

def main()->int:
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 args.out.mkdir(parents=True,exist_ok=False)
 image=IMAGE_PATH.read_bytes()
 if sha(image)!=IMAGE_SHA:raise AssertionError('pinned image hash mismatch')
 bodies,obj=compile_bodies(args.out/'compile')
 staged,slots,ips=stage(image,bodies)
 (args.out/'production.o').write_bytes(obj.read_bytes());(args.out/'staged-image.bin').write_bytes(staged);(args.out/'staged-slots.ips').write_bytes(ips)
 direct=[]
 for name,(address,_span,global_address,_caller) in TARGETS.items():
  for value in range(256):
   original=invoke(image,address,global_address,value);candidate=invoke(staged,address,global_address,value)
   if original!=candidate:raise AssertionError(f'{name} direct mismatch for byte {value:#x}: {original} != {candidate}')
   expected=value if value<0x80 else value-0x100
   if candidate['r0']!=(expected&0xffffffff):raise AssertionError(f'{name} return did not sign-extend byte {value:#x}')
   direct.append({'function':name,'byte':value,'return':candidate['r0'],'equal':True})
 compositions=[]
 values=(0,1,0x7f,0x80,0xff)
 for i,a in enumerate(values):
  for j,b in enumerate(values):
   original,original_calls=run_parent(image,i*5+j,a,b);candidate,candidate_calls=run_parent(staged,i*5+j,a,b)
   if original!=candidate or original_calls!=candidate_calls:raise AssertionError(f'original reader composition mismatch for {a:#x},{b:#x}')
   compositions.append({'flag_a':a,'flag_b':b,'equal':True,'calls':[hex(x) for x in candidate_calls],
                        'short_cleared': a!=0 and b==0})
 caller_words={}
 for name,(address,_span,_global,caller) in TARGETS.items():
  word=struct.unpack_from('<I',image,caller-CODE_BASE)[0];imm=word&0xffffff
  if imm&0x800000:imm-=0x1000000
  target=caller+8+(imm<<2)
  if word&0x0f000000!=0x0b000000 or target!=address or address&1:raise AssertionError(f'{name} caller branch target invalid')
  caller_words[name]={'site':hex(caller),'word':hex(word),'target':hex(target)}
 source_text=SOURCE.read_text(encoding='utf-8');needle='reinterpret_cast<volatile s8*>(0x0044E362u)'
 if source_text.count(needle)!=1:raise AssertionError('signed-load mutation needle not unique')
 mutant=args.out/'mutant.cpp';mutant.write_text(source_text.replace(needle,'reinterpret_cast<volatile u8*>(0x0044E362u)'),encoding='utf-8')
 mutant_bodies,_mutobj=compile_bodies(args.out/'mutant-compile',mutant);mutant_image,_,_=stage(image,mutant_bodies)
 mutation_detected=invoke(image,0x002BB978,0x0044E362,0x80)!=invoke(mutant_image,0x002BB978,0x0044E362,0x80)
 if not mutation_detected:raise AssertionError('unsigned-load mutation was not detected')
 report={'status':'passed','reference_sha256':sha(image),'production_source_sha256':sha(SOURCE.read_bytes()),
         'production_object_sha256':sha(obj.read_bytes()),'body_sha256':{n:sha(bodies[n]) for n in bodies},
         'body_sizes':{n:len(bodies[n]) for n in bodies},'slot_sizes':{n:TARGETS[n][1] for n in TARGETS},
         'relocations':{n:[] for n in TARGETS},'callers':caller_words,'direct_case_count':len(direct),
         'direct_differences':0,'parent_composition_case_count':len(compositions),'parent_composition_differences':0,
         'parent_compositions':compositions,'negative_control':{'unsigned_first_getter':mutation_detected},
         'ips_roundtrip':apply_ips(image,ips)==staged,'ips_sha256':sha(ips),'staged_image_sha256':sha(staged),
         'domain':'ordinary mapped globals; direct raw returns cover all byte values; parent composition uses controlled ring-reader seam and synthetic ordinary RAM; runtime input provenance unproven'}
 (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print('PASS direct=512 parent=25 mutation=detected bodies='+','.join(f'{k}:{len(v)}/16' for k,v in bodies.items()))
 return 0

if __name__=='__main__':raise SystemExit(main())
