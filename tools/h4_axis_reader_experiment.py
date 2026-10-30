"""Offline ARM differential for H4 axis reader; outputs only into --out-dir."""
import argparse, hashlib, json, random, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.build_check import compile_tu_armv6k, find_clang
from tools.asm_diff import extract_elf_functions_detailed
import unicorn
from unicorn import arm_const as a
CODE=ROOT/'extracted/exefs/code.bin'; SRC=ROOT/'experiments/semantic_equivalence/h4_axis_reader_candidate.cpp'
ORIG=0x27fbc8; CAND=0x1000000; STOP=0x100f000; STACK=0x8000000; CAL=0x2010000; OUT=0x2011000; DEAD=0x19fe4c

def link(raw,relocs):
    data=bytearray(raw); rows=[]
    for r in relocs:
        if r.symbol_name != 'h4_original_deadzone' or r.relocation_type != 28: raise ValueError(str(r))
        src=CAND+r.offset; delta=DEAD-(src+8)
        if src&3 or DEAD&3 or delta&3 or not -(1<<25)<=delta<(1<<25): raise ValueError('unsafe branch')
        w=struct.unpack_from('<I',data,r.offset)[0]
        if w&0x0f000000!=0x0b000000: raise ValueError('not ARM BL')
        struct.pack_into('<I',data,r.offset,0xeb000000|((delta>>2)&0xffffff)); rows.append(hex(src))
    if len(rows)!=2: raise ValueError(f'expected two helper relocations: {rows}')
    return bytes(data),rows

def run(entry,blob,c,extended=False):
    uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM); uc.ctl_set_cpu_model(a.UC_CPU_ARM_11MPCORE)
    uc.mem_map(0x100000,0x480000,7); uc.mem_write(0x100000,CODE.read_bytes())
    uc.mem_map(CAND,0x10000,7); uc.mem_write(CAND,blob); uc.mem_map(0x2000000,0x20000,3); uc.mem_map(STACK,0x4000,3)
    uc.reg_write(a.UC_ARM_REG_FPEXC,0x40000000); uc.reg_write(a.UC_ARM_REG_C1_C0_2,0xf00000)
    if extended:
        uc.reg_write(a.UC_ARM_REG_FPSCR,0x01000000)
        for n in range(4,12): uc.reg_write(getattr(a,f'UC_ARM_REG_R{n}'),0x41410000+n)
        for n in range(8,16): uc.reg_write(getattr(a,f'UC_ARM_REG_D{n}'),0x3ff0000000000000+n)
    state=bytearray(0x20); struct.pack_into('<III',state,0,CAL,c['max'],c['flags']); struct.pack_into('<f',state,0x14,c['threshold']); uc.mem_write(0x4650a0,bytes(state))
    cal=bytearray(0x20); struct.pack_into('<hhh',cal,0xc,*c['lo']); struct.pack_into('<hhh',cal,0x12,*c['hi']); cal[0x18]=c['selector']; uc.mem_write(CAL,bytes(cal))
    samples=bytearray(0x30)
    for k,(x,y) in enumerate(c['samples']): struct.pack_into('<hh',samples,k*16+12,x,y)
    uc.mem_write(0x4e3c28,bytes(samples)); uc.mem_write(OUT,b'\xa5'*16)
    calls=[]; writes=[]
    def hook(u,addr,size,user):
        if addr==DEAD:
            ptr=u.reg_read(a.UC_ARM_REG_R0)
            try: val=bytes(u.mem_read(ptr,4)).hex()
            except unicorn.UcError: val='unreadable'
            calls.append((u.reg_read(a.UC_ARM_REG_S0),val))
        if addr==STOP: u.emu_stop()
    def memwrite(u,access,address,size,value,user): writes.append((address,size,value))
    uc.hook_add(unicorn.UC_HOOK_CODE,hook)
    if extended: uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,memwrite)
    xptr=c.get('xptr',OUT if c.get('xout',True) else 0)
    yptr=c.get('yptr',OUT+4 if c.get('yout',True) else 0)
    for reg,val in [(a.UC_ARM_REG_SP,STACK+0x2000),(a.UC_ARM_REG_LR,STOP),(a.UC_ARM_REG_R0,xptr),(a.UC_ARM_REG_R1,yptr),(a.UC_ARM_REG_R2,c['mode'])]: uc.reg_write(reg,val)
    fault=None
    try: uc.emu_start(entry,STOP,count=5000)
    except unicorn.UcError as ex: fault=str(ex)
    basic={'fault':fault,'pc':hex(uc.reg_read(a.UC_ARM_REG_PC)) if fault else None,'ret':uc.reg_read(a.UC_ARM_REG_R0),'output':bytes(uc.mem_read(OUT,16)).hex(),'calls':calls,'returned':uc.reg_read(a.UC_ARM_REG_PC)==STOP}
    if not extended:return basic
    def snapshot(addr,size):return bytes(uc.mem_read(addr,size)).hex()
    def pointer_bytes(ptr):
        try:return bytes(uc.mem_read(ptr,4)).hex()
        except unicorn.UcError:return None
    basic.update({'preserved_gpr':{f'r{n}':hex(uc.reg_read(getattr(a,f'UC_ARM_REG_R{n}'))) for n in range(4,12)},
                  'preserved_vfp':{f'd{n}':hex(uc.reg_read(getattr(a,f'UC_ARM_REG_D{n}'))) for n in range(8,16)},
                  'fpscr':hex(uc.reg_read(a.UC_ARM_REG_FPSCR)),
                  'output_targets':{'x':pointer_bytes(xptr) if xptr else None,'y':pointer_bytes(yptr) if yptr else None},
                  'memory':{'state':snapshot(0x4650a0,0x20),'calibration':snapshot(CAL,0x20),'samples':snapshot(0x4e3c28,0x30),'output':snapshot(OUT,0x10)},
                  'data_writes':[[hex(addr),size,hex(value)] for addr,size,value in writes if not STACK<=addr<STACK+0x4000],
                  'stack_write_count':sum(1 for addr,_,_ in writes if STACK<=addr<STACK+0x4000)})
    return basic

def audit_cases(seed):
    rng=random.Random(seed)
    base={'max':1,'flags':0,'threshold':0.0,'lo':[-100,-200,-32768],'hi':[100,200,32767],'selector':0,'mode':0,'samples':[(0,0),(50,-100),(-32768,32767)],'xout':True,'yout':True}
    cases=[]
    def add(name,**kw):
        c=base.copy();c.update(kw);cases.append((name,c))
    for mode in [0,1,2,0xffffffff]:add('mode-'+str(mode),mode=mode)
    for mode,maximum in [(0,0),(1,0),(1,1),(1,2),(0xffffffff,0xffffffff)]:add(f'mode-max-{mode}-{maximum}',mode=mode,max=maximum)
    for selector in [0,1,2,3,255]:add('selector-'+str(selector),selector=selector,samples=[(-32768,32767),(100,-200),(32767,-32768)])
    for flags in [0,1,2,0xfffffffe,0xffffffff]:add('flags-'+hex(flags),flags=flags)
    add('limit-0',mode=1,max=0);add('alternate-source',flags=1)
    for x,y in [(0,0),(1,0),(0,1),(1,1)]:add('null-'+str(x)+str(y),xout=bool(x),yout=bool(y))
    # Equal and swapped outputs, plus writes aliasing state, calibration and source spans.
    add('out-x-equals-y',xptr=OUT,yptr=OUT)
    add('out-swapped',xptr=OUT+4,yptr=OUT)
    add('out-alias-state',xptr=0x4650a4,yptr=0x4650a8)
    add('out-alias-calibration',xptr=CAL+0x1c,yptr=CAL+0x1c)
    add('out-alias-sample-header',xptr=0x4e3c28,yptr=0x4e3c2c)
    for threshold in [0.0,-0.0,0.01,0.25,0.25000003,0.24999999,1.0,-0.25,float('nan'),float('inf'),float('-inf')]:
        add('threshold-'+repr(threshold),threshold=threshold,lo=[0,0,0],hi=[100,100,100],samples=[(25,0),(1,-100),(0,0)])
    add('zero-span-zero',lo=[0,0,0],hi=[0,0,0],samples=[(0,0),(0,0),(0,0)])
    add('zero-span-nonzero',lo=[0,0,0],hi=[0,0,0],samples=[(1,-1),(0,0),(0,0)])
    add('reversed-span',lo=[100,200,300],hi=[-100,-200,-300],samples=[(32767,-32768),(0,0),(0,0)])
    add('invalid-x-pointer',xptr=0xfffffff0,yptr=OUT+4,samples=[(50,-100),(0,0),(0,0)])
    add('invalid-y-pointer',xptr=OUT,yptr=0xfffffff0,samples=[(50,-100),(0,0),(0,0)])
    for i in range(100):add('random-'+str(i),selector=rng.randrange(3),mode=rng.randrange(2),flags=rng.randrange(2),threshold=rng.choice([0.0,0.1,0.5]),samples=[(rng.randrange(-32768,32768),rng.randrange(-32768,32768)) for _ in range(3)])
    return cases

def observable(result):
    return {k:result.get(k) for k in ['fault','ret','output','calls','returned','preserved_gpr','preserved_vfp','fpscr','output_targets','memory','data_writes']}

def run_contract_audit(blob,seed,out,obj,links):
    cases=audit_cases(seed);diffs=[];fault_cases=[]
    for name,c in cases:
        old=run(ORIG,blob,c,extended=True);new=run(CAND,blob,c,extended=True)
        if old['fault'] or new['fault']:
            # Invalid pointers are outside the function's valid caller domain. Preserve
            # the observed fault and memory effect, but do not treat post-fault scratch
            # registers/PC values as a supported semantic contract.
            fault_cases.append({'case':name,'input':c,'original_fault':old['fault'],'candidate_fault':new['fault'],'same_fault_class':old['fault']==new['fault'],'original_writes':old['data_writes'],'candidate_writes':new['data_writes']})
            continue
        if observable(old)!=observable(new):diffs.append({'case':name,'input':c,'original':old,'candidate':new})
    # Same-input sensitivity check: mutate the CMP immediate used by the unsigned upper-mode guard.
    offset=0x30; before=struct.unpack_from('<I',blob,offset)[0]
    if before!=0xE3520001:raise ValueError(f'unexpected mode guard encoding at +0x30: {before:#010x}')
    mutant=bytearray(blob);struct.pack_into('<I',mutant,offset,0xE3520002);mutant=bytes(mutant)
    control=cases[0][1].copy();control.update({'mode':2,'max':2,'threshold':0.0,'samples':[(0,0),(0,0),(-32768,32767)]})
    old=run(ORIG,blob,control,extended=True);mutated=run(CAND,mutant,control,extended=True)
    negative_detected=observable(old)!=observable(mutated)
    rep={'status':'passed' if not diffs and negative_detected and all(x['same_fault_class'] for x in fault_cases) else 'failed','mode':'contract-audit','seed':seed,'case_count':len(cases),'first_counterexample':diffs[0] if diffs else None,'difference_count':len(diffs),'fault_cases':fault_cases,'same_input_mutation_control':{'change':'CMP r2,#1 at candidate offset 0x30 changed to CMP r2,#2, extending the unsigned accepted-mode ceiling from 1 to 2','case':control,'mutation_offset':hex(offset),'original_word':hex(before),'mutant_word':hex(0xE3520002),'detected':negative_detected,'original':old,'mutated_candidate':mutated},'reference_sha256':hashlib.sha256(CODE.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(blob).hexdigest(),'mutant_sha256':hashlib.sha256(mutant).hexdigest(),'helper_relocations':links,'scope':'synthetic direct original-vs-C++ checks over valid mapped state; invalid output pointers are recorded as out-of-contract fault probes without comparing undefined post-fault scratch state. Stack bytes are reported by write count but scratch layout is not compared','unicorn':unicorn.__version__}
    (out/'contract-audit-report.json').write_text(json.dumps(rep,indent=2,allow_nan=False));print(json.dumps(rep,indent=2,allow_nan=False));return 0 if rep['status']=='passed' else 1

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out-dir',required=True); ap.add_argument('--seed',type=int,default=7); ap.add_argument('--audit-contract',action='store_true'); args=ap.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=False); obj=out/'candidate.o'
    result=compile_tu_armv6k(SRC,obj,ROOT)
    if result.returncode: raise RuntimeError(result.stderr)
    raw,rel=extract_elf_functions_detailed(obj)['h4_axis_reader_candidate']; blob,links=link(raw,rel)
    if args.audit_contract:return run_contract_audit(blob,args.seed,out,obj,links)
    rng=random.Random(args.seed); base={'max':1,'flags':0,'threshold':0.0,'lo':[-100,-200,-32768],'hi':[100,200,32767],'selector':0,'mode':0,'samples':[(0,0),(50,-100),(-32768,32767)],'xout':True,'yout':True}
    cases=[]
    def add(n,**kw): c=base.copy(); c.update(kw); cases.append((n,c))
    for mode in [0,1,2,0xffffffff]: add('mode-'+str(mode),mode=mode)
    for s in [0,1,2,255]: add('selector-'+str(s),selector=s,samples=[(-32768,32767),(100,-200),(32767,-32768)])
    add('limit-0',mode=1,max=0); add('alternate-source',flags=1)
    for x,y in [(0,0),(1,0),(0,1),(1,1)]: add('null-'+str(x)+str(y),xout=bool(x),yout=bool(y))
    for threshold in [0.01,0.25,1.0,-0.25]: add('deadzone-'+str(threshold),threshold=threshold,samples=[(20,-80),(0,0),(0,0)])
    add('zero-span',lo=[0,0,0],hi=[0,0,0],samples=[(1,-1),(0,0),(0,0)])
    for i in range(100): add('random-'+str(i),selector=rng.randrange(3),mode=rng.randrange(2),flags=rng.randrange(2),threshold=rng.choice([0.0,0.1,0.5]),samples=[(rng.randrange(-32768,32768),rng.randrange(-32768,32768)) for _ in range(3)])
    diffs=[]; counts={}
    for name,c in cases:
        old=run(ORIG,blob,c); new=run(CAND,blob,c)
        if old!=new: diffs.append({'case':name,'input':c,'original':old,'candidate':new})
    neg=base.copy(); neg['mode']=2
    expected=run(ORIG,blob,neg); mutated=neg.copy(); mutated['mode']=0
    negative_detected=expected!=run(CAND,blob,mutated)
    rep={'status':'passed' if not diffs and negative_detected else 'failed','seed':args.seed,'case_count':len(cases),'first_counterexample':diffs[0] if diffs else None,'difference_count':len(diffs),'negative_control':{'change':'invalid mode 2 replaced with mode 0','detected':negative_detected},'reference_sha256':hashlib.sha256(CODE.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'tool_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(blob).hexdigest(),'helper_relocations':links,'scope':'synthetic direct calls; original 0x0019fe4c executed; camera caller composition not run','unicorn':unicorn.__version__}
    (out/'report.json').write_text(json.dumps(rep,indent=2)); print(json.dumps(rep,indent=2)); return 0 if rep['status']=='passed' else 1
if __name__=='__main__': sys.exit(main())
