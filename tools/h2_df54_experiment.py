import hashlib, random, struct, subprocess
from pathlib import Path
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE
from unicorn.arm_const import *
ROOT=Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang

OUT=ROOT/'build/df54'
CLANG=str(find_clang())
OBJCOPY=str(Path(CLANG).parent/'llvm-objcopy.exe')
IMAGE=(ROOT/'extracted/exefs/code.bin').read_bytes()
assert hashlib.sha256(IMAGE).hexdigest()=='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
def compile_candidate(src,name):
    obj=OUT/(name+'.o'); binary=OUT/(name+'.bin'); OUT.mkdir(parents=True,exist_ok=True)
    subprocess.run([CLANG,'--target=armv6k-none-eabihf','-mcpu=mpcore','-mfpu=vfpv2','-mfloat-abi=hard','-O2','-std=c++20','-ffreestanding','-fno-exceptions','-fno-rtti','-c',str(src),'-o',str(obj)],check=True)
    subprocess.run([OBJCOPY,'-O','binary','-j','.text',str(obj),str(binary)],check=True)
    return binary.read_bytes()
def execute(body,seed,patched):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(0x100000,0x500000); u.mem_write(0x100000,IMAGE)
    u.mem_map(0x700000,0x10000); u.mem_write(0x700000,body)
    u.mem_map(0x800000,0x10000); u.mem_map(0x900000,0x10000)
    rng=random.Random(seed); state=0x900000+(seed%64)*0x100
    data=bytes(rng.randrange(256) for _ in range(0x100))
    u.mem_write(state,data); u.mem_write(0x44deb8,struct.pack('<I',state))
    value=rng.getrandbits(32); u.reg_write(UC_ARM_REG_R0,value); u.reg_write(UC_ARM_REG_SP,0x80ff00); u.reg_write(UC_ARM_REG_LR,0x80f000)
    regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
    for i,r in enumerate(regs):u.reg_write(r,0x11110000+i)
    stopped=False
    def hook(uc,addr,size,data):
        nonlocal stopped
        if addr==0x80f000:stopped=True;uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,hook)
    u.emu_start(0x700000 if patched else 0x28df54,0,count=100)
    if not stopped:raise AssertionError('function did not return')
    return (u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_SP),[u.reg_read(r) for r in regs],bytes(u.mem_read(state,0x100)))

def execute_real_helper(body,seed,patched):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM); u.mem_map(0x100000,0x500000); u.mem_write(0x100000,IMAGE)
    if patched:u.mem_write(0x28df54,body)
    u.mem_map(0x800000,0x20000); u.mem_map(0x900000,0x10000)
    rng=random.Random(seed); obj=0x900000; state=0x805000
    u.mem_write(obj,bytes(rng.randrange(256) for _ in range(0x1200)))
    u.mem_write(state,bytes(rng.randrange(256) for _ in range(0x200)))
    u.mem_write(obj+8,b'\x05'); u.mem_write(0x43e18c,struct.pack('<I',obj)); u.mem_write(0x44deb8,struct.pack('<I',state))
    sp=0x81ff00; u.reg_write(UC_ARM_REG_SP,sp); u.reg_write(UC_ARM_REG_LR,0x80f000)
    u.reg_write(UC_ARM_REG_R0,0x13572468); u.reg_write(UC_ARM_REG_R1,0x24681357); u.reg_write(UC_ARM_REG_R2,1+seed); u.reg_write(UC_ARM_REG_R3,6)
    u.mem_write(sp,struct.pack('<II',1,0)); u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
    regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
    for i,r in enumerate(regs):u.reg_write(r,0x22220000+i)
    stopped=False
    def hook(uc,addr,size,data):
        nonlocal stopped
        if addr==0x80f000:stopped=True;uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,hook); u.emu_start(0x286928,0,count=5000)
    if not stopped:raise AssertionError('original helper did not return')
    return (u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_SP),[u.reg_read(r) for r in regs],bytes(u.mem_read(obj,0x1200)),bytes(u.mem_read(state,0x200)))

src=ROOT/'experiments/semantic_equivalence/h2_df54_candidate.cpp'
body=compile_candidate(src,'candidate')
prod_obj=OUT/'production.o'
compiled=compile_tu_armv6k(ROOT/'src/engine/leaf_batch22_b.cpp',prod_obj,ROOT)
if compiled.returncode: raise RuntimeError(compiled.stderr)
production=extract_elf_functions_detailed(prod_obj)['battle_func_0028df54'][0]
mut=OUT/'mutant.cpp'; text=src.read_text(); assert text.count('state[0x3b] = 0;')==1
mut.write_text(text.replace('state[0x3b] = 0;','state[0x3b] = 1;'))
mutant=compile_candidate(mut,'mutant')
detected=0
for seed in range(64):
    ref=execute(body,seed,False); got=execute(body,seed,True)
    if ref!=got:raise SystemExit(f'differential mismatch {seed}')
    if execute(body,seed,True)!=execute(production,seed,True):raise SystemExit(f'candidate/production mismatch {seed}')
    if execute(mutant,seed,True)!=ref:detected+=1
    if execute_real_helper(body,seed,False)!=execute_real_helper(production,seed,True):
        raise SystemExit(f'0x00286928 real caller mismatch {seed}')
if detected!=64:raise SystemExit(f'negative control detected {detected}/64')
print(f'PASS 64/64 direct, candidate/production and real 0x00286928 compositions; mutant detected {detected}/64; candidate/production sizes {len(body)}/{len(production)}; original pinned hash verified.')
