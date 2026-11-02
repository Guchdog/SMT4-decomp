#!/usr/bin/env python3
"""Offline differential and TitleConfig caller composition for 0x002C1830."""
from __future__ import annotations
import hashlib, json, random, struct, sys
from pathlib import Path
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools.semantic_experiment import arm_branch
from tools import h2_logical_query_caller_composition as callers
IMAGE=ROOT/'extracted/exefs/code.bin'; IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
BASE=ROOT/'build/agent-work/H2-semantic/h2-titleconfig-002bdac0-convert/run004/staged/code.h2-002bdac0.bin'
BASE_SHA='3afbd263381b66d18f8ac680529fb27e4291899b70cb74401c8b812552df8774'
SOURCE=ROOT/'experiments/semantic_equivalence/h2_2c1830_candidate.cpp'
OUT=ROOT/'build/agent-work/H2-semantic/h2-titleconfig-002c1830-convert/run006'
ADDR=0x002C1830; SPAN=504; TEXT=0x00100000; TEMP=0x00800000; STOP=0x0080F000
DATA=0x00900000; DATA_SIZE=0x40000; STACK=0x00A0FF00; NOP=struct.pack('<I',0xE320F000); MASK=0xffffffff
HELPERS={'ui_func_002b902c':0x002B902C,'ui_func_002bffbc':0x002BFFBC,'ui_func_002c17d4':0x002C17D4}
FALLBACKS=(0x00125C10,0x00124FA8,0x00124F0C)

def sha(b): return hashlib.sha256(b).hexdigest()
def compile_body(name,source,symbol):
 obj=OUT/name; r=compile_tu_armv6k(source,obj,ROOT)
 if r.returncode: raise RuntimeError(r.stderr)
 body,rel=extract_elf_functions_detailed(obj)[symbol]
 return obj,body,rel

def relocate(body,relocs,entry):
 result=bytearray(body)
 for r in relocs:
  if r.relocation_type not in (28,29) or r.symbol_name not in HELPERS or r.explicit_addend is not None:
   raise AssertionError(f'unsupported relocation {r}')
  target=HELPERS[r.symbol_name]
  ins=struct.unpack_from('<I',result,r.offset)[0]
  if target&3: raise AssertionError(f'non-ARM helper target {target:#x}')
  if r.relocation_type==28:
   if ins&0x0f000000!=0x0b000000: raise AssertionError(f'R_ARM_CALL is not BL: {ins:#010x}')
  elif ins&0x0f000000!=0x0a000000 or ins&0x01000000:
   raise AssertionError(f'R_ARM_JUMP24 is not B: {ins:#010x}')
  delta=target-(entry+r.offset+8)
  if delta&3 or not -(1<<25)<=delta<(1<<25): raise AssertionError('ARM branch out of range/alignment')
  struct.pack_into('<I',result,r.offset,(ins&0xff000000)|((delta>>2)&0x00ffffff))
 return bytes(result)

def make_machine(image,inject=None):
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,(len(image)+0xfff)&~0xfff); u.mem_write(TEXT,image)
 u.mem_map(0x00800000,0x10000); u.mem_map(DATA,DATA_SIZE); u.mem_map(0x00A00000,0x10000)
 if inject: u.mem_write(*inject)
 state={'done':False,'trace':[],'writes':[],'last_pc':None,'responses':{}}
 def code(m,a,size,d):
  state['last_pc']=a
  if a==STOP: state['done']=True; m.emu_stop(); return
  if a in HELPERS.values() or a in FALLBACKS:
   arg=m.reg_read(UC_ARM_REG_R0); state['trace'].append((a,arg))
   queue=state['responses'].get((a,arg),state['responses'].get(a,[0]))
   if queue: value=queue.pop(0)
   else: value=0
   lr=m.reg_read(UC_ARM_REG_LR); m.reg_write(UC_ARM_REG_R0,value&MASK); m.reg_write(UC_ARM_REG_PC,lr)
 def write(m,kind,a,size,value,d): state['writes'].append((a,size,value&MASK))
 u.hook_add(UC_HOOK_CODE,code); u.hook_add(UC_HOOK_MEM_WRITE,write); u._state=state
 return u

def run_direct(u,entry,id_,mode,responses):
 st=u._state; st.update(done=False,trace=[],writes=[],last_pc=None,responses={k:list(v) for k,v in responses.items()})
 pattern=bytes((i*37+0x5a)&255 for i in range(0x200))
 u.mem_write(STACK-0x100,pattern)
 saved={r:0x12340000+i*0x01010101 for i,r in enumerate((UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11))}
 u.reg_write(UC_ARM_REG_SP,STACK); u.reg_write(UC_ARM_REG_LR,STOP)
 for r,v in saved.items(): u.reg_write(r,v)
 u.reg_write(UC_ARM_REG_R0,id_); u.reg_write(UC_ARM_REG_R1,mode)
 fault=None
 try: u.emu_start(entry,0,count=500)
 except (UcError,OSError) as e: fault=str(e)
 return {'fault':fault,'done':st['done'],'return':u.reg_read(UC_ARM_REG_R0),'trace':tuple(st['trace']),
         'callee_saved':all(u.reg_read(r)==v for r,v in saved.items()),'sp':u.reg_read(UC_ARM_REG_SP),
         'stack':bytes(u.mem_read(STACK-0x100,len(pattern))),'external_writes':tuple(x for x in st['writes'] if not STACK-0x100<=x[0]<STACK+0x100)}

def responses_for(id_,mode,primary,secondary,fallback):
 helper=HELPERS['ui_func_002b902c'] if mode==0 else HELPERS['ui_func_002bffbc'] if mode==1 else HELPERS['ui_func_002c17d4']
 out={(helper,id_):[primary]}
 if 3<=id_<=6: out[(helper,id_+9)]=[secondary]
 code=1 if id_==0 else 2 if id_==1 else 6 if id_==7 else 5 if id_==8 else 3 if id_==9 else 4 if id_==10 else 0
 fb=FALLBACKS[mode] if mode in (0,1,2) else None
 if code and fb is not None: out[(fb,code)]=[fallback]
 return out

def projection(x): return {k:x[k] for k in ('fault','done','return','trace','callee_saved','sp','stack','external_writes')}

def caller_profile(image,wrapper_code,scenario,mode0=None,mode1=None):
 m=callers.LogicalQueryCalcMachine(image,scenario,None,mode0,mode1)
 if wrapper_code is not None: m.uc.mem_write(ADDR,wrapper_code)
 return m.run()

def main():
 OUT.mkdir(parents=True,exist_ok=True); image=IMAGE.read_bytes(); base=BASE.read_bytes()
 if sha(image)!=IMAGE_SHA or sha(base)!=BASE_SHA: raise SystemExit('pinned original or cumulative base hash mismatch')
 obj,body,rel=compile_body('candidate.o',SOURCE,'candidate_002c1830')
 temp_code=relocate(body,rel,TEMP); final_code=relocate(body,rel,ADDR)
 if len(body)>SPAN: raise AssertionError('candidate exceeds original slot')
 padded=final_code+NOP*(SPAN//4-len(final_code)//4)
 final_image=bytearray(image); final_image[ADDR-TEXT:ADDR-TEXT+SPAN]=padded
 staged=bytearray(base); staged[ADDR-TEXT:ADDR-TEXT+SPAN]=padded
 changed=[i for i,(a,b) in enumerate(zip(base,staged)) if a!=b]
 if any(not ADDR-TEXT<=i<ADDR-TEXT+SPAN for i in changed): raise AssertionError('staging escaped declared slot')
 ips=encode_ips([(ADDR-TEXT,padded)],len(base))
 if apply_ips(base,ips)!=bytes(staged): raise AssertionError('IPS round-trip failed')
 old=make_machine(image); temp=make_machine(image,(TEMP,temp_code)); final=make_machine(bytes(final_image)); staged_m=make_machine(bytes(staged))
 profiles=[(old,ADDR),(temp,TEMP),(final,ADDR),(staged_m,ADDR)]
 cases=[]; rng=random.Random(0x2c1830)
 ids=(0,1,2,3,4,5,6,7,8,9,10,11,12,0x80000000,0xffffffff)
 for mode in (0,1,2):
  for id_ in ids:
   plans=[(0x80000001,0,0xFEDCBA98)]
   if 3<=id_<=6: plans.extend(((0,0x81234567,0xABCDEF01),(0,0,0x87654321)))
   else: plans.append((0,0,0x87654321))
   for primary,secondary,fallback in plans:
    responses=responses_for(id_,mode,primary,secondary,fallback)
    results=[run_direct(m,e,id_,mode,responses) for m,e in profiles]
    if any(projection(x)!=projection(results[0]) for x in results[1:]): raise AssertionError(f'direct mismatch mode={mode} id={id_}: {[projection(x) for x in results]}')
    expected_calls=[]; helper=HELPERS['ui_func_002b902c'] if mode==0 else HELPERS['ui_func_002bffbc'] if mode==1 else HELPERS['ui_func_002c17d4']
    expected_calls.append((helper,id_))
    if primary==0 and 3<=id_<=6:
     expected_calls.append((helper,id_+9))
     if secondary==0:
      code=0
    else: code=0
    if primary==0 and not (3<=id_<=6):
     code=1 if id_==0 else 2 if id_==1 else 6 if id_==7 else 5 if id_==8 else 3 if id_==9 else 4 if id_==10 else 0
    if primary==0 and code: expected_calls.append((FALLBACKS[mode],code))
    if results[0]['trace']!=tuple(expected_calls): raise AssertionError(f'call-order/short-circuit mismatch: {results[0]["trace"]} != {expected_calls}')
    cases.append({'mode':mode,'id':id_,'primary':hex(primary),'secondary':hex(secondary),'fallback':hex(fallback),'same':True})
 # Invalid modes make no calls for every key category.
 for mode in (3,0xffffffff):
  for id_ in (0,3,7,10,11,0xffffffff):
   responses={}; results=[run_direct(m,e,id_,mode,responses) for m,e in profiles]
   if any(projection(x)!=projection(results[0]) for x in results[1:]) or results[0]['return']!=0 or results[0]['trace']:
    raise AssertionError(f'invalid mode behavior differs: {mode:#x}/{id_:#x}')
   cases.append({'mode':mode,'id':id_,'invalid_mode_zero_no_calls':True})
 # Three independently compiled negative controls.
 original=SOURCE.read_text(); controls=[]
 for name,old_text,new_text,case in [
  ('secondary-id-plus-9-to-plus-10','id + 9u','id + 10u',(0,3,0,0xAABBCCDD)),
  ('id-7-fallback-6-to-5','id == 7) * 6u','id == 7) * 5u',(0,7,0,0xAABBCCDD)),
  ('nonzero-return-polarity','if (value != 0)','if (value == 0)',(1,9,0x80000001,0xABCDEF01))]:
  if original.count(old_text)<1: raise AssertionError(f'mutation anchor changed: {name}')
  mutant=OUT/f'mutant-{name}.cpp'; mutant.write_text(original.replace(old_text,new_text,1))
  mo,mb,mr=compile_body(f'mutant-{name}.o',mutant,'candidate_002c1830')
  mc=relocate(mb,mr,TEMP+0x1000); mu=make_machine(image,(TEMP+0x1000,mc))
  mode,id_,primary,fbret=case
  sec=0 if id_==3 else 0
  responses=responses_for(id_,mode,primary,sec,fbret)
  baseline=run_direct(old,ADDR,id_,mode,responses); mutated=run_direct(mu,TEMP+0x1000,id_,mode,responses)
  detected=projection(baseline)!=projection(mutated); controls.append({'name':name,'detected':detected})
  if not detected: raise AssertionError(f'negative control escaped: {name}')
 # Actual original TitleConfig_Calc runs with the wrapper replaced at final VMA.
 mode0_obj,mode0_body,mode0_rel=compile_body('caller-mode0.o',callers.MODE0_SOURCE,'candidate_002b902c')
 mode1_obj,mode1_body,mode1_rel=compile_body('caller-mode1.o',callers.MODE1_SOURCE,'candidate_002bffbc')
 if mode0_rel or mode1_rel: raise AssertionError('unexpected caller helper relocation')
 caller_rows=[]; query_seen=set(); callsite_seen=set(); static_site_seen=set()
 for scenario in callers.scenarios():
  # Exercise the pinned original TitleConfig_Calc, changing only the wrapper
  # under test. The cumulative image contains a previously converted Calc and
  # cannot prove the original six call-site paths.
  old_run=caller_profile(image,None,scenario)
  wrapped=caller_profile(bytes(final_image),None,scenario)
  old_typed=caller_profile(image,None,scenario,mode0_body,mode1_body)
  wrapped_typed=caller_profile(bytes(final_image),None,scenario,mode0_body,mode1_body)
  for label,result in [('old',old_run),('wrapper',wrapped),('old_typed',old_typed),('wrapper_typed',wrapped_typed)]:
   if result['fault'] is not None or not result['stopped'] or result['preserved']!=result['expected_preserved']:
    raise AssertionError(f'caller gate failed {scenario.label}/{label}: {result["fault"]}')
  errors=[callers.compare_runs(old_run,wrapped),callers.compare_runs(old_typed,wrapped_typed)]
  if any(errors): raise AssertionError(f'TitleConfig caller mismatch {scenario.label}: {errors}')
  query_seen.update(tuple(x) for x in old_run['logical_wrapper_trace'])
  callsite_seen.update(tuple(x) for x in old_run['logical_wrapper_pc_trace'])
  static_site_seen.update(tuple(x) for x in old_run['titleconfig_query_site_trace'])
  caller_rows.append({'scenario':scenario.label,'same_original_helpers':True,'same_typed_mode_helpers':True,'calls':old_run['logical_wrapper_trace'],'callsite_calls':old_run['logical_wrapper_pc_trace'],'titleconfig_query_sites':old_run['titleconfig_query_site_trace']})
 required={(9,1),(4,0),(3,0),(0,1),(1,1)}
 if not required<=query_seen: raise AssertionError(f'H2 wrapper calls missing: {required-query_seen}')
 site_pairs={(pc,(query_id,mode)) for pc,query_id,mode in callsite_seen}
 if len(site_pairs)!=7 or {pair for _,pair in site_pairs}!={(9,1),(4,0),(3,0),(0,1),(1,1)}:
  raise AssertionError(f'Calc wrapper-entry LR coverage mismatch: {site_pairs}')
 stage_dir=OUT/'staged'; stage_dir.mkdir(exist_ok=True); image_path=stage_dir/'code.h2-002c1830.bin'; ips_path=stage_dir/'code.h2-002c1830.ips'
 image_path.write_bytes(staged); ips_path.write_bytes(ips)
 manifest={'original_sha256':sha(image),'base_sha256':sha(base),'staged_sha256':sha(staged),'ips_sha256':sha(ips),'address':hex(ADDR),'slot_bytes':SPAN,'candidate_bytes':len(body),'changed_bytes':len(changed),'only_declared_slot_changed':True,'ips_roundtrip':True,'relocations':[{'offset':r.offset,'type':r.relocation_type,'symbol':r.symbol_name} for r in rel],'runtime':'not_run'}
 (stage_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 report={'image_sha256':sha(image),'base_sha256':sha(base),'source_sha256':sha(SOURCE.read_bytes()),'candidate_object_sha256':sha(obj.read_bytes()),'body_sha256':sha(body),'body_bytes':len(body),'slot_bytes':SPAN,'relocations':manifest['relocations'],'direct_cases':len(cases),'direct_call_matrix':cases,'negative_controls':controls,'caller_scenarios':len(caller_rows),'caller_query_pairs':sorted([list(x) for x in query_seen]),'caller_callsite_pairs':sorted([[hex(pc),query_id,mode] for pc,query_id,mode in callsite_seen]),'titleconfig_query_site_pairs':sorted([[hex(pc),query_id,mode] for pc,query_id,mode in static_site_seen]),'caller_rows':caller_rows,'staged_sha256':sha(staged),'ips_sha256':sha(ips),'changed_bytes':len(changed),'only_declared_slot_changed':True,'ips_roundtrip':True,'runtime':'not_run'}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({k:v for k,v in report.items() if k not in ('direct_call_matrix','caller_rows')},indent=2))
if __name__=='__main__': main()
