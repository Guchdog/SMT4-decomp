#!/usr/bin/env python3
"""Partial-span final-VMA differential for H2 mode predicate 0x00128C2C."""
from __future__ import annotations
import argparse,hashlib,json,struct,sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips,encode_ips
from tools import h2_11c5ec_experiment as reader
IMAGE=ROOT/'extracted/exefs/code.bin';IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
WRAPPER_SRC=ROOT/'src/engine/leaf_batch29_a.cpp';GETTER_SRC=ROOT/'src/engine/leaf_batch21_a.cpp'
BASE=0x00100000;SIZE=0x00380000;SP_BASE=0x08000000;SP_SIZE=0x10000;SP=SP_BASE+0x8000;STOP=SP_BASE+0x9000
WRAPPER=0x00128C2C;WRAPPER_WINDOW=24;INTERIOR=0x00128C48;INTERIOR_SIZE=56;GETTER=0x00138F34;GETTER_SIZE=16;GLOBAL=0x0047388B
NOP=struct.pack('<I',0xE320F000);SAVED=[getattr(arm,f'UC_ARM_REG_R{i}') for i in range(4,12)]
def sha(b):return hashlib.sha256(b).hexdigest()
def branch(site,target):
 d=target-(site+8)
 if (site|target|d)&3 or not -(1<<25)<=d<(1<<25):raise AssertionError(f'invalid ARM call {site:#x}->{target:#x}')
 return 0xEB000000|((d>>2)&0xffffff)
def compile_functions(out,wrapper_source=WRAPPER_SRC):
 out.mkdir(parents=True,exist_ok=True);wobj=out/'leaf_batch29_a.o';gobj=out/'leaf_batch21_a.o'
 for source,obj in ((wrapper_source,wobj),(GETTER_SRC,gobj)):
  res=compile_tu_armv6k(source,obj,ROOT)
  if res.returncode:raise RuntimeError(res.stderr or f'compile failed: {source}')
 wf=extract_elf_functions_detailed(wobj);gf=extract_elf_functions_detailed(gobj)
 wbody,wrels=wf['func_00128c2c'];ibody,irels=wf['func_00128c48'];gbody,grels=gf['func_00138f34']
 if len(wrels)!=1 or wrels[0].relocation_type!=28 or wrels[0].symbol_name!='func_00138f34':raise AssertionError(f'unexpected wrapper relocations {wrels}')
 if irels or grels:raise AssertionError(f'interior/getter relocations unexpected: {irels}, {grels}')
 if len(wbody)>WRAPPER_WINDOW or (WRAPPER_WINDOW-len(wbody))%4:raise AssertionError(f'wrapper body {len(wbody)} does not fit its 24-byte span')
 if len(ibody)!=INTERIOR_SIZE:raise AssertionError(f'interior body size {len(ibody)} != {INTERIOR_SIZE}')
 if len(gbody)>GETTER_SIZE or (GETTER_SIZE-len(gbody))%4:raise AssertionError(f'getter body {len(gbody)} does not fit {GETTER_SIZE}')
 fixed=bytearray(wbody);rel=wrels[0];struct.pack_into('<I',fixed,rel.offset,branch(WRAPPER+rel.offset,GETTER))
 return bytes(fixed),ibody,gbody,wobj,gobj

def stage(image,wbody,gbody):
 wpayload=wbody+NOP*((WRAPPER_WINDOW-len(wbody))//4);gpayload=gbody+NOP*((GETTER_SIZE-len(gbody))//4)
 patches=[(WRAPPER-BASE,wpayload),(GETTER-BASE,gpayload)]
 staged=bytearray(image)
 for off,payload in patches:staged[off:off+len(payload)]=payload
 ips=encode_ips(patches,len(image))
 if apply_ips(image,ips)!=bytes(staged):raise AssertionError('partial-span IPS replay failed')
 changed=[i for i,(a,b) in enumerate(zip(image,staged)) if a!=b]
 allowed=[(WRAPPER-BASE,WRAPPER-BASE+WRAPPER_WINDOW),(GETTER-BASE,GETTER-BASE+GETTER_SIZE)]
 if any(not any(a<=i<b for a,b in allowed) for i in changed):raise AssertionError('patch changed bytes outside wrapper/getter slots')
 if staged[WRAPPER-BASE+WRAPPER_WINDOW:WRAPPER-BASE+84]!=image[WRAPPER-BASE+WRAPPER_WINDOW:WRAPPER-BASE+84]:raise AssertionError('interior/NOP/literals changed')
 return bytes(staged),wpayload,gpayload,ips

def invoke(image,entry,mode):
 uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM|unicorn.UC_MODE_LITTLE_ENDIAN);uc.mem_map(BASE,SIZE);uc.mem_write(BASE,image)
 uc.mem_map(SP_BASE,SP_SIZE);uc.mem_write(GLOBAL,bytes([mode&255]));uc.reg_write(arm.UC_ARM_REG_SP,SP);uc.reg_write(arm.UC_ARM_REG_LR,STOP)
 for i,r in enumerate(SAVED):uc.reg_write(r,0xB6000000+i*0x01010101)
 before=[uc.reg_read(r) for r in SAVED];uc.hook_add(unicorn.UC_HOOK_CODE,lambda m,a,_s,_d:m.emu_stop() if a==STOP else None,begin=STOP,end=STOP)
 fault=None
 try:uc.emu_start(entry,0,count=5000)
 except unicorn.UcError as e:fault=str(e)
 return {'fault':fault,'return':uc.reg_read(arm.UC_ARM_REG_R0),'sp':uc.reg_read(arm.UC_ARM_REG_SP),'callee_saved':[uc.reg_read(r) for r in SAVED]==before}

def parent(image,index,mode,count):
 case=reader.make_case(index,mode,count,1,0,0,1,0x128C2C+index);m=reader.Machine(image,count,case['record']);m.setup(case);trace=[]
 for addr in (WRAPPER,GETTER):m.uc.hook_add(unicorn.UC_HOOK_CODE,lambda _m,a,_s,_d,trace=trace:trace.append(a),begin=addr,end=addr)
 result=m.invoke(reader.ADDRESS,case['context'],False)
 expected=[WRAPPER,GETTER]
 if trace!=expected:raise AssertionError(f'parent call trace {trace} != {expected}')
 if bool(result['ring_calls'])!=(mode!=4):raise AssertionError(f'mode gate/ring result wrong mode={mode:#x}')
 return result,trace

def branch_target(image,site,kind):
 word=struct.unpack_from('<I',image,site-BASE)[0]
 if (word>>28)==0xF or (word&0x0E000000)!=0x0A000000:raise AssertionError(f'not an ARM B/BL at {site:#x}: {word:#x}')
 if (kind=='bl') != bool(word&0x01000000):raise AssertionError(f'wrong B/BL kind at {site:#x}')
 imm=word&0xffffff
 if imm&0x800000:imm-=0x1000000
 return word,site+8+(imm<<2)
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
 image=IMAGE.read_bytes()
 if sha(image)!=IMAGE_SHA:raise AssertionError('pinned image hash mismatch')
 wbody,ibody,gbody,wobj,gobj=compile_functions(args.out/'compile');original_interior=image[INTERIOR-BASE:INTERIOR-BASE+INTERIOR_SIZE]
 if ibody!=original_interior:raise AssertionError('separate interior entry body differs from original suffix')
 staged,wpayload,gpayload,ips=stage(image,wbody,gbody)
 (args.out/'staged-image.bin').write_bytes(staged);(args.out/'partial-span.ips').write_bytes(ips);(args.out/'wrapper-slot.bin').write_bytes(wpayload);(args.out/'getter-slot.bin').write_bytes(gpayload)
 direct=[]
 for mode in range(256):
  ref=invoke(image,WRAPPER,mode);got=invoke(staged,WRAPPER,mode)
  if ref!=got:raise AssertionError(f'direct mismatch mode={mode:#x}: {ref} != {got}')
  if got['return']!=(1 if mode==4 else 0) or got['fault'] is not None or got['sp']!=SP or not got['callee_saved']:raise AssertionError(f'wrapper contract/ABI mismatch at {mode:#x}: {got}')
  direct.append({'mode':mode,'return':got['return']})
 compositions=[]
 for i,mode in enumerate((0,3,4,5,0x7f,0x80,0xff)):
  for count in (0,1):
   ref,rt=parent(image,2*i+count,mode,count);got,gt=parent(staged,2*i+count,mode,count)
   if ref!=got or rt!=gt:raise AssertionError(f'reader composition mismatch mode={mode:#x} count={count}')
   compositions.append({'mode':mode,'count':count,'equal':True,'ring_calls':len(got['ring_calls'])})
 callers=[]
 for site,target,kind in ((0x0011C60C,WRAPPER,'bl'),(0x00128C30,GETTER,'bl'),(0x0010FC3C,0x00128C44,'b'),(0x0035B0B8,INTERIOR,'b')):
  word,got=branch_target(image,site,kind)
  if got!=target or got&1:raise AssertionError(f'caller {site:#x}->{got:#x}, expected {target:#x}')
  if site in (0x0010FC3C,0x0035B0B8) and staged[site-BASE:site-BASE+4]!=image[site-BASE:site-BASE+4]:raise AssertionError('tail caller changed')
  callers.append({'site':hex(site),'word':hex(word),'target':hex(got),'kind':kind})
 source=WRAPPER_SRC.read_text(encoding='utf-8');needle='func_00138f34() == 4 ? 1 : 0'
 if source.count(needle)!=1:raise AssertionError('wrong-predicate mutation needle is not unique')
 mutant=args.out/'wrong-mode-mutant.cpp';mutant.write_text(source.replace(needle,'func_00138f34() == 3 ? 1 : 0'),encoding='utf-8')
 mb,mi,mg,_,_=compile_functions(args.out/'mutant-compile',mutant);mutant_image,_,_,_=stage(image,mb,mg)
 mutation=invoke(image,WRAPPER,4)!=invoke(mutant_image,WRAPPER,4)
 if not mutation:raise AssertionError('wrong comparison constant was not detected')
 report={'status':'passed','image_sha256':sha(image),'wrapper_source_sha256':sha(WRAPPER_SRC.read_bytes()),'getter_source_sha256':sha(GETTER_SRC.read_bytes()),'wrapper_object_sha256':sha(wobj.read_bytes()),'getter_object_sha256':sha(gobj.read_bytes()),'wrapper_body_sha256':sha(wbody),'wrapper_body_bytes':len(wbody),'wrapper_patch_window':WRAPPER_WINDOW,'interior_body_sha256':sha(ibody),'interior_body_bytes':len(ibody),'interior_matches_original':True,'getter_body_sha256':sha(gbody),'getter_body_bytes':len(gbody),'relocations_resolved':[{'symbol':'func_00138f34','target':hex(GETTER)}],'direct_case_count':len(direct),'direct_differences':0,'reader_composition_case_count':len(compositions),'reader_composition_differences':0,'caller_targets':callers,'wrong_constant_mutation_detected':mutation,'ips_sha256':sha(ips),'ips_replay':apply_ips(image,ips)==staged,'staged_sha256':sha(staged),'interior_suffix_unchanged':staged[WRAPPER-BASE+WRAPPER_WINDOW:WRAPPER-BASE+84]==image[WRAPPER-BASE+WRAPPER_WINDOW:WRAPPER-BASE+84],'scope':'mapped mode byte and synthetic reader memory with controlled ring seam; interior SVC stream preserved byte-for-byte and not executed'}
 (args.out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(f'PASS direct={len(direct)} reader={len(compositions)} wrapper={len(wbody)}/{WRAPPER_WINDOW} interior={len(ibody)}/{INTERIOR_SIZE} mutation=detected')
 return 0
if __name__=='__main__':raise SystemExit(main())
