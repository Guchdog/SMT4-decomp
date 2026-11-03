import argparse, hashlib, json, random, struct, subprocess, sys
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
from unicorn import UcError
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
IMAGE_PATH=ROOT/'extracted/exefs/code.bin'
IMAGE=IMAGE_PATH.read_bytes()
IMAGE_SHA='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
assert hashlib.sha256(IMAGE).hexdigest()==IMAGE_SHA
FUNC=0x0028df54; SLOT=28; GLOBAL=0x0044deb8; ENTRY=0x00286928
REGS=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]

def compile_source(src,out,name):
    clang=str(find_clang()); obj=out/(name+'.o'); binary=out/(name+'.bin')
    cmd=[clang,'--target=armv6k-none-eabihf','-mcpu=mpcore','-mfpu=vfpv2','-mfloat-abi=hard','-O2','-std=c++20','-ffreestanding','-fno-exceptions','-fno-rtti',f'-I{ROOT / "include"}','-c',str(src),'-o',str(obj)]
    subprocess.run(cmd,check=True,capture_output=True,text=True)
    tool=Path(clang).parent/'llvm-objcopy.exe'
    subprocess.run([str(tool),'-O','binary','-j','.text',str(obj),str(binary)],check=True,capture_output=True,text=True)
    return obj,binary.read_bytes(),cmd

def base_uc():
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(0x100000,0x500000); u.mem_write(0x100000,IMAGE)
    u.mem_map(0x700000,0x10000); u.mem_map(0x800000,0x20000); u.mem_map(0x900000,0x20000)
    return u

def compare_tuple(u,state,stop,events,fault=None):
    return {'fault':fault,'r0':u.reg_read(UC_ARM_REG_R0),'sp':u.reg_read(UC_ARM_REG_SP),
            'callee_saved':[u.reg_read(r) for r in REGS],
            'state':bytes(u.mem_read(state,0x180)).hex(),'events':events,
            'semantic_writes':sorted(events),'stopped':stop}

def same_semantics(left,right):
    return ({k:v for k,v in left.items() if k not in ('events','semantic_writes')} ==
            {k:v for k,v in right.items() if k not in ('events','semantic_writes')} and
            left['semantic_writes']==right['semantic_writes'])

def run_direct(body,case,patched):
    seed,value,state=case; u=base_uc(); rng=random.Random(seed)
    initial=bytes(rng.randrange(256) for _ in range(0x180)); u.mem_write(state,initial)
    u.mem_write(GLOBAL,struct.pack('<I',state)); u.reg_write(UC_ARM_REG_R0,value)
    sp=0x81ff00; lr=0x80f000; u.reg_write(UC_ARM_REG_SP,sp); u.reg_write(UC_ARM_REG_LR,lr)
    for i,r in enumerate(REGS): u.reg_write(r,0x11110000+i)
    events=[]; stopped=False; fault=None
    def write_hook(uc,access,address,size,val,data):
        if state <= address < state+0x180: events.append([address,size,val & ((1<<(8*size))-1)])
    def code_hook(uc,address,size,data):
        nonlocal stopped
        if address==lr: stopped=True; uc.emu_stop()
    u.hook_add(UC_HOOK_MEM_WRITE,write_hook); u.hook_add(UC_HOOK_CODE,code_hook)
    if patched: u.mem_write(0x700000,body)
    try: u.emu_start(0x700000 if patched else FUNC,0,count=100)
    except UcError as e: fault=type(e).__name__+': '+str(e)
    return compare_tuple(u,state,stopped,events,fault)

def run_state5(body,seed,patched):
    u=base_uc(); rng=random.Random(seed+0xD054); obj=0x900000+(seed%16)*0x1000; state=0x805000+(seed%8)*0x1000
    ob=bytearray(rng.randrange(256) for _ in range(0x1200)); payload=(0xA5000000 | seed) & 0xffffffff
    ob[8]=5; struct.pack_into('<I',ob,0x18,payload); u.mem_write(obj,bytes(ob))
    st=bytes(rng.randrange(256) for _ in range(0x180)); u.mem_write(state,st)
    u.mem_write(0x43e18c,struct.pack('<I',obj)); u.mem_write(GLOBAL,struct.pack('<I',state))
    sp=0x81ff00; lr=0x80f000; u.reg_write(UC_ARM_REG_SP,sp); u.reg_write(UC_ARM_REG_LR,lr)
    u.reg_write(UC_ARM_REG_R0,0x13572468); u.reg_write(UC_ARM_REG_R1,0x24681357); u.reg_write(UC_ARM_REG_R2,1); u.reg_write(UC_ARM_REG_R3,6)
    u.mem_write(sp,struct.pack('<II',1,0)); u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
    for i,r in enumerate(REGS): u.reg_write(r,0x22220000+i)
    if patched: u.mem_write(FUNC,body[:SLOT].ljust(SLOT,b'\0'))
    events=[]; calls=[]; stopped=False; fault=None
    def write_hook(uc,access,address,size,val,data):
        if state <= address < state+0x180: events.append([address,size,val & ((1<<(8*size))-1)])
    def code_hook(uc,address,size,data):
        nonlocal stopped
        if address==FUNC: calls.append(address)
        if address==lr: stopped=True; uc.emu_stop()
    u.hook_add(UC_HOOK_MEM_WRITE,write_hook); u.hook_add(UC_HOOK_CODE,code_hook)
    try: u.emu_start(ENTRY,0,count=5000)
    except UcError as e: fault=type(e).__name__+': '+str(e)
    result=compare_tuple(u,state,stopped,events,fault)
    result.update({'object':bytes(u.mem_read(obj,0x1200)).hex(),'helper_entries':calls,'expected_payload':payload})
    return result

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--out',required=True); ap.add_argument('--seed',type=int,default=20261102); ap.add_argument('--random-cases',type=int,default=64); a=ap.parse_args()
    out=(ROOT/a.out).resolve(); out.mkdir(parents=True,exist_ok=False)
    src=ROOT/'experiments/semantic_equivalence/h2_df54_candidate.cpp'; prod=ROOT/'src/engine/leaf_batch22_b.cpp'
    cobj,body,ccmd=compile_source(src,out,'candidate'); pobj,pbin,pcmd=compile_source(prod,out,'production')
    prod_body=extract_elf_functions_detailed(pobj)['battle_func_0028df54'][0]
    # Negative control writes the wrong byte value, which must change final state.
    mutsrc=out/'mutant.cpp'; st=src.read_text(encoding='utf-8')
    old='bytes[0x3b] = 0;\n    *reinterpret_cast<volatile uint32_t*>(bytes + 0xa8) = value;'
    assert st.count(old)==1
    mutsrc.write_text(st.replace('bytes[0x3b] = 0;','bytes[0x3b] = 1;'),encoding='utf-8')
    _,mutbody,_=compile_source(mutsrc,out,'mutant')
    cases=[]
    for i in range(a.random_cases):
        state=0x900000+(i%16)*0x1000; rng=random.Random(a.seed+i*101)
        cases.append((a.seed+i,rng.getrandbits(32),state))
    # Raw r0 is scalar data even when its bits equal addresses around the destination object.
    alias_state=0x910000
    for i,val in enumerate([0,0xffffffff,alias_state,alias_state+0x3b,alias_state+0xa8,GLOBAL]):
        cases.append((a.seed+10000+i,val,alias_state))
    direct=0; mutant_detected=0
    for case in cases:
        ref=run_direct(body,case,False); got=run_direct(body,case,True); prod_result=run_direct(prod_body,case,True)
        assert same_semantics(ref,got),('original/candidate direct mismatch',case,ref,got)
        assert same_semantics(ref,prod_result),('candidate/production mismatch',case,ref,prod_result)
        if not same_semantics(run_direct(mutbody,case,True),ref): mutant_detected+=1
        direct+=1
    compositions=[]; caller_mutant_detected=0
    for i in range(8):
        seed=a.seed+20000+i
        ref=run_state5(body,seed,False); got=run_state5(body,seed,True)
        prodcaller=run_state5(prod_body,seed,True)
        assert same_semantics(ref,got),('state5 composition mismatch',seed,ref,got)
        assert same_semantics(ref,prodcaller),('production state5 composition mismatch',seed,ref,prodcaller)
        assert ref['helper_entries']==[FUNC],('state5 did not call helper exactly once',seed,ref['helper_entries'])
        assert prodcaller['helper_entries']==[FUNC],('production did not call helper exactly once',seed,prodcaller['helper_entries'])
        assert ref['r0']==1 and int(ref['state'][2*(0xA8):2*(0xA8+4)],16)>=0,('unexpected state5 result',seed)
        assert ref['events']==[[0x805000+(seed%8)*0x1000+0x3b,1,0],[0x805000+(seed%8)*0x1000+0xa8,4,ref['expected_payload']]],('unexpected helper write order',seed,ref['events'])
        mut=run_state5(mutbody,seed,True)
        if not same_semantics(mut,ref): caller_mutant_detected+=1
        compositions.append({'seed':seed,'return':ref['r0'],'helper_entries':len(ref['helper_entries']),
          'original_write_order':ref['events'],'candidate_write_order':got['events'],
          'production_write_order':prodcaller['events'],
          'semantic_writes':ref['semantic_writes'],'payload':ref['expected_payload']})
    assert mutant_detected==len(cases)
    assert caller_mutant_detected==len(compositions)
    detail=extract_elf_functions_detailed(cobj)['candidate_0028df54']
    body_detail=detail[0]; reloc=detail[1] if len(detail)>1 else []
    assert len(body)<=SLOT,(len(body),SLOT)
    assert not reloc,reloc
    assert len(prod_body)<=SLOT,(len(prod_body),SLOT)
    report={'passed':True,'scope':'valid mapped writable ordinary RAM; direct helper and original 0x00286928 selector-6 state-5 composition only; write ordering is recorded but excluded from equivalence because writes are disjoint and concurrent observers are outside scope',
      'seed':a.seed,'random_cases':a.random_cases,'direct_cases':direct,'alias_cases':6,'direct_mutation_detected':mutant_detected,
      'state5_compositions':compositions,'caller_mutation_detected':caller_mutant_detected,
      'image_sha256':hashlib.sha256(IMAGE).hexdigest(),'candidate_sha256':sha(src),'production_tu_sha256':sha(prod),
      'candidate_body_bytes':len(body),'production_body_bytes':len(prod_body),'candidate_relocations':reloc,
      'commands':[ccmd,pcmd],'exit_codes':[0,0,0],'limits':['null/invalid global pointer faults are not differentially characterized','no MMIO/concurrent-observer guarantees','0x00286928 dependencies are original pinned code, not fully reconstructed']}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'direct':direct,'state5':len(compositions),'mutations':[mutant_detected,caller_mutant_detected],'body_bytes':[len(body),len(prod_body)],'report':str(out/'report.json')},indent=2))
if __name__=='__main__': main()
