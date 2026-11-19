#!/usr/bin/env python3
"""Offline differential for three initializer entries around 0x003F3454."""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys
from pathlib import Path
import unicorn
import capstone
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import arm_branch

REFERENCE = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
TEXT, TEXT_SIZE = 0x00100000, 0x00400000
INJECT, INJECT_SIZE = 0x01000000, 0x10000
STACK, STACK_SIZE, SP = 0x08000000, 0x4000, 0x08003000
RETURN = 0x0100F000
WATCH_A, WATCH_A_SIZE = 0x00471000, 0x3000
ARRAY, ARRAY_SIZE = 0x004E62C0, 0x200
CTOR, VEC_VENEER, VEC_THUMB = 0x00353120, 0x002C5F50, 0x002C5F58
SOURCE = ROOT / "experiments/semantic_equivalence/h18_003f3454_family.cpp"
ENTRIES = {
    0x003F3454: {"symbol":"h18_003f3454_candidate","length":0x3C,"pool":(0x003F3490,0x003F34A0),"candidate_size":None},
    0x003F34A0: {"symbol":"h18_003f34a0_candidate","length":0x24,"pool":(0x003F34C4,0x003F34CC),"candidate_size":None},
    0x003F34CC: {"symbol":"h18_003f34cc_candidate","length":0x24,"pool":(0x003F34F0,0x003F34F8),"candidate_size":None},
}
FUNC_BY_NAME = {x["symbol"]:a for a,x in ENTRIES.items()}

def compile_candidates(out:Path,source=SOURCE,name="candidate"):
    obj=out/f"{name}.o"
    result=compile_tu_armv6k(source,obj,ROOT)
    if result.returncode: raise RuntimeError(result.stderr or "ARMv6K compile failed")
    extracted=extract_elf_functions_detailed(obj)
    code_map={}; info={"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
                      "object_sha256":hashlib.sha256(obj.read_bytes()).hexdigest(),"symbols":{}}
    for address,item in ENTRIES.items():
        symbol=item["symbol"]
        if symbol not in extracted: raise ValueError(f"missing candidate symbol {symbol}")
        code,relocs=extracted[symbol]
        if relocs: raise ValueError(f"unsupported relocations for {symbol}: {relocs}")
        code_map[address]=code
        info["symbols"][symbol]={"size":len(code),"sha256":hashlib.sha256(code).hexdigest()}
    return code_map,info

def fixture(seed,index):
    rng=random.Random(seed ^ (index*0x45D9F3B))
    return {"watch":rng.randbytes(WATCH_A_SIZE),"array":rng.randbytes(ARRAY_SIZE),
            "regs":[rng.getrandbits(32) for _ in range(13)],"flags":index%16}

class Machine:
    def __init__(self,image,code,address,fx):
        self.uc=unicorn.Uc(unicorn.UC_ARCH_ARM,unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT,TEXT_SIZE,unicorn.UC_PROT_ALL)
        self.uc.mem_write(TEXT,image)
        self.uc.mem_map(INJECT,INJECT_SIZE,unicorn.UC_PROT_ALL)
        self.uc.mem_map(STACK,STACK_SIZE,unicorn.UC_PROT_ALL)
        self.uc.mem_write(WATCH_A,fx["watch"])
        self.uc.mem_write(ARRAY,fx["array"])
        if code is not None:
            self.uc.mem_write(INJECT,code)
            self.uc.mem_write(address,arm_branch(address,INJECT))
        self.address,self.fx=address,fx
        self.calls=[]; self.writes=[]; self.fault=None; self.stopped=False
        self.uc.reg_write(arm.UC_ARM_REG_CPSR,0x10|(fx["flags"]<<28))
        for i,v in enumerate(fx["regs"]): self.uc.reg_write(getattr(arm,f"UC_ARM_REG_R{i}"),v)
        self.uc.reg_write(arm.UC_ARM_REG_SP,SP); self.uc.reg_write(arm.UC_ARM_REG_LR,RETURN)
        self.uc.hook_add(unicorn.UC_HOOK_CODE,self._code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE,self._write)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_INVALID,self._invalid)

    def _r(self,n): return self.uc.reg_read(getattr(arm,f"UC_ARM_REG_R{n}"))&0xffffffff
    def _read(self,a,n): return bytes(self.uc.mem_read(a,n))
    def _write(self,uc,access,address,size,value,_):
        if not (STACK <= address < STACK + STACK_SIZE):
            self.writes.extend(range(address,address+size))
    def _invalid(self,uc,access,address,size,value,_):
        self.fault={"access":int(access),"address":hex(address),"size":size}; return False

    def _code(self,uc,address,size,_):
        if address==RETURN:
            self.stopped=True; uc.emu_stop(); return
        if address!=VEC_THUMB: return
        cpsr=uc.reg_read(arm.UC_ARM_REG_CPSR)&0xffffffff
        args=[self._r(i) for i in range(4)]
        ctor_bytes=self._read(CTOR,4)
        constructor_model="bx_lr_no_object_writes" if ctor_bytes==bytes.fromhex("1eff2fe1") else "unknown"
        entry={"helper":"vector_constructor_iterator","entry":hex(VEC_THUMB),"thumb_state":bool(cpsr&(1<<5)),
               "args":[hex(v) for v in args],"constructor":hex(args[1]),"stride":args[2],"count":args[3],
               "constructor_pointer_state":"ARM" if not (args[1]&1) else "Thumb",
               "constructor_model":constructor_model,"modeled_callbacks":args[3] if args[1] else 0,
               "return":hex(args[0])}
        self.calls.append(entry)
        if address!=VEC_THUMB or not (cpsr&(1<<5)) or constructor_model!="bx_lr_no_object_writes":
            self.fault={"error":"tail-call interworking or constructor model mismatch"}; uc.emu_stop(); return
        uc.reg_write(arm.UC_ARM_REG_R0,args[0])
        uc.reg_write(arm.UC_ARM_REG_CPSR,cpsr&~(1<<5))
        uc.reg_write(arm.UC_ARM_REG_PC,self._r(14)&~1)

    def run(self):
        try: self.uc.emu_start(self.address,0,count=10000)
        except unicorn.UcError as exc: self.fault={"error":str(exc)}
        regs={f"r{i}":self._r(i) for i in range(13)}
        regs.update({"sp":self.uc.reg_read(arm.UC_ARM_REG_SP)&0xffffffff,
                    "pc":self.uc.reg_read(arm.UC_ARM_REG_PC)&0xffffffff,
                    "lr":self._r(14),"cpsr":self.uc.reg_read(arm.UC_ARM_REG_CPSR)&0xffffffff})
        return {"regs":regs,"calls":self.calls,"writes":sorted(set(self.writes)),"fault":self.fault,
                "stopped":self.stopped,"watch":self._read(WATCH_A,WATCH_A_SIZE),"array":self._read(ARRAY,ARRAY_SIZE)}

def execute(image,code,address,fx): return Machine(image,code,address,fx).run()

def compare(old,new):
    if old["fault"] or new["fault"]: return f"fault old={old['fault']} new={new['fault']}"
    if not old["stopped"] or not new["stopped"]: return "return continuation not reached"
    for key in ("r0","r4","r5","r6","r7","r8","r9","r10","r11","sp","pc"):
        if old["regs"][key]!=new["regs"][key]: return f"ABI/register differs at {key}"
    if (old["regs"]["cpsr"]&0xF0000000)!=(new["regs"]["cpsr"]&0xF0000000): return "NZCV differs"
    if old["calls"]!=new["calls"]: return "tail helper trace/interworking differs"
    if old["writes"]!=new["writes"]: return "outside-stack byte write set differs"
    if old["watch"]!=new["watch"] or old["array"]!=new["array"]: return "watched memory differs"
    return None

def check_boundaries(image):
    checks={}
    expected_pools={0x003F3454:[0x00471A38,0x00471A48,0x00353120,0x004E62C0],
                    0x003F34A0:[0x00472570,0x00472578],
                    0x003F34CC:[0x00472798,0x004727A0]}
    for address,item in ENTRIES.items():
        start=address- TEXT
        code=image[start:start+item["length"]]
        pool_start,pool_end=item["pool"]
        if len(code)!=item["length"] or pool_end<=pool_start: raise ValueError("entry boundary is outside pinned image")
        pool_words=[struct.unpack_from("<I",image,p-TEXT)[0] for p in range(pool_start,pool_end,4)]
        if pool_words!=expected_pools[address]: raise ValueError(f"literal pool mismatch at {address:#x}")
        checks[hex(address)]={"code_bytes":len(code),"pool":[hex(pool_start),hex(pool_end)],
                               "pool_words":[hex(x) for x in pool_words]}
    cs=capstone.Cs(capstone.CS_ARCH_ARM,capstone.CS_MODE_ARM); cs.detail=True
    tail=list(cs.disasm(image[0x003F348C-TEXT:0x003F3490-TEXT],0x003F348C))
    if len(tail)!=1 or tail[0].mnemonic!="b" or tail[0].operands[0].imm!=VEC_VENEER:
        raise ValueError("0x003F3454 is no longer a tail B to the ARM veneer")
    for ret in (0x003F34C0,0x003F34EC):
        if image[ret-TEXT:ret-TEXT+4]!=bytes.fromhex("1eff2fe1"):
            raise ValueError(f"initializer at {ret:#x} lost BX LR boundary")
    if image[CTOR-TEXT:CTOR-TEXT+4]!=bytes.fromhex("1eff2fe1"): raise ValueError("constructor callback is no longer bx lr")
    if image[VEC_VENEER-TEXT:VEC_VENEER-TEXT+8]!=bytes.fromhex("01c08fe21cff2fe1"): raise ValueError("ARM-to-Thumb veneer changed")
    return checks

def run(image_path:Path,output:Path,seed=7,samples=20):
    output.mkdir(parents=True,exist_ok=True)
    image=image_path.read_bytes()
    if hashlib.sha256(image).hexdigest()!=REFERENCE: raise ValueError("pinned image hash mismatch")
    boundaries=check_boundaries(image)
    candidates,compile_info=compile_candidates(output)
    outcomes={}
    for address,item in ENTRIES.items():
        rows=[]
        for index in range(samples):
            fx=fixture(seed,index)
            old=execute(image,None,address,fx); new=execute(image,candidates[address],address,fx)
            why=compare(old,new)
            rows.append({"case":index,"nzcv_input":fx["flags"],"passed":why is None,"reason":why,
                         "return":hex(old["regs"]["r0"]),"helper_trace":old["calls"]})
        outcomes[hex(address)]={"passed":all(x["passed"] for x in rows),"cases":len(rows),"results":rows}
    source=SOURCE.read_text(encoding="utf-8")
    negative_specs=[
        ("entry_3454_wrong_tail_count","0x40u);","0x20u);",0x003F3454,{"helper":"count"}),
        ("entry_34a0_wrong_sentinel_address","0x00472570u","0x00472574u",0x003F34A0,{"memory":"sentinel"}),
        ("entry_34cc_wrong_zero_address","*reinterpret_cast<u32*>(0x004727A0u) = 0;","*reinterpret_cast<u32*>(0x004727A4u) = 0;",0x003F34CC,{"memory":"zero"}),
    ]
    negative=[]
    for j,(name,before,after,address,_) in enumerate(negative_specs):
        if source.count(before)!=1: raise ValueError(f"negative-control anchor not unique: {name}")
        mutant=output/f"{name}.cpp"; mutant.write_text(source.replace(before,after),encoding="utf-8")
        bad,_=compile_candidates(output,mutant,name)
        fx=fixture(seed^0xABC,j)
        old=execute(image,None,address,fx); changed=execute(image,bad[address],address,fx)
        reason=compare(old,changed)
        negative.append({"name":name,"detected":reason is not None,"difference":reason})
    report={"schema":1,"entries":outcomes,"seed":seed,"samples_per_entry":samples,
            "reference_sha256":REFERENCE,"boundaries":boundaries,"compile":compile_info,
            "passed":all(x["passed"] for x in outcomes.values()) and all(x["detected"] for x in negative),
            "negative_controls":negative,
            "tail_helper_model":{"veneer_arm":hex(VEC_VENEER),"helper_thumb":hex(VEC_THUMB),
              "callback_arm":hex(CTOR),"constructor_entry_bytes":"1eff2fe1",
              "behavior":"The Thumb iterator is intercepted and modeled as count constructor calls at stride 8; the constructor is the verified BX LR stub, so it performs no object writes. The iterator returns the original base pointer.",
              "caller_saved_registers_are_not_compared":True},
            "caller":{"status":"not_run","reason":"No caller composition was identified or exercised."},
            "runtime":"not_run",
            "limitations":["The vector iterator is a deterministic model; only its ARM veneer, Thumb entry address/mode and no-op constructor bytes are tied to the pinned image.",
              "Synthetic RAM fixtures and helper trace do not establish actual startup order, registration, or whole-program effects.",
              "No runtime/emulator or caller-composition comparison was run."]}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image",type=Path,default=ROOT/"extracted/exefs/code.bin")
    p.add_argument("--output",type=Path,required=True); p.add_argument("--seed",type=int,default=7)
    p.add_argument("--samples",type=int,default=20)
    a=p.parse_args(); result=run(a.image,a.output,a.seed,a.samples)
    print(json.dumps({"passed":result["passed"],"entries":{k:v["cases"] for k,v in result["entries"].items()},"report":str(a.output/"report.json")}))
    return 0 if result["passed"] else 1
if __name__=="__main__": raise SystemExit(main())
