#!/usr/bin/env python3
"""Direct pinned ARM differential for the H2 input ring reader."""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips,encode_ips
from tools import h2_11c5ec_experiment as reader
from tools import h2_input_mode_wrapper_experiment as mode_patch
IMAGE=ROOT/'extracted/exefs/code.bin';SOURCE=ROOT/'src/engine/leaf_batch16_c.cpp'
IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
ADDRESS=0x0012A758;SLOT=424;BASE=0x00100000;CODE_SIZE=0x00380000
DATA=0x00500000;DATA_SIZE=0x00040000;SP_BASE=0x08000000;SP_SIZE=0x10000;SP=SP_BASE+0x8000;STOP=SP_BASE+0x9000
SRC=DATA+0x10000;OUT=DATA+0x20000;COUNT=DATA+0x30000;CURSOR=DATA+0x30010;INDEX=DATA+0x30020
U32=0xffffffff;U64=0xffffffffffffffff;NOP=struct.pack('<I',0xE320F000)
SAVED=[getattr(arm,f'UC_ARM_REG_R{i}') for i in range(4,12)]
def sha(b):return hashlib.sha256(b).hexdigest()
def compile_body(out,source=SOURCE):
 out.mkdir(parents=True,exist_ok=True);obj=out/'leaf_batch16_c.o';res=compile_tu_armv6k(source,obj,ROOT)
 if res.returncode:raise RuntimeError(res.stderr or 'production TU compile failed')
 body,relocs=extract_elf_functions_detailed(obj)['func_0012a758']
 if len(body)>SLOT or (SLOT-len(body))%4:raise AssertionError(f'body {len(body)} does not fit {SLOT}-byte slot')
 if relocs:raise AssertionError(f'unexpected ring reader relocations: {relocs}')
 return body,obj

def stage(image,body):
 payload=body+NOP*((SLOT-len(body))//4);off=ADDRESS-BASE
 staged=bytearray(image);staged[off:off+SLOT]=payload;ips=encode_ips([(off,payload)],len(image))
 if apply_ips(image,ips)!=bytes(staged):raise AssertionError('ring IPS replay mismatch')
 if image[:off]!=staged[:off] or image[off+SLOT:]!=staged[off+SLOT:]:raise AssertionError('ring patch escaped its 424-byte slot')
 return bytes(staged),payload,ips

def fixture(request,effective,pair0,pair1,cursor,index,seed):
 rng=random.Random(seed);source=bytearray(rng.randrange(256) for _ in range(0xB0))
 struct.pack_into('<Q',source,0,pair0&U64);struct.pack_into('<Q',source,8,pair1&U64);struct.pack_into('<I',source,0x10,effective&U32)
 for slot in range(8):
  record=struct.pack('<IIIHH',*(rng.getrandbits(32) for _ in range(3)),rng.getrandbits(16),rng.getrandbits(16))
  source[0x28+slot*16:0x38+slot*16]=record
 output=bytes(rng.randrange(256) for _ in range(0x100))
 return {'request':request,'effective':effective,'pair0':pair0&U64,'pair1':pair1&U64,'cursor':cursor&U64,'index':index&U32,'source':bytes(source),'output':output,'seed':seed}

class DirectMachine:
 def __init__(self,image):
  self.uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM|unicorn.UC_MODE_LITTLE_ENDIAN)
  self.uc.mem_map(BASE,CODE_SIZE);self.uc.mem_write(BASE,image);self.uc.mem_map(DATA,DATA_SIZE);self.uc.mem_map(SP_BASE,SP_SIZE)
  self.writes=[];self.mutation=None;self.mutation_fired=False;self.mutation_event_count=0
  self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,self.on_write)
  self.uc.hook_add(unicorn.UC_HOOK_CODE,self.on_code,begin=STOP,end=STOP)
 def on_write(self,uc,_access,address,size,value,_data):
  if DATA<=address<DATA+DATA_SIZE:self.writes.append((address,size,value&U32))
  events=(self.mutation or {}).get('events',[self.mutation] if self.mutation else [])
  if self.mutation and self.mutation_event_count<len(events):
   event=events[self.mutation_event_count]
   if address==event['trigger_addr']:
    uc.mem_write(event['change_addr'],event['change_bytes']);self.mutation_event_count+=1;self.mutation_fired=True
 def on_code(self,uc,address,_size,_data):
  if address==STOP:uc.emu_stop()
 def run(self,c,mutation=None):
  uc=self.uc;uc.mem_write(SRC,c['source']);uc.mem_write(OUT,c['output']);uc.mem_write(COUNT,struct.pack('<I',0xDEADBEEF));uc.mem_write(CURSOR,struct.pack('<Q',c['cursor']));uc.mem_write(INDEX,struct.pack('<I',c['index']));uc.mem_write(SP,struct.pack('<II',CURSOR,INDEX))
  uc.reg_write(arm.UC_ARM_REG_R0,SRC);uc.reg_write(arm.UC_ARM_REG_R1,OUT);uc.reg_write(arm.UC_ARM_REG_R2,c['request']&U32);uc.reg_write(arm.UC_ARM_REG_R3,COUNT);uc.reg_write(arm.UC_ARM_REG_SP,SP);uc.reg_write(arm.UC_ARM_REG_LR,STOP)
  for i,r in enumerate(SAVED):uc.reg_write(r,0xC5000000+i*0x01010101)
  before=[uc.reg_read(r) for r in SAVED];self.writes.clear();self.mutation=mutation;self.mutation_fired=False;self.mutation_event_count=0;fault=None
  try:uc.emu_start(ADDRESS,0,count=200000)
  except unicorn.UcError as e:fault=str(e)
  relevant=bytes(uc.mem_read(SRC,0xB0))+bytes(uc.mem_read(OUT,0x100))+bytes(uc.mem_read(COUNT,4))+bytes(uc.mem_read(CURSOR,8))+bytes(uc.mem_read(INDEX,4))
  result={'fault':fault,'r0':uc.reg_read(arm.UC_ARM_REG_R0),'sp':uc.reg_read(arm.UC_ARM_REG_SP),'callee_saved':[uc.reg_read(r) for r in SAVED]==before,'memory':relevant.hex(),'writes':self.writes.copy(),'mutation_fired':self.mutation_fired,'mutation_event_count':self.mutation_event_count}
  self.mutation=None;return result

def compare_case(original,staged,c,mutation=None,label=''):
 a=original.run(c,mutation);b=staged.run(c,mutation)
 if a!=b:raise AssertionError(f'{label} mismatch; original={a}; candidate={b}')
 if a['fault'] is not None or a['sp']!=SP or not a['callee_saved']:raise AssertionError(f'{label} fault/ABI: {a}')
 return a

def stage_mutant(out,original,needle,replacement,label):
 text=SOURCE.read_text(encoding='utf-8')
 if text.count(needle)!=1:raise AssertionError(f'{label} mutation source not unique')
 path=out/'mutants'/f'{label}.cpp';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text.replace(needle,replacement),encoding='utf-8')
 body,_=compile_body(out/'mutants'/f'{label}-compile',path);return stage(original,body)[0]

def run_parent(image,index,ring):
 case=reader.make_case(index,0,1,1,0,0,1,0x12A758+index)
 uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM|unicorn.UC_MODE_LITTLE_ENDIAN)
 uc.mem_map(BASE,CODE_SIZE);uc.mem_write(BASE,image);uc.mem_map(DATA,DATA_SIZE);uc.mem_map(0x004E3000,0x1000);uc.mem_map(SP_BASE,SP_SIZE)
 context=case['context'];obj=case['object'];source=case['source'];uc.mem_write(context,case['context_bytes']);uc.mem_write(obj,bytes(16));uc.mem_write(source,bytes(0xB0));uc.mem_write(context,struct.pack('<I',obj));uc.mem_write(obj+4,struct.pack('<I',source))
 # One stable record at canonical slot 3; H2 requests at most one record.
 ring_source=bytearray(0xB0);struct.pack_into('<QQi',ring_source,0,10,20,3)
 record=struct.pack('<IIIhh',*case['record'][:3],case['record'][3],case['record'][4])
 ring_source[0x28+3*16:0x38+3*16]=record
 uc.mem_write(source,bytes(ring_source));uc.mem_write(reader.STATE,case['output_bytes']);uc.mem_write(reader.MODE,b'\x00');uc.mem_write(reader.FLAG_A,b'\x00');uc.mem_write(reader.FLAG_B,b'\x00');uc.mem_write(reader.POSTPROCESS_GATE,b'\x01')
 writes=[]
 def on_write(_uc,_access,address,size,value,_data):
  if reader.STATE<=address<reader.STATE+0x20 or context<=address<context+0x60:writes.append((address,size,value&U32))
 write_hook=uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,on_write);uc.reg_write(arm.UC_ARM_REG_FPEXC,0x40000000)
 for i,r in enumerate(SAVED):uc.reg_write(r,0xC1000000+i*0x01010101)
 saved=[uc.reg_read(r) for r in SAVED];uc.reg_write(arm.UC_ARM_REG_SP,SP);uc.reg_write(arm.UC_ARM_REG_LR,STOP);uc.reg_write(arm.UC_ARM_REG_R0,context);uc.reg_write(arm.UC_ARM_REG_R1,reader.STATE)
 stop_hook=uc.hook_add(unicorn.UC_HOOK_CODE,lambda m,a,_s,_d:m.emu_stop() if a==STOP else None,begin=STOP,end=STOP)
 fault=None
 try:uc.emu_start(reader.ADDRESS,0,count=200000)
 except unicorn.UcError as e:fault=str(e)
 result={'fault':fault,'return':uc.reg_read(arm.UC_ARM_REG_R0),'sp':uc.reg_read(arm.UC_ARM_REG_SP),'callee_saved':[uc.reg_read(r) for r in SAVED]==saved,'output':bytes(uc.mem_read(reader.STATE,0x20)).hex(),'context':bytes(uc.mem_read(context,0x60)).hex(),'writes':writes,'source_header':bytes(uc.mem_read(source,0x18)).hex()}
 uc.hook_del(write_hook);uc.hook_del(stop_hook)
 return result

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--seed',type=int,default=20261229);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
 original=IMAGE.read_bytes()
 if sha(original)!=IMAGE_SHA:raise AssertionError('pinned image hash mismatch')
 body,obj=compile_body(args.out/'compile');candidate,payload,ips=stage(original,body)
 original_machine=DirectMachine(original);candidate_machine=DirectMachine(candidate)
 (args.out/'staged-image.bin').write_bytes(candidate);(args.out/'slot.ips').write_bytes(ips);(args.out/'production.o').write_bytes(obj.read_bytes())
 pair_scenarios=[(10,20,10),(10,20,9),(20,10,15),((-5)&U64,(-3)&U64,(-7)&U64),((-(1<<63))&U64,(-5)&U64,0),(30,30,30),((-10)&U64,(-10)&U64,(-10)&U64)]
 requests=(-0x80000000,-1,0,1,7,8,0x7fffffff);effective_values=(-1,0,1,3,7);indices=(0,1,3,7,U32)
 directed=0
 for req in requests:
  for eff in effective_values:
   for p0,p1,cur in pair_scenarios:
    for idx in indices:
     c=fixture(req,eff,p0,p1,cur,idx,args.seed+directed)
     compare_case(original_machine,candidate_machine,c,label=f'directed-{directed}');directed+=1
 rng=random.Random(args.seed);seeded=0
 for i in range(128):
  req=rng.choice(requests);eff=rng.choice((0,1,2,3,4,5,6,7));idx=rng.choice((0,1,2,3,4,5,6,7,U32))
  p0,p1,cur=rng.choice(pair_scenarios);c=fixture(req,eff,p0,p1,cur,idx,rng.getrandbits(32));compare_case(original_machine,candidate_machine,c,label=f'seeded-{i}');seeded+=1
 # One-shot source changes after the first payload load force a full snapshot retry.
 retry_cases=[]
 for field,new_value in ((0x10,3),(0,11),(4,1),(8,21),(12,1)):
  c=fixture(1,4,10,20,5,0,args.seed+0x100+field)
  change=struct.pack('<I',new_value)
  mutation={'trigger_addr':OUT,'change_addr':SRC+field,'change_bytes':change}
  result=compare_case(original_machine,candidate_machine,c,mutation,f'retry-field-{field:#x}')
  if not result['mutation_fired']:raise AssertionError(f'retry hook did not fire for source field {field:#x}')
  copy_writes=sum(1 for address,_size,_value in result['writes'] if OUT<=address<OUT+16)
  if copy_writes<10:raise AssertionError(f'snapshot mutation at {field:#x} did not copy before retry: {copy_writes} stores')
  retry_cases.append({'field':hex(field),'hook_fired':True,'copy_store_count':copy_writes})
 repeat_case=fixture(1,4,10,20,5,0,args.seed+0x180)
 repeated={'events':[{'trigger_addr':OUT,'change_addr':SRC+0x10,'change_bytes':struct.pack('<I',3)},{'trigger_addr':OUT,'change_addr':SRC,'change_bytes':struct.pack('<I',11)}]}
 repeat_result=compare_case(original_machine,candidate_machine,repeat_case,repeated,'two-retry-sequence')
 repeat_stores=sum(1 for address,_size,_value in repeat_result['writes'] if OUT<=address<OUT+16)
 if repeat_result['mutation_event_count']!=2 or repeat_stores<15:raise AssertionError(f'repeated retry sequence did not execute three copies: {repeat_result}')
 retry_cases.append({'field':'multiple-fields','hook_fired':True,'mutation_event_count':2,'copy_store_count':repeat_stores})
 # Explicit contract assertions for raw return paths and copy/store bounds.
 early=candidate_machine.run(fixture(0,3,10,20,5,0,args.seed+9))
 stable=candidate_machine.run(fixture(1,3,10,20,5,0,args.seed+10))
 if early['r0']!=SRC or stable['r0']!=INDEX:raise AssertionError(f'path-dependent r0 contract mismatch {early["r0"]:#x}/{stable["r0"]:#x}')
 mutations=[]
 cap_mut=stage_mutant(args.out,original,'if (requested > 7) requested = 7;','if (requested > 8) requested = 8;','wrong-cap')
 cap_case=fixture(8,7,(-1)&U64,(-2)&U64,(-2)&U64,0,args.seed+0x200)
 cap_machine=DirectMachine(cap_mut);mutations.append({'name':'wrong-cap-7','detected':original_machine.run(cap_case)!=cap_machine.run(cap_case)})
 signed_mut=stage_mutant(args.out,original,'if (cursor_value >= pair0_value) {','if (cursor_bits >= pair0_bits) {','unsigned-pair-compare')
 signed_case=fixture(7,3,(-(1<<63))&U64,20,0,0,args.seed+0x201)
 signed_machine=DirectMachine(signed_mut);mutations.append({'name':'unsigned-64-bit-compare','detected':original_machine.run(signed_case)!=signed_machine.run(signed_case)})
 slot_mut=stage_mutant(args.out,original,'static_cast<u32>(slot_index - i + 8) & 7u','static_cast<u32>(slot_index - i + 8) & 3u','wrong-ring-modulus')
 slot_case=fixture(7,3,10,20,5,0,args.seed+0x202)
 slot_machine=DirectMachine(slot_mut);mutations.append({'name':'wrong-ring-modulus','detected':original_machine.run(slot_case)!=slot_machine.run(slot_case)})
 order_mut=stage_mutant(args.out,original,'cursor[1] = pair0_high;\n        cursor[0] = pair0_low;','cursor[0] = pair0_low;\n        cursor[1] = pair0_high;','wrong-cursor-store-order')
 order_case=fixture(1,3,10,20,5,0,args.seed+0x203)
 order_machine=DirectMachine(order_mut);mutations.append({'name':'wrong-cursor-store-order','detected':original_machine.run(order_case)!=order_machine.run(order_case)})
 if not all(x['detected'] for x in mutations):raise AssertionError(f'undetected negative control(s): {mutations}')
 mode_bodies,interior,getter,wobj,gobj=mode_patch.compile_functions(args.out/'mode-integration')
 mode_image,_,_,_=mode_patch.stage(original,mode_bodies,getter)
 integrated,_,integrated_ips=stage(mode_image,body)
 parent_cases=[]
 for i in range(8):
  a=run_parent(original,i,False);b=run_parent(integrated,i,True)
  if a!=b:raise AssertionError(f'actual reader composition mismatch {i}: {a} != {b}')
  if a['fault'] is not None or a['return']!=1 or a['sp']!=SP or not a['callee_saved']:raise AssertionError(f'actual reader parent contract failed: {a}')
  parent_cases.append({'case':i,'equal':True,'return':a['return']})
 report={'status':'passed','reference_sha256':sha(original),'source_sha256':sha(SOURCE.read_bytes()),'object_sha256':sha(obj.read_bytes()),'body_sha256':sha(body),'body_bytes':len(body),'slot_bytes':SLOT,'relocations':[],'direct_directed_cases':directed,'direct_seeded_cases':seeded,'direct_differences':0,'retry_fields':retry_cases,'retry_differences':0,'raw_return':{'early':hex(early['r0']),'stable':hex(stable['r0']),'stable_is_index_pointer':True},'mutations':mutations,'ips_sha256':sha(ips),'ips_replay':apply_ips(original,ips)==candidate,'staged_image_sha256':sha(candidate),'actual_reader_compositions':parent_cases,'integrated_image_sha256':sha(integrated),'integrated_ips_sha256':sha(integrated_ips),'domain':'ordinary aligned RAM, canonical ring slots 0..7 and one-shot deterministic snapshot mutation; producer timing/liveness and aliasing are not established'}
 (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(f'PASS direct={directed}+{seeded} retry={len(retry_cases)} parents={len(parent_cases)} body={len(body)}/{SLOT} mutations={len(mutations)}')
 return 0
if __name__=='__main__':raise SystemExit(main())
