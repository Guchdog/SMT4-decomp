#!/usr/bin/env python3
"""Offline final-VMA differential for the H2 unsigned input-mode byte getter."""
from __future__ import annotations
import argparse, hashlib, json, struct, sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools import h2_11c5ec_experiment as reader
IMAGE=ROOT/'extracted/exefs/code.bin'
SOURCE=ROOT/'src/engine/leaf_batch21_a.cpp'
IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
ADDRESS=0x00138F34; SLOT=16; GLOBAL=0x0047388B
CODE_BASE=0x00100000; CODE_SIZE=0x00380000
STACK=0x08000000; STACK_SIZE=0x10000; SP=STACK+0x8000; STOP=STACK+0x9000
NOP=struct.pack('<I',0xE320F000)
SAVED=[getattr(arm,f'UC_ARM_REG_R{i}') for i in range(4,12)]
def sha(b):return hashlib.sha256(b).hexdigest()
def compile_body(out:Path,source=SOURCE):
 out.mkdir(parents=True,exist_ok=True);obj=out/'leaf_batch21_a.o'
 result=compile_tu_armv6k(source,obj,ROOT)
 if result.returncode:raise RuntimeError(result.stderr or 'production TU compile failed')
 body,relocs=extract_elf_functions_detailed(obj)['func_00138f34']
 if relocs:raise AssertionError(f'unexpected relocations {relocs}')
 if len(body)>SLOT or (SLOT-len(body))%4:raise AssertionError(f'body does not fit {SLOT}-byte slot: {len(body)}')
 return body,obj

def stage(image,body):
 payload=body+NOP*((SLOT-len(body))//4);offset=ADDRESS-CODE_BASE
 staged=bytearray(image);staged[offset:offset+SLOT]=payload
 ips=encode_ips([(offset,payload)],len(image))
 if apply_ips(image,ips)!=bytes(staged):raise AssertionError('IPS replay mismatch')
 changed=[i for i,(a,b) in enumerate(zip(image,staged)) if a!=b]
 if any(not offset<=i<offset+SLOT for i in changed):raise AssertionError('changed bytes outside mode getter')
 return bytes(staged),payload,ips

def invoke(image,value):
 uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM|unicorn.UC_MODE_LITTLE_ENDIAN)
 uc.mem_map(CODE_BASE,CODE_SIZE);uc.mem_write(CODE_BASE,image)
 uc.mem_map(STACK,STACK_SIZE);uc.mem_write(GLOBAL,bytes([value&255]))
 uc.reg_write(arm.UC_ARM_REG_SP,SP);uc.reg_write(arm.UC_ARM_REG_LR,STOP)
 for i,r in enumerate(SAVED):uc.reg_write(r,0xA5000000+i*0x01010101)
 saved=[uc.reg_read(r) for r in SAVED]
 uc.hook_add(unicorn.UC_HOOK_CODE,lambda m,a,_s,_d:m.emu_stop() if a==STOP else None,begin=STOP,end=STOP)
 fault=None
 try:uc.emu_start(ADDRESS,0,count=1000)
 except unicorn.UcError as e:fault=str(e)
 return {'fault':fault,'return':uc.reg_read(arm.UC_ARM_REG_R0),'sp':uc.reg_read(arm.UC_ARM_REG_SP),'callee_saved':[uc.reg_read(r) for r in SAVED]==saved}

def parent(image,index,mode,count):
 case=reader.make_case(index,mode,count,1,0,0,1,0x138F34+index)
 machine=reader.Machine(image,case['count'],case['record']);machine.setup(case);calls=[]
 machine.uc.hook_add(unicorn.UC_HOOK_CODE,lambda _m,a,_s,_d:calls.append(a),begin=ADDRESS,end=ADDRESS)
 result=machine.invoke(reader.ADDRESS,case['context'],False)
 if calls != [ADDRESS]:raise AssertionError(f'getter call trace {calls} for mode={mode:#x}')
 if bool(result['ring_calls']) != (mode!=4):raise AssertionError(f'mode gate ring behavior wrong for {mode:#x}')
 return result,calls

def branch_target(image,site):
 word=struct.unpack_from('<I',image,site-CODE_BASE)[0]
 if word&0x0F000000!=0x0B000000:raise AssertionError(f'{site:#x} is not ARM BL: {word:#x}')
 imm=word&0xffffff
 if imm&0x800000:imm-=0x1000000
 return word,site+8+(imm<<2)

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 args.out.mkdir(parents=True,exist_ok=False)
 image=IMAGE.read_bytes()
 if sha(image)!=IMAGE_SHA:raise AssertionError('pinned input image hash mismatch')
 body,obj=compile_body(args.out/'compile');staged,payload,ips=stage(image,body)
 (args.out/'staged-image.bin').write_bytes(staged);(args.out/'staged-slot.ips').write_bytes(ips);(args.out/'production.o').write_bytes(obj.read_bytes())
 direct=[]
 for value in range(256):
  ref=invoke(image,value);got=invoke(staged,value)
  if ref!=got:raise AssertionError(f'direct mismatch at {value:#x}: {ref} != {got}')
  if got['return']!=value:raise AssertionError(f'unsigned raw return mismatch at {value:#x}')
  if got['fault'] is not None or got['sp']!=SP or not got['callee_saved']:raise AssertionError(f'ABI/fault at {value:#x}: {got}')
  direct.append({'byte':value,'return':got['return']})
 compositions=[]
 for i,mode in enumerate((0,3,4,5,0x7f,0x80,0xff)):
  for count in (0,1):
   ref,rc=parent(image,i*2+count,mode,count);got,gc=parent(staged,i*2+count,mode,count)
   if ref!=got or rc!=gc:raise AssertionError(f'reader mismatch mode={mode:#x},count={count}')
   compositions.append({'mode':mode,'count':count,'equal':True,'return':got['return'],'ring_calls':len(got['ring_calls'])})
 caller_word,caller_target=branch_target(image,0x00128C30)
 if caller_target!=ADDRESS or caller_target&1:raise AssertionError(f'wrapper BL target {caller_target:#x}')
 reader_targets=[]
 for off in range(reader.SLOT_SIZE-4):
  site=reader.ADDRESS+off
  word,target=branch_target(image,site) if struct.unpack_from('<I',image,site-CODE_BASE)[0]&0x0F000000==0x0B000000 else (None,None)
  if target==0x00128C2C:reader_targets.append({'site':hex(site),'word':hex(word)})
 if not reader_targets:raise AssertionError('reader has no BL to 0x00128C2C')
 text=SOURCE.read_text(encoding='utf-8');needle='reinterpret_cast<volatile u8*>(0x0047388Bu)'
 if text.count(needle)!=1:raise AssertionError('unsigned-load mutation needle is not unique')
 mutant=args.out/'signed-mutant.cpp';mutant.write_text(text.replace(needle,'reinterpret_cast<volatile s8*>(0x0047388Bu)'),encoding='utf-8')
 mutant_body,_=compile_body(args.out/'mutant-compile',mutant);mutant_image,_,_=stage(image,mutant_body)
 mutation=invoke(image,0x80)!=invoke(mutant_image,0x80)
 if not mutation:raise AssertionError('signed-byte mutation was not detected')
 report={'status':'passed','image_sha256':sha(image),'source_sha256':sha(SOURCE.read_bytes()),'object_sha256':sha(obj.read_bytes()),'body_sha256':sha(body),'body_bytes':len(body),'slot_bytes':SLOT,'relocations':[],'direct_case_count':len(direct),'direct_differences':0,'parent_composition_case_count':len(compositions),'parent_composition_differences':0,'parent_compositions':compositions,'wrapper_call':{'site':'0x00128c30','word':hex(caller_word),'target':hex(caller_target)},'reader_calls_to_wrapper':reader_targets,'mutation_signed_load_detected':mutation,'ips_sha256':sha(ips),'staged_image_sha256':sha(staged),'ips_replay':apply_ips(image,ips)==staged,'scope':'ordinary mapped global byte; original wrapper and other reader dependencies; synthetic reader memory and controlled ring-reader seam'}
 (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(f'PASS direct={len(direct)} reader={len(compositions)} body={len(body)}/{SLOT} mutation=detected')
 return 0
if __name__=='__main__':raise SystemExit(main())
