"""Offline selector-0/1 caller composition for the H4 integer-divider candidate."""
import argparse, hashlib, json, random, struct, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed
import unicorn
from unicorn import arm_const as a

CODE=ROOT/'extracted/exefs/code.bin'
SRC=ROOT/'experiments/semantic_equivalence/h4_integer_divide_candidate.cpp'
DIV=0x2C615C
DIV_SIZE=556
BASE=0x100000
OUT=0x2011000
STACK=0x8000000
SP=STACK+0x2000
STOP=0x100F000
RANGE=[a.UC_ARM_REG_R4,a.UC_ARM_REG_R5,a.UC_ARM_REG_R6,a.UC_ARM_REG_R7,
       a.UC_ARM_REG_R8,a.UC_ARM_REG_R9,a.UC_ARM_REG_R10,a.UC_ARM_REG_R11]
sha=lambda b:hashlib.sha256(b).hexdigest()

def compile_candidate(source,obj):
    result=compile_tu_armv6k(source,obj,ROOT)
    if result.returncode:raise RuntimeError(result.stderr)
    raw,relocs=extract_elf_functions_detailed(obj)['h4_integer_divide_candidate']
    if relocs:raise ValueError('candidate has relocations: '+repr(relocs))
    if len(raw)>DIV_SIZE or len(raw)%4:raise ValueError(f'candidate size invalid for replacement: {len(raw)}')
    return raw

def replace_divider(image,body):
    offset=DIV-BASE
    if image[offset:offset+DIV_SIZE]==b'':raise ValueError('divider range outside code image')
    replacement=body+b'\x00\x00\xa0\xe1'*((DIV_SIZE-len(body))//4)
    patched=bytearray(image);patched[offset:offset+DIV_SIZE]=replacement
    if bytes(patched[offset:offset+len(body)])!=body:raise ValueError('replacement body verification failed')
    if bytes(patched[offset+len(body):offset+DIV_SIZE])!=b'\x00\x00\xa0\xe1'*((DIV_SIZE-len(body))//4):raise ValueError('replacement padding verification failed')
    return bytes(patched),replacement

def run(image,entry,x,y,aa,bb,alias='normal'):
    uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(a.UC_CPU_ARM_11MPCORE)
    uc.mem_map(BASE,0x480000,7);uc.mem_write(BASE,image)
    uc.mem_map(0x2000000,0x20000,3);uc.mem_map(STACK,0x4000,3)
    uc.mem_map(STOP,0x1000,7)
    uc.mem_write(OUT,b'\xa5'*0x20)
    struct.pack_into('<ii',bytearray(8),0,aa,bb)
    stackargs=struct.pack('<ii',aa,bb)
    uc.mem_write(SP,stackargs)
    if alias=='same':xptr,yptr=OUT,OUT
    elif alias=='swapped':xptr,yptr=OUT+2,OUT
    elif alias=='x-null':xptr,yptr=0,OUT+2
    elif alias=='y-null':xptr,yptr=OUT,0
    else:xptr,yptr=OUT,OUT+2
    for r,v in zip(RANGE,[0x52520004+i*0x101 for i in range(8)]):uc.reg_write(r,v)
    for r,v in [(a.UC_ARM_REG_R0,xptr),(a.UC_ARM_REG_R1,yptr),
                (a.UC_ARM_REG_R2,x&0xffffffff),(a.UC_ARM_REG_R3,y&0xffffffff),
                (a.UC_ARM_REG_SP,SP),(a.UC_ARM_REG_LR,STOP)]:uc.reg_write(r,v)
    writes=[];div_calls=[]
    def code_hook(u,addr,size,user):
        if addr==DIV:
            n=u.reg_read(a.UC_ARM_REG_R0);d=u.reg_read(a.UC_ARM_REG_R1)
            div_calls.append((n,d))
    def write_hook(u,access,address,size,value,user):
        stack=STACK<=address and address+size<=STACK+0x4000
        writes.append({'address':hex(address),'size':size,'value':hex(value&((1<<(size*8))-1)),'stack':stack})
    uc.hook_add(unicorn.UC_HOOK_CODE,code_hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,write_hook)
    fault=None;fault_pc=None
    try:uc.emu_start(entry,STOP,count=100000)
    except unicorn.UcError as exc:
        fault=str(exc);fault_pc=hex(uc.reg_read(a.UC_ARM_REG_PC))
    nonstack=[w for w in writes if not w['stack']]
    return {'fault':fault,'fault_pc':fault_pc,'returned':uc.reg_read(a.UC_ARM_REG_PC)==STOP,
            'r0':uc.reg_read(a.UC_ARM_REG_R0),'r1':uc.reg_read(a.UC_ARM_REG_R1),
            'sp':uc.reg_read(a.UC_ARM_REG_SP),'saved':[uc.reg_read(r) for r in RANGE],
            'output':bytes(uc.mem_read(OUT,0x20)).hex(),'nonstack_writes':nonstack,
            'stack_write_count':len(writes)-len(nonstack),'div_call_count':len(div_calls),
            'zero_divisor_call_count':sum(1 for _,d in div_calls if d==0),
            'div_inputs':[[hex(n),hex(d)] for n,d in div_calls]}

def same_observable(old,new):
    keys=('fault','fault_pc','returned','r0','r1','sp','saved','output','nonstack_writes')
    return all(old[k]==new[k] for k in keys)

def make_cases(seed,random_cases):
    vals=[0,1,-1,36,-36,40,-40,400,-400,-32768,32767]
    calibrations=[(0,0),(0,100),(10,100),(-100,100),(100,-100),(32767,-32768),(-32768,32767)]
    cases=[]
    for caller in (0x13B9FC,0x13B8F8):
        label='selector-0' if caller==0x13B9FC else 'selector-1'
        for aa,bb in calibrations:
            for x in vals:
                for y in vals:
                    cases.append((label,caller,x,y,aa,bb,'normal'))
        for alias in ('same','swapped','x-null','y-null'):
            for x,y,aa,bb in [(400,0,0,0),(100,-36,10,100),(-32768,32767,-32768,32767),(0,0,0,100)]:
                cases.append((label,caller,x,y,aa,bb,alias))
    rng=random.Random(seed)
    for caller in (0x13B9FC,0x13B8F8):
        label='selector-0' if caller==0x13B9FC else 'selector-1'
        for i in range(random_cases):
            cases.append((label,caller,rng.randrange(-32768,32768),rng.randrange(-32768,32768),
                          rng.randrange(-32768,32768),rng.randrange(-32768,32768),'normal'))
    return cases

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out-dir',required=True);ap.add_argument('--seed',type=int,default=20261028)
    ap.add_argument('--random-cases-per-caller',type=int,default=128)
    args=ap.parse_args();out=Path(args.out_dir);out.mkdir(parents=True,exist_ok=False)
    image=CODE.read_bytes();obj=out/'candidate.o';body=compile_candidate(SRC,obj)
    patched,replacement=replace_divider(image,body)
    (out/'candidate-helper-image.bin').write_bytes(patched)
    (out/'candidate-replacement.bin').write_bytes(replacement)
    text=SRC.read_text(encoding='utf-8-sig')
    before='return static_cast<u64>(dividend) << 32;'
    after='return (static_cast<u64>(dividend) << 32) | 1u;'
    if text.count(before)!=1:raise ValueError('mutation anchor mismatch')
    mutant_source=out/'mutant.cpp';mutant_source.write_text(text.replace(before,after),encoding='utf-8')
    mutant_obj=out/'mutant.o';mutant_body=compile_candidate(mutant_source,mutant_obj)
    mutant_image,_=replace_divider(image,mutant_body)
    cases=make_cases(args.seed,args.random_cases_per_caller)
    diffs=[];faults=[];rows=[];totals={}
    for label,entry,x,y,aa,bb,alias in cases:
        old=run(image,entry,x,y,aa,bb,alias);new=run(patched,entry,x,y,aa,bb,alias)
        key=label;agg=totals.setdefault(key,{'cases':0,'differences':0,'matching_faults':0,'unmatched_faults':0,'zero_div_calls_original':0,'zero_div_calls_candidate':0,'stack_writes_original':0,'stack_writes_candidate':0})
        agg['cases']+=1;agg['zero_div_calls_original']+=old['zero_divisor_call_count'];agg['zero_div_calls_candidate']+=new['zero_divisor_call_count']
        agg['stack_writes_original']+=old['stack_write_count'];agg['stack_writes_candidate']+=new['stack_write_count']
        if old['fault'] or new['fault']:
            matched_fault=old['fault']==new['fault'] and old['fault_pc']==new['fault_pc']
            agg['matching_faults' if matched_fault else 'unmatched_faults']+=1
            faults.append({'caller':label,'input':[x,y,aa,bb],'alias':alias,'matched':matched_fault,'original':old,'candidate':new})
        if not same_observable(old,new):
            agg['differences']+=1
            row={'caller':label,'input':[x,y,aa,bb],'alias':alias,'original':old,'candidate':new}
            if len(diffs)<20:diffs.append(row)
        rows.append({'caller':label,'input':[x,y,aa,bb],'alias':alias,'equal':same_observable(old,new),
                     'original':{k:old[k] for k in ('fault','fault_pc','returned','r0','r1','sp','saved','output','nonstack_writes','stack_write_count','div_call_count','zero_divisor_call_count')},
                     'candidate':{k:new[k] for k in ('fault','fault_pc','returned','r0','r1','sp','saved','output','nonstack_writes','stack_write_count','div_call_count','zero_divisor_call_count')}})
    control_input=(0x13B9FC,400,0,0,0)
    control=[]
    for label,entry in [('selector-0',0x13B9FC),('selector-1',0x13B8F8)]:
        x,y,aa,bb=control_input[1:]
        old=run(image,entry,x,y,aa,bb);mut=run(mutant_image,entry,x,y,aa,bb)
        detected=(not same_observable(old,mut))
        control.append({'caller':label,'input':[x,y,aa,bb],'original':old,'mutated_candidate':mut,
                        'detected':detected,'reached_zero_divisor':old['zero_divisor_call_count']>0})
    unmatched_faults=[x for x in faults if not x['matched']]
    status='passed' if not diffs and not unmatched_faults and all(c['detected'] and c['reached_zero_divisor'] for c in control) else 'failed'
    report={'status':status,'scope':'original selector-0/1 caller bodies with only 0x002C615C replaced by relocation-free experimental candidate; synthetic signed-halfword values/calibration; compare return, output snapshot, SP, r4-r11, faults and ordered non-stack writes. Stack-write identity and flags are recorded/excluded.',
            'seed':args.seed,'random_cases_per_caller':args.random_cases_per_caller,'case_count':len(cases),
            'totals_by_caller':totals,'difference_count':sum(x['differences'] for x in totals.values()),
            'first_counterexamples':diffs,'fault_case_count':len(faults),
            'matching_fault_count':sum(x['matching_faults'] for x in totals.values()),
            'unmatched_fault_count':sum(x['unmatched_faults'] for x in totals.values()),'fault_examples':faults[:20],
            'case_results':rows,'same_input_mutation_controls':control,
            'reference_sha256':sha(image),'candidate_source_sha256':sha(SRC.read_bytes()),
            'runner_sha256':sha(Path(__file__).read_bytes()),'candidate_object_sha256':sha(obj.read_bytes()),
            'candidate_body_sha256':sha(body),'candidate_body_length':len(body),'candidate_relocations':[],
            'replacement_sha256':sha(replacement),'patched_image_sha256':sha(patched),
            'mutant_source_sha256':sha(mutant_source.read_bytes()),'mutant_body_sha256':sha(mutant_body),
            'mutant_image_sha256':sha(mutant_image),'replacement_address':hex(DIV),'replacement_size':DIV_SIZE,
            'replacement_padding':'ARM NOP 0xE1A00000','unicorn':unicorn.__version__}
    (out/'report.json').write_text(json.dumps(report,indent=2));
    print(json.dumps({'status':status,'cases':len(cases),'differences':report['difference_count'],
                      'matching_faults':report['matching_fault_count'],'unmatched_faults':report['unmatched_fault_count'],'controls':control},indent=2))
    return 0 if status=='passed' else 1

if __name__=='__main__':sys.exit(main())
