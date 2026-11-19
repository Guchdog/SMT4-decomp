#!/usr/bin/env python3
"""Bounded differential experiment for the callable entry at 0x002e0dd0."""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys
from pathlib import Path
import capstone
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import arm_branch

FUNC = 0x002E0DD0
ENTRY_BYTES = bytes.fromhex("f0412de900c0a0e10260a0e174809fe50120a0e118509de5")
TEXT = 0x00100000
TEXT_SIZE = 0x00400000
DATA = 0x02000000
DATA_SIZE = 0x1000
STACK = 0x08000000
STACK_SIZE = 0x2000
SP = STACK + 0x1000
INJECT = 0x01000000
RETURN = INJECT + 0x1000
GATE, COUNT, VALUE, CLEANUP = 0x00263534, 0x002B5C2C, 0x00248E58, 0x002390DC
GLOBAL_SLOT = 0x00464FAC
GLOBAL_CONTEXT = DATA + 0x100
OBJECT = DATA + 0x300
STRBUF = DATA + 0x500
REFERENCE = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"

def validate_candidate(code: bytes) -> None:
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs.detail = True
    instructions = []
    for ins in cs.disasm(code, INJECT):
        if ins.address != INJECT + sum(item.size for item in instructions):
            raise ValueError("candidate executable prefix has a decode gap")
        instructions.append(ins)
        if ins.mnemonic == "pop" and "pc" in ins.op_str:
            break
    if not instructions:
        raise ValueError("candidate has no executable instructions")
    returns = [i for i in instructions if i.mnemonic == "pop" and "pc" in i.op_str]
    if not returns:
        raise ValueError("candidate lacks a stack-pop return")
    for ins in instructions:
        if ins.group(capstone.CS_GRP_CALL):
            if ins.mnemonic != "blx" or not ins.operands or ins.operands[0].type != capstone.arm.ARM_OP_REG:
                raise ValueError(f"unsupported helper call form: {ins.mnemonic} {ins.op_str}")
        elif ins.group(capstone.CS_GRP_JUMP):
            if ins.mnemonic.startswith("bx") and ins.op_str == "lr":
                continue
            if not ins.operands or ins.operands[0].type != capstone.arm.ARM_OP_IMM:
                raise ValueError(f"unsupported branch: {ins.mnemonic} {ins.op_str}")
            target = ins.operands[0].imm
            if not INJECT <= target < INJECT + len(code):
                raise ValueError(f"branch leaves candidate: {ins.mnemonic} {ins.op_str}")
        for op in ins.operands:
            if op.type == capstone.CS_OP_MEM and ins.reg_name(op.mem.base) == "pc":
                if not ins.mnemonic.startswith("ldr"):
                    raise ValueError("unsupported PC-relative memory access")
                target = (ins.address + 8 + op.mem.disp) & ~3
                if not INJECT <= target <= INJECT + len(code) - 4:
                    raise ValueError("literal pool address leaves candidate")

def compile_candidate(out: Path, source: Path | None = None, name="candidate"):
    source = source or ROOT / "experiments/semantic_equivalence/h18_002e0dd0_candidate.cpp"
    obj = out / f"{name}.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K compilation failed")
    symbols = extract_elf_functions_detailed(obj)
    item = symbols.get("h18_002e0dd0_candidate")
    if item is None:
        raise ValueError("candidate symbol missing")
    code, relocs = item
    if relocs:
        raise ValueError(f"unresolved candidate relocations: {relocs}")
    validate_candidate(code)
    return code, {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
                  "candidate_sha256": hashlib.sha256(code).hexdigest(),
                  "candidate_size": len(code)}

class Harness:
    def __init__(self, image: bytes, code: bytes | None, fixture, *, start=FUNC, stops=(RETURN,)):
        regs, data, stack, sp, gate_result, external = fixture
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_ALL)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_write(DATA, data)
        self.uc.mem_write(STACK, stack)
        self.uc.mem_write(GLOBAL_SLOT, struct.pack("<I", GLOBAL_CONTEXT))
        for addr, contents in external:
            self.uc.mem_write(addr, contents)
        if code is not None:
            self.uc.mem_write(INJECT, code)
            self.uc.mem_write(FUNC, arm_branch(FUNC, INJECT))
        self.gate_result, self.start, self.stops = gate_result, start, tuple(stops)
        self.log, self.fault, self.stop_seen = [], None, False
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        for i, value in enumerate(regs):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_INVALID, self._invalid)

    def _invalid(self, uc, access, address, size, value, _):
        self.fault = {"access": int(access), "address": hex(address), "size": size}
        return False

    def _code(self, uc, address, size, _):
        if address in self.stops:
            self.stop_seen = True
            uc.emu_stop()
            return
        if address not in (GATE, COUNT, VALUE, CLEANUP):
            return
        r = lambda n: uc.reg_read(getattr(arm, f"UC_ARM_REG_R{n}")) & 0xFFFFFFFF
        lr = uc.reg_read(arm.UC_ARM_REG_LR) & 0xFFFFFFFF
        thumb = (uc.reg_read(arm.UC_ARM_REG_CPSR) >> 5) & 1
        if address == GATE:
            entry = {"helper":"gate","args":[r(0),r(1),r(2),r(3)],"thumb":thumb,"result":self.gate_result}
            result = self.gate_result
        elif address == COUNT:
            ptr, n = r(0), 0
            while n < 256:
                value = struct.unpack("<H", bytes(uc.mem_read(ptr + 2*n, 2)))[0]
                if value == 0:
                    break
                n += 1
            else:
                self.fault = {"error":"unterminated u16 sequence","address":hex(ptr)}
                uc.emu_stop()
                return
            entry = {"helper":"count","args":[ptr],"thumb":thumb,"result":n,"elements":n+1}
            result = n
        elif address == VALUE:
            entry = {"helper":"value","args":[r(0),r(1),r(2),r(3)],"thumb":thumb,"result":None}
            result = None
        else:
            entry = {"helper":"cleanup","args":[r(0)],"thumb":thumb,"result":None}
            result = None
        self.log.append(entry)
        if result is not None:
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        cpsr = uc.reg_read(arm.UC_ARM_REG_CPSR)
        uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr & ~(1 << 5))
        uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

    def run(self):
        try:
            self.uc.emu_start(self.start, 0, count=3000)
        except unicorn.UcError as error:
            self.fault = {"error":str(error)}
        state = {f"r{i}":self.uc.reg_read(getattr(arm,f"UC_ARM_REG_R{i}")) & 0xFFFFFFFF for i in range(13)}
        state.update({"sp":self.uc.reg_read(arm.UC_ARM_REG_SP)&0xFFFFFFFF,
                      "lr":self.uc.reg_read(arm.UC_ARM_REG_LR)&0xFFFFFFFF,
                      "pc":self.uc.reg_read(arm.UC_ARM_REG_PC)&0xFFFFFFFF,
                      "cpsr":self.uc.reg_read(arm.UC_ARM_REG_CPSR)&0xFFFFFFFF})
        return {"state":state,"log":self.log,"fault":self.fault,"stopped":self.stop_seen,
                "data":bytes(self.uc.mem_read(DATA,DATA_SIZE)),
                "entry_stack":bytes(self.uc.mem_read(self.uc.reg_read(arm.UC_ARM_REG_SP) if False else SP, 0x40))}

def make_fixture(seed, index, args, fifth, values, gate_result, extra_stack=None, external=()):
    rng = random.Random(seed ^ index)
    data = bytearray(rng.randbytes(DATA_SIZE))
    struct.pack_into("<I",data,GLOBAL_CONTEXT-DATA,OBJECT-0x18)
    struct.pack_into("<I",data,GLOBAL_CONTEXT-DATA+0x18,OBJECT)
    if DATA <= args[2] < DATA + DATA_SIZE:
        for i,value in enumerate(values):
            struct.pack_into("<H",data,args[2]-DATA+2*i,value)
    stack = bytearray(STACK_SIZE)
    struct.pack_into("<I",stack,SP-STACK,fifth)
    if extra_stack:
        for off,value in extra_stack.items():
            struct.pack_into("<I",stack,SP-STACK+off,value)
    regs=[rng.getrandbits(32) for _ in range(13)]
    regs[:4]=args
    return regs,bytes(data),bytes(stack),SP,gate_result,tuple(external)

def execute(image, code, fixture, start=FUNC, stops=(RETURN,)):
    return Harness(image,code,fixture,start=start,stops=stops).run()

def compare(old,new,keys=None):
    if old["fault"] or new["fault"]:
        return f"fault old={old['fault']} new={new['fault']}"
    if not old["stopped"] or not new["stopped"]:
        return "expected return/continuation not reached"
    # LR and r1-r3/r12 are caller-saved; the original and compiled helper
    # call sites naturally leave different values there.
    keys=keys or ["r0","r4","r5","r6","r7","r8","r9","r10","r11","sp","pc"]
    if any(old["state"][key]!=new["state"][key] for key in keys):
        return "observable register/ABI state differs"
    if old["log"]!=new["log"]:
        return "helper order/arguments/results differ"
    if old["data"]!=new["data"]:
        return "fixture memory differs"
    return None

def directed_cases(seed,samples):
    vectors=[[],[1,0],[0xffff,0],[0x8000,0x7fff,0],[1,2,3,4,5,6,7,0]]
    gates=[0,1,0x7fffffff,0x80000000,0xffffffff]
    out=[]
    for gate in gates:
        for i,values in enumerate(vectors):
            out.append({"gate":gate,"values":values or [0],"label":f"gate-{gate:08x}-seq-{i}"})
    rng=random.Random(seed)
    for i in range(samples):
        n=rng.randrange(0,24)
        values=[rng.randrange(1,0x10000) for _ in range(n)]+[0]
        out.append({"gate":rng.choice(gates),"values":values,"label":f"random-{i}"})
    return out

def expected_log(args,fifth,values,gate):
    obj=OBJECT
    first={"helper":"gate","args":[obj,args[0],args[1],args[3]],"thumb":0,"result":gate}
    if gate&0x80000000:
        return [first]
    n=values.index(0)
    return [first,{"helper":"count","args":[args[2]],"thumb":1,"result":n,"elements":n+1},
            {"helper":"value","args":[obj,0x6e,args[2],n*2],"thumb":0,"result":None},
            {"helper":"value","args":[obj,0x65,args[3],fifth],"thumb":0,"result":None},
            {"helper":"cleanup","args":[obj],"thumb":0,"result":None}]

def run(image_path,output,seed,samples):
    output.mkdir(parents=True,exist_ok=True)
    image=image_path.read_bytes()
    if hashlib.sha256(image).hexdigest()!=REFERENCE:
        raise ValueError("pinned code image hash mismatch")
    offset=FUNC-TEXT
    if image[offset:offset+len(ENTRY_BYTES)]!=ENTRY_BYTES:
        raise ValueError("original entry bytes/boundary changed")
    code,compile_info=compile_candidate(output)
    outcomes=[]
    for i,case in enumerate(directed_cases(seed,samples)):
        args=(DATA+0x800+((i*0x20)%0x600),0x11000000+i,DATA+0x900,0x22000000+i)
        fifth=(0x1200+i)&0xffffffff
        fx=make_fixture(seed,i,args,fifth,case["values"],case["gate"])
        old=execute(image,None,fx); new=execute(image,code,fx)
        why=compare(old,new)
        want=expected_log(args,fifth,case["values"],case["gate"])
        if old["log"]!=want or new["log"]!=want:
            why=why or "expected helper interaction mismatch"
        result=5 if case["gate"]&0x80000000 else 0
        if old["state"]["r0"]!=result or new["state"]["r0"]!=result:
            why=why or "expected return 0/5 mismatch"
        outcomes.append({"label":case["label"],"gate_result":hex(case["gate"]),
                         "expected_return":result,"passed":why is None,"reason":why,
                         "helper_order":[x["helper"] for x in new["log"]]})
    callers=[]
    # Execute real caller continuations from their direct BL sites, with the
    # call-site register/stack shapes recovered by the contract audit.
    for name,site,stop,gateret,caller_regs,expected in [
        ("ui_func_003bbdb8_ignored_result",0x003bbdfc,0x003bbe18,0,
         (0x44000000,0x55000000,0x0043de3c,0x66000000),0x0043ddf2),
        ("ui_func_003bbfb0_non5_returns_0",0x003bc070,RETURN,0,
         (0x44000000,0x55000000,0x0043de3c,0x66000000),0),
        ("ui_func_003bbfb0_five_returns_11",0x003bc070,RETURN,0x80000000,
         (0x44000000,0x55000000,0x0043de3c,0x66000000),0x11)]:
        values=[65,66,0]
        data_args=caller_regs
        extra={0x14:0x44444444,0x18:0x55555555,0x1c:0x66666666,0x20:0x77777777,0x24:RETURN}
        fx=make_fixture(seed^site,site,data_args,0x1200,values,gateret,extra_stack=extra,
                        external=((0x0043de3c,struct.pack("<HHH",*values)),))
        # For the ignored-result caller, post-call instructions load [r5+8].
        regs,data,stack,sp,gr,ext=fx
        b=bytearray(data)
        struct.pack_into("<I",b,0xA00,0xABCDEF00)
        regs[5]=DATA+0xA00
        regs[6]=0x77000000
        fx=(regs,bytes(b),stack,sp,gr,ext)
        stops=(stop,)
        old=execute(image,None,fx,start=site,stops=stops)
        new=execute(image,code,fx,start=site,stops=stops)
        # AAPCS makes r1-r3 caller-saved across the wrapper and the caller's
        # continuation; compare the returned value and preserved state only.
        why=compare(old,new,["r0","r4","r5","r6","r7","r8","r9","r10","r11","sp","pc"])
        if old["state"]["r0"]!=expected or new["state"]["r0"]!=expected:
            why=why or f"caller continuation r0 expected {expected:#x}"
        callers.append({"caller":name,"call_site":hex(site),"stop":hex(stop),
                        "expected_return":expected,
                        "passed":why is None,"reason":why,
                        "helper_order":[x["helper"] for x in new["log"]]})
    negative_controls=[]
    source_path=ROOT/"experiments/semantic_equivalence/h18_002e0dd0_candidate.cpp"
    source_text=source_path.read_text(encoding="utf-8")
    neg_specs=[
        ("gate_uses_nonzero_instead_of_bit31",
         "if ((status & 0x80000000u) != 0) return 5;",
         "if (status != 0) return 5;", 1, [65,0]),
        ("wrong_first_value_key",
         "apply_value(object, 0x6eu, arg2, count << 1);",
         "apply_value(object, 0x6fu, arg2, count << 1);", 0, [65,0]),
        ("forwards_wrong_fifth_argument",
         "apply_value(object, 0x65u, reinterpret_cast<const u16*>(arg3), arg4);",
         "apply_value(object, 0x65u, reinterpret_cast<const u16*>(arg3), arg3);", 0, [65,0]),
    ]
    for ni,(name,old_text,new_text,gateret,values) in enumerate(neg_specs):
        if source_text.count(old_text)!=1:
            raise ValueError(f"negative control source anchor not unique: {name}")
        mutant_source=output/f"{name}.cpp"
        mutant_source.write_text(source_text.replace(old_text,new_text),encoding="utf-8")
        mutant_code,_=compile_candidate(output,mutant_source,name)
        args=(DATA+0x800,0x12345678,DATA+0x900,0x87654321)
        fx=make_fixture(seed,0xABC000+ni,args,0xDEADBEEF,values,gateret)
        old=execute(image,None,fx)
        bad=execute(image,mutant_code,fx)
        reason=compare(old,bad)
        negative_controls.append({"name":name,"detected":reason is not None,"reason":reason})
    negative_ok=all(x["detected"] for x in negative_controls)
    report={"schema":1,"address":hex(FUNC),"seed":seed,"samples":samples,
            "passed":all(x["passed"] for x in outcomes+callers) and negative_ok,
            "reference_sha256":REFERENCE,**compile_info,
            "entry_original_span":0x8c,"entry_bytes_checked":len(ENTRY_BYTES),
            "direct":{"passed":all(x["passed"] for x in outcomes),"cases":len(outcomes),"results":outcomes},
            "callers":callers,"negative_controls":negative_controls,
            "limitations":[
                "0x00263534 returns configured values; 0x002b5c2c scans the test u16 sequence; 0x00248e58 and 0x002390dc are no-op trace stubs. Their real semantics and side effects remain unresolved.",
                "Tests use fixed global/object fixtures, aligned readable RAM, and bounded zero-terminated u16 arrays; object lifetime, aliasing, MMIO, invalid pointers, and concurrent mutation are outside scope.",
                "Caller compositions start at real BL sites with audited register/stack shapes and execute through the caller return; they do not execute each caller's prior setup or outer application state.",
                "Only callable entry 0x002e0dd0 is covered. Adjacent VFP-heavy body 0x002e0e5c remains unresolved and is not modified.",
                "No production conversion, full build, emulator, or whole-game equivalence claim."
            ],
            "first_failure":next((x for x in outcomes+callers if not x["passed"]),None)}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image",type=Path,default=ROOT/"extracted/exefs/code.bin")
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--samples",type=int,default=64)
    a=p.parse_args()
    result=run(a.image,a.output,a.seed,a.samples)
    print(json.dumps({"passed":result["passed"],"report":str(a.output/"report.json")}))
    return 0 if result["passed"] else 1

if __name__=="__main__": raise SystemExit(main())
