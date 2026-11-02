"""Pinned ARM differential for 0x002892C0 and original 0x0029EDFC wrapper."""
import hashlib, json, random, struct, sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

OUT = ROOT / 'build/agent-work/H2-semantic/h2-titleconfig-002892c0-convert/run001'
IMAGE = ROOT / 'extracted/exefs/code.bin'
SOURCE = ROOT / 'experiments/semantic_equivalence/h2_2892c0_candidate.cpp'
BASE, TARGET, WRAPPER = 0x100000, 0x2892c0, 0x29edfc
OBJ, STACK, STOP = 0x900000, 0x80ff000, 0x100fffc
MASK = 0xffffffff

def sha(b): return hashlib.sha256(b).hexdigest()
def compile_candidate(path, obj):
    result = compile_tu_armv6k(path, obj, ROOT)
    if result.returncode: raise RuntimeError(result.stderr)
    body, reloc = extract_elf_functions_detailed(obj)['candidate_002892c0']
    if reloc: raise AssertionError(f'unexpected relocations {reloc}')
    if len(body) % 4: raise AssertionError(f'body alignment {len(body)}')
    return body

def machine(image, body):
    u = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    u.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    u.mem_map(BASE, 0x400000); u.mem_write(BASE, image)
    u.mem_map(OBJ, 0x10000); u.mem_map(0x8000000, 0x100000)
    u.mem_map(0x1000000, 0x10000)
    if body is not None:
        # Private test-only trampoline: do not overwrite the next original symbol.
        cave = 0x01001000
        delta = cave - (TARGET + 8)
        assert delta % 4 == 0 and -(1 << 25) <= delta < (1 << 25)
        u.mem_write(TARGET, struct.pack('<I', 0xea000000 | ((delta >> 2) & 0xffffff)))
        u.mem_write(cave, body)
    return u

def run(u, start, fields, index, disabled=0, flag=0x87):
    data=bytearray((i * 29 + 37) & 255 for i in range(0x100))
    for offset,value in zip((0x10,0x1c,0x20,0x24),fields): struct.pack_into('<I',data,offset,value & MASK)
    data[0x62]=disabled; data[0x60]=flag
    u.mem_write(OBJ,bytes(data))
    regs=[getattr(arm,'UC_ARM_REG_R'+str(i)) for i in range(4,12)]
    saved=[0x14253647 + i*0x10101 for i in range(8)]
    for reg,value in zip(regs,saved): u.reg_write(reg,value)
    u.reg_write(arm.UC_ARM_REG_R0,OBJ);u.reg_write(arm.UC_ARM_REG_R1,index & MASK)
    u.reg_write(arm.UC_ARM_REG_SP,STACK);u.reg_write(arm.UC_ARM_REG_LR,STOP)
    events=[];entered=[];done=[False]
    def on_write(uc,access,address,size,value,user):
        if not STACK-0x1000 <= address < STACK: events.append((address,size,value & ((1 << (size*8))-1)))
    def on_code(uc,address,size,user):
        if address==TARGET: entered.append((uc.reg_read(arm.UC_ARM_REG_R0),uc.reg_read(arm.UC_ARM_REG_R1)))
        if address==STOP: done[0]=True;uc.emu_stop()
    wh=u.hook_add(unicorn.UC_HOOK_MEM_WRITE,on_write); ch=u.hook_add(unicorn.UC_HOOK_CODE,on_code)
    fault=None
    try: u.emu_start(start,0,count=1000)
    except unicorn.UcError as e: fault=str(e)
    finally: u.hook_del(wh);u.hook_del(ch)
    return {'fault':fault,'done':done[0], 'ret':u.reg_read(arm.UC_ARM_REG_R0),
            'sp':u.reg_read(arm.UC_ARM_REG_SP),'saved':[u.reg_read(x) for x in regs],
            'expected_saved':saved,'object':bytes(u.mem_read(OBJ,len(data))),
            'writes':events,'entries':entered}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    image=IMAGE.read_bytes()
    if sha(image) != '1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558': raise AssertionError('image hash')
    body=compile_candidate(SOURCE,OUT/'candidate.o')
    old,new=machine(image,None),machine(image,body)
    cases=[]
    values=[0,1,2,3,0x7fffffff,0x80000000,0xffffffff]
    for count in values:
        for idx in values:
            for start,visible in [(0,0),(2,1),(0xffffffff,0x7fffffff),(0x80000000,0xffffffff)]:
                cases.append((visible,count,start,0xa55a5aa5,idx))
    rng=random.Random(2892)
    for _ in range(1024): cases.append(tuple(rng.getrandbits(32) for _ in range(5)))
    def assert_run(a,b,label):
        if a!=b: raise AssertionError(f'{label} mismatch {a!r} {b!r}')
        if a['fault'] or not a['done'] or a['sp']!=STACK or a['saved']!=a['expected_saved']: raise AssertionError(f'{label} ABI/fault')
        if any(not OBJ<=x[0]<OBJ+0x100 for x in a['writes']): raise AssertionError(f'{label} unexpected write')
    for i,(visible,count,start,end,index) in enumerate(cases):
        a=run(old,TARGET,(visible,count,start,end),index);b=run(new,TARGET,(visible,count,start,end),index)
        assert_run(a,b,f'direct-{i}')
        if a['ret']!=1 or a['entries']!=[(OBJ,index)]: raise AssertionError('direct entry/return')
    caller=0
    for disabled in (0,1,0x80):
        for visible,count,start,end,index in cases[:120]:
            a=run(old,WRAPPER,(visible,count,start,end),index,disabled)
            b=run(new,WRAPPER,(visible,count,start,end),index,disabled)
            assert_run(a,b,f'caller-{caller}')
            if len(a['entries']) != (0 if disabled else 1): raise AssertionError('wrapper helper entry')
            caller+=1
    source=SOURCE.read_text(encoding='utf-8-sig')
    mutant=source.replace('signed_less(count, index)', '!signed_less(index, count)')
    if mutant==source: raise AssertionError('mutation failed')
    path=OUT/'mutant.cpp';path.write_text(mutant,encoding='utf-8')
    bad=machine(image,compile_candidate(path,OUT/'mutant.o'))
    detected=False
    for visible,count,start,end,index in cases:
        if run(old,TARGET,(visible,count,start,end),index)!=run(bad,TARGET,(visible,count,start,end),index): detected=True;break
    if not detected: raise AssertionError('negative control escaped')
    result={'image_sha256':sha(image),'source_sha256':sha(SOURCE.read_bytes()),'runner_sha256':sha(Path(__file__).read_bytes()),
            'object_sha256':sha((OUT/'candidate.o').read_bytes()),'body_sha256':sha(body),'body_bytes':len(body),'relocations':0,
            'direct_count':len(cases),'caller_count':caller,'negative_control_detected':detected,'seed':2892,
            'caller':'original 0x0029EDFC through test-only trampoline to candidate at 0x01001000',
            'placement':'test-only trampoline; production code placement unproven','runtime':'not_run'}
    (OUT/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
