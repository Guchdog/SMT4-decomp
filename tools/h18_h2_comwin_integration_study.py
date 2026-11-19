#!/usr/bin/env python3
"""Private final-VMA staging and registered-callback composition for ComWin_Calc."""
from __future__ import annotations
import argparse, hashlib, json, struct, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
IMAGE_PATH=ROOT/'extracted/exefs/code.bin'; IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
SOURCE=ROOT/'experiments/semantic_equivalence/h18_h2_comwin_calc.cpp'
TEXT=0x100000; ADDR=0x11b094; SPAN=148; COMPOUND=0x11ae10; COMPOUND_SIZE=792
GLOBAL=0x43e0f8; WIDGET=0x2bf9f0; ALLOC=0x2c4b84; ZERO=0x2c4b30; CREATE_CALC=0x2c5978
INIT=0x10a748; AFTER_CREATE_CALC=0x10a7c0; WORK=0x900000; STACK=0xa0ff00; STOP=0xa0f000
NOP=struct.pack('<I',0xe320f000)
def sha(b): return hashlib.sha256(b).hexdigest()
def compile_candidate(out):
 r=compile_tu_armv6k(SOURCE,out,ROOT)
 if r.returncode: raise RuntimeError(r.stderr)
 entry=extract_elf_functions_detailed(out)['h18_h2_comwin_calc_candidate']; body,rel=entry
 if rel: raise AssertionError(f'candidate has unresolved relocations: {rel}')
 if len(body)>SPAN or len(body)%4: raise AssertionError(f'invalid candidate size/alignment: {len(body)}')
 return body
def make_ipspatch(image,body):
 padded=body+NOP*((SPAN-len(body))//4)
 if len(padded)!=SPAN: raise AssertionError('padded function must exactly cover subentry')
 offset=ADDR-TEXT; ips=encode_ips([(offset,padded)],len(image)); staged=apply_ips(image,ips)
 if staged[offset:offset+SPAN]!=padded: raise AssertionError('IPS roundtrip did not reproduce candidate slot')
 changed=[i for i,(a,b) in enumerate(zip(image,staged)) if a!=b]
 if any(not offset<=i<offset+SPAN for i in changed): raise AssertionError('staging changed bytes outside candidate subentry')
 lo=COMPOUND-TEXT; hi=lo+COMPOUND_SIZE
 if staged[lo:offset]!=image[lo:offset] or staged[offset+SPAN:hi]!=image[offset+SPAN:hi]: raise AssertionError('compound span bytes outside subentry changed')
 return padded,ips,staged,changed
def registration_run(image,callback_outcome):
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,0x500000); u.mem_write(TEXT,image); u.mem_map(0x800000,0x300000)
 u.mem_write(GLOBAL,b'\0'*4)
 u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP); u.reg_write(UC_ARM_REG_R0,0); u.reg_write(UC_ARM_REG_R1,0); u.reg_write(UC_ARM_REG_R2,0); u.reg_write(UC_ARM_REG_R3,0)
 u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
 state={'alloc':0,'zero':0,'create_calc':0,'stopped_init':False,'registration':None,'widget_calls':[],'callback_returned':False}
 def hook(m,pc,size,data):
  if pc==ALLOC:
   state['alloc']+=1; m.reg_write(UC_ARM_REG_R0,WORK); m.reg_write(UC_ARM_REG_PC,m.reg_read(UC_ARM_REG_LR))
  elif pc==ZERO:
   state['zero']+=1; ptr=m.reg_read(UC_ARM_REG_R0); size=m.reg_read(UC_ARM_REG_R1); m.mem_write(ptr,bytes(size)); m.reg_write(UC_ARM_REG_R0,ptr); m.reg_write(UC_ARM_REG_PC,m.reg_read(UC_ARM_REG_LR))
  elif pc==CREATE_CALC:
   state['create_calc']+=1; sp=m.reg_read(UC_ARM_REG_SP); name=m.reg_read(UC_ARM_REG_R0); raw=bytes(m.mem_read(name,32)).split(b'\0',1)[0]
   stack_words=[m.mem_read(sp+4*i,4) for i in range(4)]
   state['registration']={'name':raw.decode('ascii'),'r1':m.reg_read(UC_ARM_REG_R1),'r2':m.reg_read(UC_ARM_REG_R2),'r3':m.reg_read(UC_ARM_REG_R3),'stack_args':[struct.unpack('<I',x)[0] for x in stack_words],'callback_ptr':struct.unpack('<I',stack_words[0])[0]}
   m.reg_write(UC_ARM_REG_R0,0x88776655); m.reg_write(UC_ARM_REG_PC,m.reg_read(UC_ARM_REG_LR))
  elif pc==AFTER_CREATE_CALC:
   state['stopped_init']=True; m.emu_stop()
  elif pc==WIDGET:
   state['widget_calls'].append(m.reg_read(UC_ARM_REG_R0)); m.reg_write(UC_ARM_REG_R0,callback_outcome); m.reg_write(UC_ARM_REG_PC,m.reg_read(UC_ARM_REG_LR))
  elif pc==STOP:
   state['callback_returned']=True; m.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook); u.emu_start(INIT,0,count=30000)
 if not state['stopped_init'] or state['registration'] is None: raise AssertionError(f'ComWin_Init registration prefix not reached: {state}')
 registered=state['registration']['callback_ptr']
 if registered!=ADDR: raise AssertionError(f'actual registration pointer changed: {hex(registered)}')
 work=struct.unpack('<I',bytes(u.mem_read(GLOBAL,4)))[0]
 if work!=WORK: raise AssertionError(f'ComWin_Init did not bind fixture work: {hex(work)}')
 init_bytes=bytes(u.mem_read(work,0x188)); init_state,init_counter=struct.unpack_from('<II',init_bytes,8)
 # Invoke the callback through the callback value observed at the original registration boundary.
 callback_results=[]
 for label,initial_state,counter in [('zero_init',init_state,init_counter),('state1_fixture',1,9)]:
  u.mem_write(work+8,struct.pack('<I',initial_state)); u.mem_write(work+0xc,struct.pack('<I',counter)); state['widget_calls']=[]; state['callback_returned']=False
  u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP); u.reg_write(UC_ARM_REG_R0,0xdeadbeef)
  u.emu_start(registered,0,count=3000)
  if not state['callback_returned']: raise AssertionError(f'registered callback failed: {label}')
  callback_results.append({'case':label,'state':struct.unpack('<I',bytes(u.mem_read(work+8,4)))[0],'counter':struct.unpack('<I',bytes(u.mem_read(work+0xc,4)))[0],'return':u.reg_read(UC_ARM_REG_R0),'helper_args':list(state['widget_calls'])})
 return {'init_hooks':{'alloc':state['alloc'],'zero':state['zero'],'create_calc':state['create_calc']},'registration':state['registration'],'work_after_init':{'state':init_state,'counter':init_counter,'task_handle':struct.unpack_from('<I',init_bytes)[0]},'callbacks':callback_results}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
 image=IMAGE_PATH.read_bytes()
 if sha(image)!=IMAGE_SHA: raise SystemExit('pinned original SHA mismatch')
 body=compile_candidate(out/'candidate.o'); padded,ips,staged,changed=make_ipspatch(image,body)
 disasm=list(Cs(CS_ARCH_ARM,CS_MODE_ARM).disasm(body,ADDR))
 blx_count=sum(ins.mnemonic=='blx' for ins in disasm)
 if blx_count!=3 or struct.pack('<I',GLOBAL) not in body or struct.pack('<I',WIDGET) not in body: raise AssertionError('candidate ARM/BLX literal references are unexpected')
 (out/'staged_code.bin').write_bytes(staged); (out/'candidate.ips').write_bytes(ips)
 # Stage is kept private. Do not rewrite config/functions.csv or window.cpp.
 original_registration=registration_run(image,1); staged_registration=registration_run(staged,1)
 if original_registration!=staged_registration: raise AssertionError(f'registration/callback composition differs: {original_registration} != {staged_registration}')
 if original_registration['registration']['name']!='ComWin Calc' or original_registration['registration']['callback_ptr']!=ADDR: raise AssertionError('original registration did not pass expected name/callback')
 expected_calls=[[],[WORK+0x3c]]
 if [c['helper_args'] for c in original_registration['callbacks']]!=expected_calls: raise AssertionError('registered callback state/helper composition unexpected')
 # Confirm disassembled VMA code has final-address-resolved BL/BLX instruction behavior via execution traces.
 report={'reference_sha256':sha(image),'source_sha256':sha(SOURCE.read_bytes()),'object_sha256':sha((out/'candidate.o').read_bytes()),'candidate_sha256':sha(body),'candidate_bytes':len(body),'slot_bytes':SPAN,'compound_span':{'start':hex(COMPOUND),'end':hex(COMPOUND+COMPOUND_SIZE),'candidate_relative_start':hex(ADDR-COMPOUND),'bytes_before_preserved':ADDR-COMPOUND,'bytes_after_preserved':COMPOUND+COMPOUND_SIZE-(ADDR+SPAN)},'relocations':[],'candidate_entry_vma':hex(ADDR),'entry_pointer_bit0':ADDR&1,'widget_target_arm':hex(WIDGET),'widget_pointer_bit0':WIDGET&1,'blx_register_calls':blx_count,'changed_file_offsets':changed,'changed_bytes':len(changed),'only_subentry_changed':all((ADDR-TEXT)<=i<(ADDR-TEXT+SPAN) for i in changed),'ips_sha256':sha(ips),'ips_roundtrip':apply_ips(image,ips)==staged,'staged_sha256':sha(staged),'original_registration_composition':original_registration,'staged_registration_composition':staged_registration,'same_observed_setup_and_registered_callback':True,'caller_limits':['`ComWin_Init` executes original instructions through its actual call to AsdTask_CreateCalc wrapper address 0x002c5978. That wrapper is intercepted after argument setup; its internal task-manager registration implementation is not executed.','Allocation and zero helpers at 0x002c4b84/0x002c4b30 are modeled to return one private work block and clear it. The callback pointer, name, and args at the real caller boundary are captured.','The callback is then invoked using the captured registered pointer in the private image, once with post-init state and once with an explicit state-1 fixture. This is not task-scheduler execution or a natural UI cycle.','No production source, ledger, IPS installation, canonical build or emulator was changed/run.'] ,'passed':True}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'passed':True,'candidate_bytes':len(body),'changed_bytes':len(changed),'ips_roundtrip':report['ips_roundtrip'],'registration':original_registration['registration'],'callbacks':original_registration['callbacks']},indent=2))
if __name__=='__main__': main()
