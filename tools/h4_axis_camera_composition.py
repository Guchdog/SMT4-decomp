"""Reproducible bounded 0x001FA948 ARM camera caller composition."""
import argparse, hashlib, json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from tools.build_check import compile_tu_armv6k
from tools.asm_diff import extract_elf_functions_detailed
from tools.h4_axis_reader_experiment import link, run as direct_run, CAND, DEAD, CODE, SRC
import unicorn
from unicorn import arm_const as a
SITE=0x1fa948; END=0x1faa84; VIEW=0x2012000; SLOT=0x2013000; CTX=0x2014000; STACK=0x8000000; SP=STACK+0x2000
sha=lambda b:hashlib.sha256(b).hexdigest()

def bl_word(site,target):
    delta=target-(site+8)
    if (site|target|delta)&3 or not -(1<<25)<=delta<(1<<25): raise ValueError('unsafe ARM BL')
    return 0xeb000000|((delta>>2)&0xffffff)

def execute(image, blob, case, patched):
    u=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM); u.ctl_set_cpu_model(a.UC_CPU_ARM_11MPCORE)
    u.mem_map(0x100000,0x480000,7); u.mem_write(0x100000,image); u.mem_map(CAND,0x10000,7); u.mem_write(CAND,blob)
    u.mem_map(0x2000000,0x20000,3); u.mem_map(STACK,0x4000,3)
    u.reg_write(a.UC_ARM_REG_FPEXC,0x40000000); u.reg_write(a.UC_ARM_REG_C1_C0_2,0xf00000)
    if patched: u.mem_write(SITE,struct.pack('<I',bl_word(SITE,CAND)))
    u.mem_write(VIEW,b'\x11'*0x200); u.mem_write(SLOT,struct.pack('<I',VIEW)); u.mem_write(CTX+0x368,struct.pack('<I',2))
    u.mem_write(SP,b'\xa5'*8)
    state=bytearray(0x20); struct.pack_into('<III',state,0,0x2010000,1,0); struct.pack_into('<f',state,0x14,case['threshold']); u.mem_write(0x4650a0,bytes(state))
    cal=bytearray(0x20); struct.pack_into('<hhh',cal,0xc,0,0,0); struct.pack_into('<hhh',cal,0x12,100,100,100); u.mem_write(0x2010000,bytes(cal))
    sample=bytearray(0x30); struct.pack_into('<hh',sample,12,case['x'],case['y']); u.mem_write(0x4e3c28,bytes(sample))
    for reg,val in [(a.UC_ARM_REG_SP,SP),(a.UC_ARM_REG_R0,SP+4),(a.UC_ARM_REG_R1,SP),(a.UC_ARM_REG_R2,0),(a.UC_ARM_REG_R3,0x437a0000),(a.UC_ARM_REG_R4,0x2016000),(a.UC_ARM_REG_R5,0x2017000),(a.UC_ARM_REG_R6,0),(a.UC_ARM_REG_R8,SLOT),(a.UC_ARM_REG_R9,CTX),(a.UC_ARM_REG_R10,0x5a)]: u.reg_write(reg,val)
    calls=[]; reader=[]
    def hook(uc,addr,size,user):
        if addr==DEAD: calls.append({'threshold_bits':hex(uc.reg_read(a.UC_ARM_REG_S0)),'value_bytes':bytes(uc.mem_read(uc.reg_read(a.UC_ARM_REG_R0),4)).hex()})
        if addr==0x1fa94c: reader.append({'return':uc.reg_read(a.UC_ARM_REG_R0),'stack_y_then_x':bytes(uc.mem_read(SP,8)).hex()})
        if addr==END: uc.emu_stop()
    u.hook_add(unicorn.UC_HOOK_CODE,hook)
    try: u.emu_start(SITE,END,count=10000)
    except unicorn.UcError as e: return {'fault':str(e),'pc':hex(u.reg_read(a.UC_ARM_REG_PC))}
    return {'reader':reader,'deadzone_calls':calls,'r6':u.reg_read(a.UC_ARM_REG_R6),'view_prefix':bytes(u.mem_read(VIEW,0x170)).hex(),'stop':hex(u.reg_read(a.UC_ARM_REG_PC))}

def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--out-dir',required=True); args=ap.parse_args()
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=False); obj=out/'candidate.o'; build=compile_tu_armv6k(SRC,obj,ROOT)
    if build.returncode: raise RuntimeError(build.stderr)
    raw,rels=extract_elf_functions_detailed(obj)['h4_axis_reader_candidate']; blob,links=link(raw,rels); image=CODE.read_bytes()
    orig=struct.unpack_from('<I',image,SITE-0x100000)[0]; expected=bl_word(SITE,0x27fbc8)
    if orig!=expected: raise ValueError('pinned callsite differs')
    cases=[{'name':'neutral','x':0,'y':0,'threshold':0.0},{'name':'positive','x':60,'y':0,'threshold':0.0},{'name':'negative','x':-60,'y':0,'threshold':0.0},{'name':'plus-half','x':50,'y':0,'threshold':0.0},{'name':'minus-half','x':-50,'y':0,'threshold':0.0},{'name':'deadzone-zero','x':10,'y':0,'threshold':0.25}]
    rows=[]
    for c in cases:
        old=execute(image,blob,c,False); new=execute(image,blob,c,True); rows.append({'input':c,'original':old,'candidate':new,'equal':old==new and old.get('stop')==hex(END)})
    mutant=bytearray(blob); before=bytes(mutant[0x30:0x34]); w=struct.unpack_from('<I',mutant,0x30)[0]
    if w & 0xfff != 1: raise ValueError('unexpected mutation instruction')
    struct.pack_into('<I',mutant,0x30,w & ~0xfff); after=bytes(mutant[0x30:0x34]); (out/'mutant.bin').write_bytes(mutant)
    control={'max':1,'flags':0,'threshold':0.0,'lo':[-100,-200,-32768],'hi':[100,200,32767],'selector':0,'mode':1,'samples':[(0,0),(50,-100),(-32768,32767)],'xout':True,'yout':True}
    control_o=direct_run(0x27fbc8,blob,control); control_m=direct_run(CAND,bytes(mutant),control)
    report={'status':'passed' if all(r['equal'] for r in rows) and control_o!=control_m else 'failed','scope':'synthetic call-site 0x001FA948 to stop 0x001FAA84, not full camera task; ABI write-set/FPSCR/fault, physical input and rendered camera unproven','reference_sha256':sha(image),'source_sha256':sha(SRC.read_bytes()),'script_sha256':sha(Path(__file__).read_bytes()),'object_sha256':sha(obj.read_bytes()),'candidate_sha256':sha(blob),'unicorn':unicorn.__version__,'patch':{'site':hex(SITE),'original_word':hex(orig),'original_target':'0x27fbc8','replacement_word':hex(bl_word(SITE,CAND)),'candidate_address':hex(CAND),'displacement_bytes':CAND-(SITE+8),'aligned':True,'in_arm_bl_range':True,'helper_relocations':[{'site':hex(CAND+r.offset),'symbol':r.symbol_name,'type':r.relocation_type,'original_word':hex(struct.unpack_from('<I',raw,r.offset)[0]),'linked_word':hex(struct.unpack_from('<I',blob,r.offset)[0]),'target':hex(DEAD)} for r in rels],'helper_target':hex(DEAD)},'fixture':{'sp':hex(SP),'r0':'SP+4','r1':'SP','r2':0,'r3':'0x437a0000','r8':hex(SLOT),'r9':hex(CTX),'r10':'0x5a','r6':0,'view_address':hex(VIEW),'view_initial':'0x11 repeated','context_368':2,'calibration_low':0,'calibration_high':100,'mode_max':1,'flags':0,'stack_initial':'a5 repeated'},'cases':rows,'mutation':{'offset':'0x30','before':before.hex(),'after':after.hex(),'mutant_sha256':sha(mutant),'input':control,'original':control_o,'mutant':control_m,'detected':control_o!=control_m}}
    (out/'report.json').write_text(json.dumps(report,indent=2)); print(json.dumps({'status':report['status'],'cases':len(rows),'mutation_detected':report['mutation']['detected']},indent=2)); return 0 if report['status']=='passed' else 1
if __name__=='__main__': sys.exit(main())

