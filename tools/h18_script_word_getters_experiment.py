#!/usr/bin/env python3
"""Bounded ARM differential for the two script record low-byte getters."""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from dataclasses import replace
from tools.semantic_experiment import (Runner, Case, DATA, DATA_SIZE, SP, STACK_SIZE,
    TEXT, arm_branch, difference, validate_leaf, unicorn)
from tools.semantic_experiment_support import compile_candidate_symbols

ADDRESSES = (0x002345f0, 0x002345fc)
HALFWORDS = (0x0000,0x0001,0x007f,0x0080,0x00ff,0x0100,0x017f,0x0180,0x01ff,
             0x7fff,0x8000,0x80ff,0xff00,0xff7f,0xff80,0xffff)
SEEDS = (7, 20261024)
CALLER_WINDOWS = ({"target":"0x002345f0","caller":"0x0038c43c","callsite":0x0038c5f4,"start":0x0038c5f0,"stop":0x0038c5fc},
                  {"target":"0x002345fc","caller":"0x0038c43c","callsite":0x0038c5e8,"start":0x0038c5e4,"stop":0x0038c5f0})

def verify_reference(path):
    import capstone, csv
    image=Path(path).read_bytes(); cs=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM)
    expected={ADDRESSES[0]:bytes.fromhex('b804d0e1ff0000e21eff2fe1'), ADDRESSES[1]:bytes.fromhex('ba04d0e1ff0000e21eff2fe1')}
    functions={}; sites={a:[] for a in ADDRESSES}
    for address, code in expected.items():
        actual=image[address-TEXT:address-TEXT+12]
        if actual!=code: raise ValueError(f'pinned instructions changed at 0x{address:08x}')
        functions[hex(address)]={'original_bytes_hex':actual.hex(),'instructions':[i.mnemonic+' '+i.op_str for i in cs.disasm(actual,address)]}
    for offset in range(0,len(image)-4,4):
        word=struct.unpack_from('<I',image,offset)[0]
        if word>>24 != 0xeb: continue
        callsite=TEXT+offset; imm=word&0xffffff
        if imm&0x800000: imm-=1<<24
        target=callsite+8+imm*4
        if target in sites:
            caller='unknown'
            with (ROOT/'config/functions.csv').open(encoding='utf-8',newline='') as f:
                for row in csv.DictReader(f):
                    start=int(row['address'],16); size=int(row['size']);
                    if start<=callsite<start+size: caller=row.get('name') or hex(start); break
            sites[target].append({'callsite':hex(callsite),'caller':caller})
    return {'functions':functions,'direct_callers':{hex(a):sites[a] for a in ADDRESSES}}

def make_cases(address, seed, samples):
    rng=random.Random(seed ^ address); offset=0x48 if address==ADDRESSES[0] else 0x4a
    for index,value in enumerate((*HALFWORDS, *(rng.randrange(65536) for _ in range(samples)))):
        regs=[rng.getrandbits(32) for _ in range(13)]; regs[0]=DATA+0x100+(index%8)*4
        memory=bytearray(rng.randbytes(DATA_SIZE)); struct.pack_into('<H',memory,regs[0]-DATA+offset,value)
        struct.pack_into('<H',memory,regs[0]-DATA+(0x4a if offset==0x48 else 0x48),value^0x5aa5)
        yield Case(f'case-{index}-result-{value&255:#x}',tuple(regs),bytes(memory),rng.randbytes(STACK_SIZE),rng.getrandbits(4)<<28)

def _compiled(source, out):
    return compile_candidate_symbols(source,out,ROOT,{'candidate_002345f0','candidate_002345fc','control_wrong_offset','control_signed_extension','control_omitted_mask','control_memory_write'})

def _single(image, address, code, case):
    return Runner(image,address,code).run(case)

def _ram_semantic_difference(original, rebuilt, **kwargs):
    # AArch32 LDRH reads two bytes; Clang may legally narrow the typed C++ load
    # to LDRB because only the low byte is used. In this ordinary-RAM domain,
    # compare resulting state and writes; retain and report read footprints.
    return difference(replace(original, reads=rebuilt.reads), rebuilt, **kwargs)

def _run_with_full_state(runner, case, **kwargs):
    result=runner.run(case,**kwargs)
    regs=tuple(runner.uc.reg_read(r) for r in runner.reg_ids)
    import unicorn
    from unicorn import arm_const as arm
    state={'r0_r12':regs,'sp':runner.uc.reg_read(arm.UC_ARM_REG_SP),
           'lr':runner.uc.reg_read(arm.UC_ARM_REG_LR),'pc':result.pc,'nzcv':result.nzcv}
    return result,state

def _full_ram_difference(original_runner, candidate_runner, case, **kwargs):
    a,as_= _run_with_full_state(original_runner,case,**kwargs); b,bs=_run_with_full_state(candidate_runner,case,**kwargs)
    reason=_ram_semantic_difference(a,b,**({'caller_window':kwargs.get('start') is not None,'compare_flags':True}))
    if reason: return reason
    if as_!=bs: return 'full GPR/LR/SP/NZCV/PC state differs'
    return None

def run(code_path, output, seed=7, samples=32):
    output=Path(output); output.mkdir(parents=True,exist_ok=True); image=Path(code_path).read_bytes()
    source=ROOT/'experiments/semantic_equivalence/h18_script_word_getters.cpp'
    compiled=_compiled(source,output/'h18_script_word_getters.o')
    funcs=[]
    for address,symbol in zip(ADDRESSES,('candidate_002345f0','candidate_002345fc')):
        outcomes=[]; original=Runner(image,address)
        for case in make_cases(address,seed,samples):
            reason=_full_ram_difference(original,Runner(image,address,compiled[symbol]),case)
            outcomes.append({'case':case.label,'passed':reason is None,'reason':reason})
        funcs.append({'address':hex(address),'cases':len(outcomes),'passed':all(x['passed'] for x in outcomes),'results':outcomes,'candidate_bytes':len(compiled[symbol]),'candidate_sha256':hashlib.sha256(compiled[symbol]).hexdigest()})
    # Deliberate wrong implementations must be rejected by directed inputs.
    controls=[]
    control_functions=(('wrong_offset','control_wrong_offset',ADDRESSES[0]),('signed_extension','control_signed_extension',ADDRESSES[0]),('omitted_mask','control_omitted_mask',ADDRESSES[0]),('memory_write','control_memory_write',ADDRESSES[0]))
    for name,symbol,address in control_functions:
        detected=False; reason=None
        all_cases=list(make_cases(address,seed,0))
        directed=(all_cases[3] if name=='signed_extension' else
                  all_cases[11] if name=='omitted_mask' else
                  all_cases[4] if name=='wrong_offset' else all_cases[0])
        for case in (directed,):
            reason=_full_ram_difference(Runner(image,address),Runner(image,address,compiled[symbol]),case)
            if reason: detected=True; break
        controls.append({'name':name,'detected':detected,'reason':reason})
    caller=[]
    for window in CALLER_WINDOWS:
        address=int(window['target'],16); sym='candidate_'+f'{address:08x}'; start=window['start']; stop=window['stop']
        # Keep the caller's actual add/BL/mov sequence; SL (r10) points into aligned ordinary RAM.
        cases=list(make_cases(address,seed,1)); case=cases[-1]; regs=list(case.registers); regs[10]=DATA+0x100
        offset=0x48 if address==ADDRESSES[0] else 0x4a
        struct.pack_into('<H',bytearray(),0,0) if False else None
        data=bytearray(case.data); struct.pack_into('<H',data,0x100+0x28+offset,0x00d3); struct.pack_into('<H',data,0x100+0x28+(0x4a if offset==0x48 else 0x48),0x005e)
        case=Case(case.label,tuple(regs),bytes(data),case.stack,case.nzcv)
        original_runner=Runner(image,address); candidate_runner=Runner(image,address,compiled[sym])
        a,as_=_run_with_full_state(original_runner,case,start=start,stops=(stop,))
        b,bs=_run_with_full_state(candidate_runner,case,start=start,stops=(stop,))
        reason=_ram_semantic_difference(a,b,returns_value=False,caller_window=True,compare_flags=True)
        if reason is None and as_!=bs: reason='full GPR/LR/SP/NZCV/PC state differs'
        caller.append({'target':window['target'],'caller':window['caller'],'callsite':hex(window['callsite']),'start':hex(start),'stop':hex(stop),'passed':reason is None,'reason':reason,'cases':1,'consumes_result':True,'original_reads':[hex(x) for x in sorted(a.reads)],'candidate_reads':[hex(x) for x in sorted(b.reads)]})
    refs=verify_reference(code_path)
    report={'schema':1,'seed':seed,'passed':all(x['passed'] for x in funcs) and all(x['detected'] for x in controls) and all(x['passed'] for x in caller), 'functions':funcs,'results':funcs,'direct_callers':refs['direct_callers'],'reference':refs['functions'],'negative_controls':controls,'caller_windows':caller,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'object_sha256':hashlib.sha256((output/'h18_script_word_getters.o').read_bytes()).hexdigest(),'limitations':['Only aligned ordinary RAM was exercised; unaligned ARM LDRH behavior, MMIO, exceptions, races and game runtime are outside the domain. Caller windows stop after the paired getter result is consumed in one representative 0038c43c sequence.']}
    (output/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8'); return report

def main():
    p=argparse.ArgumentParser(); p.add_argument('--code',type=Path,default=ROOT/'extracted/exefs/code.bin'); p.add_argument('--output',type=Path,required=True); p.add_argument('--seed',type=int,default=7); p.add_argument('--samples',type=int,default=32); a=p.parse_args(); r=run(a.code,a.output,a.seed,a.samples); print(json.dumps({'passed':r['passed'],'report':str(a.output/'report.json')})); return 0 if r['passed'] else 1
if __name__=='__main__': raise SystemExit(main())
