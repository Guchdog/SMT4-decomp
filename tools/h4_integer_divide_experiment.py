"""Offline ARM quotient/remainder and ABI differential for 0x002C615C."""
import argparse, hashlib, json, random, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.build_check import compile_tu_armv6k, find_clang
from tools.asm_diff import extract_elf_functions_detailed
import unicorn
from unicorn import arm_const as a
CODE=ROOT/'extracted/exefs/code.bin'; SRC=ROOT/'experiments/semantic_equivalence/h4_integer_divide_candidate.cpp'
CAND=0x1000000; STOP=0x100f000; STACK=0x8000000; SP=STACK+0x2000
sha=lambda b: hashlib.sha256(b).hexdigest()
REGS=[a.UC_ARM_REG_R4,a.UC_ARM_REG_R5,a.UC_ARM_REG_R6,a.UC_ARM_REG_R7,a.UC_ARM_REG_R8,a.UC_ARM_REG_R9,a.UC_ARM_REG_R10,a.UC_ARM_REG_R11]
def build(src,obj):
    p=compile_tu_armv6k(src,obj,ROOT)
    if p.returncode: raise RuntimeError(p.stderr)
    raw,relocs=extract_elf_functions_detailed(obj)['h4_integer_divide_candidate']
    if relocs: raise ValueError('unexpected relocations '+repr(relocs))
    return raw

def run(image,blob,entry,x,y):
    u=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM); u.ctl_set_cpu_model(a.UC_CPU_ARM_11MPCORE)
    u.mem_map(0x100000,0x480000,7);u.mem_write(0x100000,image);u.mem_map(CAND,0x10000,7);u.mem_write(CAND,blob);u.mem_map(STACK,0x4000,3)
    regs=[0x12340000+i*0x101 for i in range(8)]
    for r,v in zip(REGS,regs): u.reg_write(r,v)
    for r,v in [(a.UC_ARM_REG_R0,x),(a.UC_ARM_REG_R1,y),(a.UC_ARM_REG_SP,SP),(a.UC_ARM_REG_LR,STOP)]: u.reg_write(r,v)
    writes=[]
    def wh(uc,access,address,size,value,user): writes.append({'address':hex(address),'size':size,'value':hex(value & ((1<<(8*size))-1)),'stack':STACK<=address and address+size<=STACK+0x4000})
    u.hook_add(unicorn.UC_HOOK_MEM_WRITE,wh)
    fault=None
    try: u.emu_start(entry,STOP,count=10000)
    except unicorn.UcError as e: fault=str(e)
    return {'r0':u.reg_read(a.UC_ARM_REG_R0),'r1':u.reg_read(a.UC_ARM_REG_R1),'sp':u.reg_read(a.UC_ARM_REG_SP),'saved':[u.reg_read(r) for r in REGS],'returned':u.reg_read(a.UC_ARM_REG_PC)==STOP,'fault':fault,'writes':writes}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out-dir',required=True);ap.add_argument('--seed',type=int,default=20261028);ap.add_argument('--random-cases',type=int,default=512); args=ap.parse_args()
    out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=False);obj=out/'candidate.o';blob=build(SRC,obj);image=CODE.read_bytes()
    text=SRC.read_text(encoding='utf-8-sig'); before='return static_cast<u64>(dividend) << 32;'; after='return 0;'
    if text.count(before)!=1: raise ValueError('mutation anchor mismatch')
    mut_src=out/'mutant.cpp';mut_src.write_text(text.replace(before,after),encoding='utf-8');mut_obj=out/'mutant.o';mut=build(mut_src,mut_obj)
    vals=[0,1,2,3,5,17,0x7fffffff,0x80000000,0x80000001,0xfffffffb,0xffffffff]; cases=[(x,y) for x in vals for y in vals]
    rng=random.Random(args.seed);cases += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(args.random_cases)]
    diffs=[];results=[];zero_stack=[];candidate_stack=[];nonstack=[]
    for x,y in cases:
        old=run(image,blob,0x2c615c,x,y);new=run(image,blob,CAND,x,y)
        if any(not w['stack'] for w in old['writes']+new['writes']): nonstack.append([hex(x),hex(y)])
        if y==0 and len(zero_stack)<3: zero_stack.append({'input':[hex(x),hex(y)],'original':old['writes'],'candidate':new['writes']})
        if len(candidate_stack)<1 and new['writes']: candidate_stack.append(new['writes'])
        keys=['r0','r1','sp','saved','returned','fault']
        results.append({'input':[hex(x),hex(y)],'original':{k:old[k] for k in keys},'candidate':{k:new[k] for k in keys}})
        if any(old[k]!=new[k] for k in keys) or old['fault'] or not old['returned'] or old['sp']!=SP or old['saved']!=[0x12340000+i*0x101 for i in range(8)] or any(not w['stack'] for w in old['writes']+new['writes']): diffs.append({'input':[hex(x),hex(y)],'original':old,'candidate':new})
    negative_input=(17,0);baseline=run(image,blob,0x2c615c,*negative_input);bad=run(image,mut,CAND,*negative_input);detected=(baseline['r0'],baseline['r1'])!=(bad['r0'],bad['r1'])
    report={'status':'passed' if not diffs and detected else 'failed','scope':'direct ARM function return r0/r1, SP and r4-r11; stack writes separately reported; flags, full memory faults, caller composition and runtime excluded','seed':args.seed,'random_cases':args.random_cases,'case_count':len(cases),'difference_count':len(diffs),'case_results':results,'first_counterexample':diffs[0] if diffs else None,'nonstack_write_cases':nonstack,'zero_divisor_stack_examples':zero_stack,'candidate_stack_example':candidate_stack,'reference_sha256':sha(image),'source_sha256':sha(SRC.read_bytes()),'runner_sha256':sha(Path(__file__).read_bytes()),'object_sha256':sha(obj.read_bytes()),'candidate_sha256':sha(blob),'candidate_length':len(blob),'relocations':[],'compiler':str(find_clang()),'unicorn':unicorn.__version__,'scalar_return':'unsigned long long (AAPCS r0 low, r1 high); validated by differential outputs','mutation':{'source_before':before,'source_after':after,'source_sha256':sha(mut_src.read_bytes()),'object_sha256':sha(mut_obj.read_bytes()),'linked_bytes_sha256':sha(mut),'input':[hex(v) for v in negative_input],'original':baseline,'mutant':bad,'detected':detected}}
    (out/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps({'status':report['status'],'cases':len(cases),'differences':len(diffs),'mutation_detected':detected,'first_counterexample':report['first_counterexample']},indent=2));return 0 if report['status']=='passed' else 1
if __name__=='__main__':sys.exit(main())

