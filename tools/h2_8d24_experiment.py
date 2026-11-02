import hashlib, random, struct, subprocess
from pathlib import Path
from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import find_clang
OUT=ROOT/'build/agent-work/H2-semantic/h2-helper-002b8d24-case12-alias-coverage/001'
SRC=ROOT/'experiments/semantic_equivalence/h2_8d24_candidate.cpp'
IMAGE=(ROOT/'extracted/exefs/code.bin').read_bytes()
assert hashlib.sha256(IMAGE).hexdigest()=='1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558'
def compile_code(path,name):
    obj=OUT/(name+'.o')
    subprocess.run([str(find_clang()),'--target=armv6k-none-eabihf','-mcpu=mpcore','-mfpu=vfpv2','-mfloat-abi=hard','-O2','-std=c++20','-ffreestanding','-fno-exceptions','-fno-rtti','-c',str(path),'-o',str(obj)],check=True)
    body,relocs=extract_elf_functions_detailed(obj)['candidate_002b8d24']
    if relocs or len(body)>360: raise ValueError(f'unsupported layout size={len(body)} relocs={len(relocs)}')
    return body
def run(body,seed,selector,mask,bits,caller=False,image=IMAGE):
    u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x100000,0x600000);u.mem_write(0x100000,image)
    if body is not None: u.mem_write(0x2b8d24,body)
    u.mem_map(0x800000,0x20000);u.mem_map(0x900000,0x20000)
    rng=random.Random(seed); obj=0x900000; data=bytearray(rng.randrange(256) for _ in range(0x1200))
    for i in range(5): data[0x37+i]=(mask>>i)&1
    for offset in [0xc4,0x1dc,0x40c]+[0x498+i*140 for i in range(5)]:struct.pack_into('<I',data,offset+0x58,0x914000 if seed==4729 else 0)
    struct.pack_into('<I',data,0xe4,bits)
    for offset in [0xc4,0x268]:struct.pack_into('<I',data,offset+0x48,0x910000)
    data[8]=1;data[9]=selector&255
    u.mem_write(obj,bytes(data));manager=bytearray(0x100)
    if seed==4729:
        struct.pack_into('<H',manager,8,224);struct.pack_into('<I',manager,0x1c,0x912000)
        u.mem_write(0x912000,bytes([255])*(8*28));u.mem_write(0x914000,bytes(rng.randrange(256) for _ in range(0x100)))
    u.mem_write(0x910000,bytes(manager))
    u.mem_write(0x43e18c,struct.pack('<I',obj));u.mem_write(0x43e0b8,struct.pack('<Ii',1,-1));u.mem_write(0x44dc20,bytes(4))
    sp=0x81ff00;lr=0x80f000;u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,lr);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
    u.reg_write(UC_ARM_REG_R0,obj);u.reg_write(UC_ARM_REG_R1,selector if not caller else 0x24681357);u.reg_write(UC_ARM_REG_R2,0x12345678 if not caller else 1);u.reg_write(UC_ARM_REG_R3,0xabcdef12 if not caller else 6)
    u.mem_write(sp,struct.pack('<II',1,0));regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
    for i,r in enumerate(regs):u.reg_write(r,0x12340000+i)
    events=[];writes=[];done=False
    def oncode(uc,a,size,ctx):
        nonlocal done
        if a in (0x2af854,0x2bf030,0x1384f0):
            args=(uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1))
            if a==0x2af854:args+=(uc.reg_read(UC_ARM_REG_R2),)
            events.append((a,args))
        if a==lr:done=True;uc.emu_stop()
    u.hook_add(UC_HOOK_CODE,oncode);u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,k,a,s,v,c:writes.append((a,s,v)) if not 0x81f000<=a<0x820000 else None)
    u.emu_start(0x286928 if caller else 0x2b8d24,0,count=5000)
    if not done:raise AssertionError('no return')
    return (u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_SP),tuple(u.reg_read(r) for r in regs),bytes(u.mem_read(obj,0x1200)),tuple(events),tuple(writes))

def validate_staged_image(image_path,base_image_path=None):
    staged=Path(image_path).read_bytes()
    base=Path(base_image_path).read_bytes() if base_image_path else IMAGE
    if len(staged)!=len(IMAGE) or len(base)!=len(IMAGE):raise AssertionError('staged image length changed')
    cases=[]
    for seed in (17,4729):
      for selector in list(range(20))+[0x80000000,0xffffffff]:
        if selector==6:
          for bits in (0x3f800000,0x3f7fffff,0,0x80000000,0x7f800000,0x7fc00001):cases.append((seed,selector,0,bits))
        elif selector==12:
          for mask in range(32):cases.append((seed,selector,mask,0))
        else:cases.append((seed,selector,0,0))
    for case in cases:
      original=run(None,*case,image=IMAGE)
      patched=run(None,*case,image=staged)
      if original!=patched:raise AssertionError(f'staged image differential mismatch {case}')
    for seed in (17,4729):
      original=run(None,seed,11,0,0,True,image=IMAGE)
      patched=run(None,seed,11,0,0,True,image=staged)
      if original!=patched:raise AssertionError(f'staged caller composition mismatch seed={seed}')
    off=0x2b8d24-0x100000
    if staged[:off]!=base[:off] or staged[off+360:]!=base[off+360:]:
      raise AssertionError('staged image differs from its declared base outside the function slot')
    print(f'PASS staged final image: {len(cases)} direct cases and 2 caller compositions')
if __name__ == '__main__':
    body=compile_code(SRC,'candidate-final');text=SRC.read_text();controls={
     'return6':('if (value != 0x3f800000) return value;','if (value != 0x3f800000) return 0;'),
     'second':('reset(object + 0x1dc, 2, 0);','reset(object + 0x1e0, 2, 0);'),
     'stride':('i * 140','i * 136'),
     'loop_limit':('i < 5','i < 4'),
     'selector':('selector == 1 || selector == 10','selector == 1 || selector == 13'),
     'tail_byte':('set_byte(object + 0x150, 0)','set_byte(object + 0x154, 0)'),
     'clear':('*reinterpret_cast<uint32_t*>(object + 0x28) = 0;','*reinterpret_cast<uint32_t*>(object + 0x28) = 1;')}
    mutants={}
    for name,(old,new) in controls.items():
        assert text.count(old)==1
        p=OUT/(name+'.cpp');p.write_text(text.replace(old,new),encoding='utf-8');mutants[name]=compile_code(p,'mutant-'+name)
    cases=[]
    for seed in (17,4729):
      for selector in list(range(20))+[0x80000000,0xffffffff]:
        if selector==6:
          for bits in (0x3f800000,0x3f7fffff,0,0x80000000,0x7f800000,0x7fc00001):cases.append((seed,selector,0,bits))
        elif selector==12:
          for mask in range(32):cases.append((seed,selector,mask,0))
        else:cases.append((seed,selector,0,0))
    counts={name:0 for name in mutants}
    for case in cases:
        orig=run(None,*case);got=run(body,*case)
        if orig!=got:raise AssertionError(f'mismatch {case}: {[(i,a,b) for i,(a,b) in enumerate(zip(orig,got)) if a!=b and i!=3]}')
        for name,m in mutants.items():
          try:
            if run(m,*case)!=orig:counts[name]+=1
          except UcError:
            counts[name]+=1
    if not all(counts.values()):raise AssertionError(f'undetected controls {counts}')
    for seed in (17,4729):
        if run(None,seed,11,0,0,True)!=run(body,seed,11,0,0,True):raise AssertionError('caller mismatch')
    af_src=ROOT/'experiments/semantic_equivalence/h2_af854_candidate.cpp';af_obj=OUT/'af854-candidate.o'
    subprocess.run([str(find_clang()),'--target=armv6k-none-eabihf','-mcpu=mpcore','-mfpu=vfpv2','-mfloat-abi=hard','-O2','-std=c++20','-ffreestanding','-fno-exceptions','-fno-rtti','-c',str(af_src),'-o',str(af_obj)],check=True)
    af,af_relocs=extract_elf_functions_detailed(af_obj)['candidate_002af854']
    if len(af)!=64 or af_relocs:raise AssertionError('unexpected af854 candidate layout')
    def run_chain(patched,seed):
        u=Uc(UC_ARCH_ARM,UC_MODE_ARM);u.mem_map(0x100000,0x600000);u.mem_write(0x100000,IMAGE)
        if patched:u.mem_write(0x2b8d24,body);u.mem_write(0x2af854,af)
        u.mem_map(0x800000,0x20000);u.mem_map(0x900000,0x20000)
        rng=random.Random(seed);obj=0x900000;data=bytearray(rng.randrange(256) for _ in range(0x1200));subs=[0x498+i*140 for i in range(5)]
        for i in range(5):
            data[0x37+i]=1
            struct.pack_into('<I',data,subs[i]+0x58,0x910000 if i==0 else obj+subs[i-1]+0x20)
            struct.pack_into('<I',data,subs[i]+0x5c,0x89898989)
        u.mem_write(obj,bytes(data));lst=bytearray(0x100);struct.pack_into('<I',lst,60,0x12345678);u.mem_write(0x910000,bytes(lst))
        sp=0x81ff00;lr=0x80f000;u.reg_write(UC_ARM_REG_SP,sp);u.reg_write(UC_ARM_REG_LR,lr);u.reg_write(UC_ARM_REG_R0,obj);u.reg_write(UC_ARM_REG_R1,12);u.reg_write(UC_ARM_REG_FPEXC,0x40000000)
        regs=[UC_ARM_REG_R4,UC_ARM_REG_R5,UC_ARM_REG_R6,UC_ARM_REG_R7,UC_ARM_REG_R8,UC_ARM_REG_R9,UC_ARM_REG_R10,UC_ARM_REG_R11]
        for i,r in enumerate(regs):u.reg_write(r,0x22330000+i)
        events=[];writes=[];done=False
        def oncode(uc,a,size,ctx):
            nonlocal done
            if a==0x2af854:events.append((uc.reg_read(UC_ARM_REG_R0),uc.reg_read(UC_ARM_REG_R1),uc.reg_read(UC_ARM_REG_R2)))
            if a==lr:done=True;uc.emu_stop()
        u.hook_add(UC_HOOK_CODE,oncode);u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,k,a,s,v,c:writes.append((a,s,v)) if not 0x81f000<=a<0x820000 else None)
        u.emu_start(0x2b8d24,0,count=5000)
        if not done:raise AssertionError('case12 chain did not return')
        if events != [(obj+x,5,0) for x in subs]:raise AssertionError(f'wrong five helper entries: {events}')
        values=[struct.unpack('<I',u.mem_read(obj+x+0x20,4))[0] for x in subs]
        if values != [0x12345678,5,5,5,5]:raise AssertionError(f'cross-alias chain mismatch {values}')
        return (u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_SP),tuple(u.reg_read(r) for r in regs),bytes(u.mem_read(obj,0x1200)),tuple(events),tuple(writes))
    for seed in (17,4729):
        if run_chain(False,seed)!=run_chain(True,seed):raise AssertionError(f'case12 cross-alias mismatch seed={seed}')
    print(f'PASS {len(cases)} direct, 2 real 0x286928 compositions, 2 five-call cross-alias chains; negative controls {counts}; original deps in base cases, alias-aware af854 in chain; bodies {len(body)}/{len(af)} bytes')
