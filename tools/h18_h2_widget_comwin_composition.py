#!/usr/bin/env python3
"""Compose original/C++ ComWin_Calc and widget helper with named callee models."""
from __future__ import annotations
import argparse, hashlib, json, struct, subprocess, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang, get_armv6k_flags
IMAGE_PATH=ROOT/'extracted/exefs/code.bin'; IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
WIDGET_SOURCE=ROOT/'experiments/semantic_equivalence/h1_preview_helper_candidate.cpp'
COMWIN_SOURCE=ROOT/'experiments/semantic_equivalence/h18_h2_comwin_calc.cpp'
TEXT=0x100000; WIDGET=0x2bf9f0; COMWIN=0x11b094; COMWIN_SIZE=148
INJECT=0x1000000; INJECT_SIZE=0x20000; TRACE=0x1010000
DATA=0x2000000; WORK=DATA; ROWS=DATA+0x1000; SEQUENCE=DATA+0x2000
STACK=0x8000000; STOP=0x800f000; GLOBAL=0x43e0f8
NOP=struct.pack('<I',0xe320f000); MASK=0xffffffff
CALLEE=(UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11)
DEPS={0x2bdac0:1,0x2c615c:2,0x2b1fc0:3,0x2b1dfc:4,0x2b1c8c:5}
def sha(data): return hashlib.sha256(data).hexdigest()
def compile_obj(src,out,symbol):
 p=compile_tu_armv6k(src,out,ROOT)
 if p.returncode: raise RuntimeError(p.stderr)
 body,rel=extract_elf_functions_detailed(out)[symbol]
 if rel: raise AssertionError(f'{symbol} unresolved relocations: {rel}')
 return body,sha(out.read_bytes())
def link_widget(out,source,label):
 generated=out/f'linked_{label}.cpp'
 generated.write_text(
  '#include "'+str(source.resolve()).replace('\\','/')+'"\n'
  'using U32=unsigned int; using S32=int;\n'
  'static S32 interp_result(S32 d,U32 n){if(!n)return 0; U32 x=(d<0)?0u-(U32)d:(U32)d,q=0,r=0; for(int i=31;i>=0;--i){r=(r<<1)|((x>>i)&1u);if(r>=n){r-=n;q|=(1u<<i);}} return d<0?(S32)(0u-q):(S32)q;}\n'
  'static void record(U32 id,U32 a,U32 b,U32 c){ volatile U32* p=(volatile U32*)0x01010000u; U32 n=p[0]; p[1+n*4]=id; p[2+n*4]=a; p[3+n*4]=b; p[4+n*4]=c; p[0]=n+1; }\n'
  'extern "C" __attribute__((noinline,used)) void camp_func_002bdac0(void* o,S32 a,S32 f){record(1,(U32)(unsigned long)o,(U32)a,(U32)f);}\n'
  'extern "C" __attribute__((noinline,used)) S32 ui_func_002c615c(S32 d,U32 n){S32 r=interp_result(d,n);record(2,(U32)d,n,(U32)r);return r;}\n'
  'extern "C" __attribute__((noinline,used)) void ui_func_002b1fc0(void* o){record(3,(U32)(unsigned long)o,0,0);}\n'
  'extern "C" __attribute__((noinline,used)) void ui_func_002b1dfc(void* o){record(4,(U32)(unsigned long)o,0,0);}\n'
  'extern "C" __attribute__((noinline,used)) void ui_func_002b1c8c(void* o){record(5,(U32)(unsigned long)o,0,0);}\n',encoding='utf-8')
 clang=find_clang(); elf=out/f'linked_{label}.elf'; cmd=[str(clang),*get_armv6k_flags(ROOT,clang),'-nostdlib','-fuse-ld=lld','-Wl,-Ttext=0x01000000','-Wl,-e,h1_preview_helper_candidate','-Wl,--build-id=none',str(generated),'-o',str(elf)]
 p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True)
 if p.returncode: raise RuntimeError(p.stderr)
 tools=clang.parent; raw=out/f'linked_{label}.text'; subprocess.run([str(tools/'llvm-objcopy.exe'),'--dump-section',f'.text={raw}',str(elf)],check=True,capture_output=True,text=True)
 n=subprocess.run([str(tools/'llvm-nm.exe'),'-n',str(elf)],check=True,capture_output=True,text=True); syms={}
 for line in n.stdout.splitlines():
  f=line.split()
  if len(f)>=3:
   try: syms[f[2]]=int(f[0],16)
   except ValueError: pass
 entry=syms['h1_preview_helper_candidate']; text=raw.read_bytes()
 if len(text)>=0x10000: raise AssertionError('linked candidate exceeds private text window')
 return {'elf':elf,'text':text,'entry':entry,'offset':entry-INJECT,'sha256':sha(elf.read_bytes()),'text_sha256':sha(text),'text_size':len(text),'argv':cmd}
def widget_object(work,off,kind,direction=0):
 obj=WORK+off
 def w32(at,x): struct.pack_into('<I',work,off+at,x&MASK)
 def w16(at,x): struct.pack_into('<H',work,off+at,x&0xffff)
 work[off:off+0x8b]=bytearray(0x8b); w32(4,0); w32(8,0)
 if kind=='early': w32(4,0xffffffff); w32(8,0xffffffff)
 elif kind in ('ready','not_ready'):
  work[off+0x86]=1; work[off+0x87]=0 if kind=='not_ready' else 1; work[off+0x88]=1; work[off+0x89]=1
 elif kind in ('interpolate','animation'):
  w32(0x4c,ROWS); w16(0x50,0); w16(0x52,0); work[off+0x54]=direction&0xff; work[off+0x86]=0; work[off+0x87:off+0x8a]=b'\x01\x01\x01'
  row=bytearray(12); struct.pack_into('<hhhhH',row,0,10,20,30,40,8 if kind=='interpolate' else 0); row[10]=1 if kind=='interpolate' else 0
  if kind=='animation':
   work[off+0x84]=1; w32(0x78,SEQUENCE); w16(0x7c,0)
   seq=bytearray(0x38); struct.pack_into('<I',seq,0,5); seq[4]=1; struct.pack_into('<I',seq,0x1c,6); seq[0x20]=2
   return obj,row,seq
  return obj,row,None
 return obj,None,None
def signed32(x): return x if x<0x80000000 else x-0x100000000
def trunc_div(a,b): return (abs(a)//abs(b)) * (-1 if (a<0)!=(b<0) else 1)
def run_case(image,widget_text,widget_entry,comwin_body,case):
 u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(TEXT,0x500000); u.mem_write(TEXT,image); u.mem_map(INJECT,INJECT_SIZE); u.mem_write(INJECT,widget_text); u.mem_map(DATA,0x10000); u.mem_map(STACK,0x10000)
 if comwin_body is not None: u.mem_write(COMWIN,comwin_body+NOP*((COMWIN_SIZE-len(comwin_body))//4))
 u.mem_write(GLOBAL,struct.pack('<I',WORK)); work=bytearray(0x188); struct.pack_into('<II',work,8,case['state'],case.get('counter',5))
 obj_off=0xc8 if case['state']==2 else 0x3c
 obj,row,seq=widget_object(work,obj_off,case['widget'],case.get('direction',0)); u.mem_write(WORK,bytes(work))
 if row is not None: u.mem_write(ROWS,bytes(row))
 if seq is not None: u.mem_write(SEQUENCE,bytes(seq))
 u.mem_write(TRACE,bytes(0x1000)); u.reg_write(UC_ARM_REG_SP,STACK+0x8000); u.reg_write(UC_ARM_REG_LR,STOP); u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
 for i,r in enumerate(CALLEE): u.reg_write(r,0x33440000+i)
 saved={r:u.reg_read(r) for r in CALLEE}; helper=[]; status={'returned':False}
 def hook(m,pc,size,data):
  if pc==WIDGET and widget_entry is not None:
   m.reg_write(UC_ARM_REG_PC,widget_entry); return
  if pc in DEPS:
   ident=DEPS[pc]; r0=m.reg_read(UC_ARM_REG_R0); r1=m.reg_read(UC_ARM_REG_R1); r2=m.reg_read(UC_ARM_REG_R2)
   result=(trunc_div(signed32(r0),r1) if r1 else 0) if ident==2 else 0
   if ident==2: helper.append([ident,r0,r1,result&MASK])
   elif ident==1: helper.append([ident,r0,r1,r2])
   else: helper.append([ident,r0])
   m.reg_write(UC_ARM_REG_R0,result&MASK); m.reg_write(UC_ARM_REG_PC,m.reg_read(UC_ARM_REG_LR))
  elif pc==STOP: status['returned']=True; m.emu_stop()
 u.hook_add(UC_HOOK_CODE,hook); u.emu_start(COMWIN,0,count=50000)
 if not status['returned']: raise AssertionError(f'ComWin did not return for {case}')
 if widget_entry is not None:
  count=struct.unpack('<I',bytes(u.mem_read(TRACE,4)))[0]; helper=[]
  for i in range(count):
   event=list(struct.unpack('<IIII',bytes(u.mem_read(TRACE+4+16*i,16))))
   helper.append(event if event[0]==2 else event[:4] if event[0]==1 else event[:2])
 return {'return':u.reg_read(UC_ARM_REG_R0),'sp':u.reg_read(UC_ARM_REG_SP),'callee_saved_preserved':all(u.reg_read(r)==v for r,v in saved.items()),'state':struct.unpack('<I',bytes(u.mem_read(WORK+8,4)))[0],'counter':struct.unpack('<I',bytes(u.mem_read(WORK+0xc,4)))[0],'work':bytes(u.mem_read(WORK,0x188)).hex(),'helper_trace':helper,'widget_bytes':bytes(u.mem_read(WORK+obj_off,0x8b)).hex()}
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--output',required=True); a=ap.parse_args(); out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
 image=IMAGE_PATH.read_bytes()
 if sha(image)!=IMAGE_SHA: raise SystemExit('pinned original image SHA mismatch')
 cw,cwsha=compile_obj(COMWIN_SOURCE,out/'comwin.o','h18_h2_comwin_calc_candidate')
 if len(cw)>COMWIN_SIZE or len(cw)%4: raise AssertionError('ComWin candidate span invalid')
 linked=link_widget(out,WIDGET_SOURCE,'candidate')
 cases=[{'name':'state1_early','state':1,'widget':'early'},{'name':'state1_common_ready','state':1,'widget':'ready'},{'name':'state1_common_not_ready','state':1,'widget':'not_ready'},{'name':'state1_interpolation','state':1,'widget':'interpolate','direction':0},{'name':'state1_interpolation_reverse','state':1,'widget':'interpolate','direction':1},{'name':'state1_animation_sequence','state':1,'widget':'animation'},{'name':'state2_common_ready','state':2,'widget':'ready'},{'name':'state2_common_not_ready','state':2,'widget':'not_ready'},{'name':'state4_common_ready','state':4,'widget':'ready'},{'name':'state4_common_not_ready','state':4,'widget':'not_ready'},{'name':'state0_no_widget','state':0,'widget':'ready'},{'name':'state3_no_widget','state':3,'widget':'ready'},{'name':'state5_no_widget','state':5,'widget':'ready'}]
 combos={}
 for case in cases:
  variants={}
  for cname,cbody in [('original',None),('comwin_candidate',cw)]:
   for wname,wentry in [('original',None),('widget_candidate',linked['entry'])]:
    name=f'{cname}+{wname}'; variants[name]=run_case(image,linked['text'],wentry,cbody,case)
  baseline=variants['original+original']
  for name,result in variants.items():
   if result!=baseline: raise AssertionError(f'{case["name"]}/{name} mismatch: {result} != {baseline}')
  combos[case['name']]={'fixture':case,'variants':variants}
 # Widget mutant: reverse final completion conjunction result, test ready fixture through state-1 caller.
 source=WIDGET_SOURCE.read_text(encoding='utf-8'); needle='? 1 : 0;'
 if source.count(needle)!=1: raise AssertionError('widget mutant anchor not unique')
 mutant_src=out/'widget_mutant.cpp'; mutant_src.write_text(source.replace(needle,'? 0 : 1;',1)); mutant=link_widget(out,mutant_src,'widget_mutant')
 control=next(c for c in cases if c['name']=='state1_common_ready')
 good=run_case(image,linked['text'],linked['entry'],cw,control); bad=run_case(image,mutant['text'],mutant['entry'],cw,control)
 if good==bad: raise AssertionError('widget readiness negative control escaped')
 # ComWin mutant: invert state-1 result gate without changing either assigned candidate.
 csrc=COMWIN_SOURCE.read_text(encoding='utf-8'); cneedle='if (widget_calc(const_cast<uint8_t*>(work + 0x3cu)) != 0) {'
 if csrc.count(cneedle)!=2: raise AssertionError('ComWin mutant anchor not unique')
 cmut_src=out/'comwin_mutant.cpp'; cmut_src.write_text(csrc.replace(cneedle,'if (widget_calc(const_cast<uint8_t*>(work + 0x3cu)) == 0) {',1)); cmut,cmutsha=compile_obj(cmut_src,out/'comwin_mutant.o','h18_h2_comwin_calc_candidate')
 cgood=run_case(image,linked['text'],linked['entry'],cw,control); cbad=run_case(image,linked['text'],linked['entry'],cmut,control)
 if cgood==cbad: raise AssertionError('ComWin state-gate negative control escaped')
 report={'reference_sha256':sha(image),'widget_candidate_sha256':sha(WIDGET_SOURCE.read_bytes()),'comwin_candidate_sha256':sha(COMWIN_SOURCE.read_bytes()),'compiled_comwin_object_sha256':cwsha,'compiled_comwin_body_sha256':sha(cw),'comwin_bytes':len(cw),'comwin_mutant_object_sha256':cmutsha,'widget_linked_elf_sha256':linked['sha256'],'widget_linked_text_sha256':linked['text_sha256'],'widget_entry':hex(linked['entry']),'widget_text_size':linked['text_size'],'callee_models':{'0x002bdac0':'trace (object,animation,frame); returns zero with no object writes','0x002c615c':'trace (signed delta,duration,result); truncating signed delta/duration, zero for duration zero','0x002b1fc0':'trace object; returns zero with no object writes','0x002b1dfc':'trace object; returns zero with no object writes','0x002b1c8c':'trace object; returns zero with no object writes'},'cases':combos,'negative_controls':{'widget_readiness_inversion':{'detected':True,'good':good,'mutant':bad},'comwin_state1_gate_inversion':{'detected':True,'good':cgood,'mutant':cbad}},'passed':True,'limitations':['All five external widget callees are deterministic models; only their arguments and assumed returns are covered. Their real side effects, callbacks, lifetimes and data dependencies are not established.','Synthetic ComWin work, row and sequence fixtures use valid in-bounds storage; this task does not execute ComWin_Init, a task scheduler, or a live UI cycle.','The four candidate/original combinations establish behavior only under these explicit fixtures and dependency models; they do not promote the widget candidate or prove production/runtime equivalence.']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps({'passed':True,'cases':len(cases),'comwin_bytes':len(cw),'widget_text_size':linked['text_size'],'negative_controls':list(report['negative_controls'])},indent=2))
if __name__=='__main__': main()
