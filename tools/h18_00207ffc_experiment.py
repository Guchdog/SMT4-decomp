#!/usr/bin/env python3
"""Bounded differential for the enclosing state handler at 0x00207FFC."""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import arm_branch

FUNC = 0x00207FFC
CATALOG_BLOCK = 0x002080E0
ENTRY_PROLOGUE = bytes.fromhex("70402de910439fe56360a0e3028b2ded98d04de2001094e5c08a9fedf800d1e10a0050e3")
REFERENCE = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
TEXT, TEXT_SIZE = 0x00100000, 0x00400000
INJECT, INJECT_SIZE = 0x01000000, 0x00010000
DATA, DATA_SIZE = 0x02000000, 0x00010000
STACK, STACK_SIZE = 0x08000000, 0x00010000
ENTRY_SP, RETURN = STACK + 0x8000, 0x0100F000
GLOBAL_CONTEXT = 0x004474D8
GLOBAL_SETTING = 0x0049FC7C
CONTEXT = DATA + 0x100
ALLOC_RESOURCE, FILE_RESOURCE = DATA + 0x3000, DATA + 0x4000
RESOURCE_TARGET_A, RESOURCE_TARGET_B = DATA + 0x5000, DATA + 0x6000
CONTEXT_ALT = DATA + 0x200
SKY, CREATE, LOAD, POLL = 0x0020E5A4, 0x0025BE50, 0x0029A2D0, 0x002AE16C
SETUP, SET_A, SET_B, SET_VECTOR, FORMAT = 0x002A06C8, 0x002A5A54, 0x00287300, 0x0028C8A8, 0x002BE7FC
HELPERS = {SKY:"sky_id", CREATE:"create", LOAD:"load", POLL:"poll", SETUP:"setup",
           SET_A:"set_a", SET_B:"set_b", SET_VECTOR:"set_vector", FORMAT:"format"}
SOURCE = ROOT / "experiments/semantic_equivalence/h18_00207ffc_candidate.cpp"

def compile_candidate(out: Path, source=SOURCE, name="candidate"):
    obj = out / f"{name}.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "ARMv6K compilation failed")
    item = extract_elf_functions_detailed(obj).get("h18_00207ffc_candidate")
    if item is None:
        raise ValueError("candidate symbol missing")
    code, relocs = item
    staged = bytearray(code)
    resolved = []
    for reloc in relocs:
        if reloc.relocation_type != 2 or reloc.offset % 4 or reloc.offset + 4 > len(staged):
            raise ValueError(f"unsupported candidate relocation: {reloc}")
        addend = struct.unpack_from("<I", staged, reloc.offset)[0]
        if reloc.symbol_name not in ("", ".text") or addend >= len(staged):
            raise ValueError(f"candidate relocation is not a local text reference: {reloc}, addend={addend:#x}")
        target = INJECT + addend
        struct.pack_into("<I", staged, reloc.offset, target)
        resolved.append({"offset":reloc.offset,"addend":hex(addend),"target":hex(target)})
    code = bytes(staged)
    return code, {"source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                  "object_sha256": hashlib.sha256(obj.read_bytes()).hexdigest(),
                  "candidate_sha256": hashlib.sha256(code).hexdigest(), "candidate_size": len(code),
                  "local_abs32_relocations_resolved": resolved}

def fixture(seed, index, *, state, map_id=0x13, variant=2, sky_arg=7, sky_result=4,
            setting=0, embedded0=0, embedded0_data=DATA+0x7000,
            embedded10=0, embedded10_data=DATA+0x7100, poll_results=(1,), mutations=()):
    rng = random.Random(seed ^ index)
    data = bytearray(rng.randbytes(DATA_SIZE))
    struct.pack_into("<H", data, CONTEXT-DATA+4, map_id & 0xffff)
    struct.pack_into("<H", data, CONTEXT-DATA+6, sky_arg & 0xffff)
    struct.pack_into("<H", data, CONTEXT-DATA+8, state & 0xffff)
    struct.pack_into("<I", data, CONTEXT-DATA+0x0c, FILE_RESOURCE)
    struct.pack_into("<I", data, CONTEXT-DATA+0x10, FILE_RESOURCE)
    struct.pack_into("<I", data, CONTEXT-DATA+0x20, embedded10)
    struct.pack_into("<I", data, CONTEXT-DATA+0x24, embedded10_data)
    struct.pack_into("<I", data, CONTEXT-DATA+0x28, embedded0)
    struct.pack_into("<I", data, CONTEXT-DATA+0x2c, embedded0_data)
    data[CONTEXT_ALT-DATA:CONTEXT_ALT-DATA+0x40] = data[CONTEXT-DATA:CONTEXT-DATA+0x40]
    struct.pack_into("<I", data, CONTEXT_ALT-DATA+0x10, ALLOC_RESOURCE)
    struct.pack_into("<I", data, CONTEXT_ALT-DATA+0x0c, ALLOC_RESOURCE)
    struct.pack_into("<I", data, ALLOC_RESOURCE-DATA+8, RESOURCE_TARGET_A)
    struct.pack_into("<I", data, FILE_RESOURCE-DATA+8, RESOURCE_TARGET_B)
    stack = bytearray(STACK_SIZE)
    regs = [rng.getrandbits(32) for _ in range(13)]
    return {"data":bytes(data), "stack":bytes(stack), "regs":regs, "setting":setting, "sky_result":sky_result,
            "poll_results":tuple(poll_results), "mutations":tuple(mutations), "index":index}

class Machine:
    def __init__(self, image, code, fx):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_write(DATA, fx["data"]); self.uc.mem_write(STACK, fx["stack"])
        self.uc.mem_write(GLOBAL_CONTEXT, struct.pack("<I", CONTEXT))
        self.uc.mem_write(GLOBAL_SETTING, struct.pack("<I", fx["setting"]))
        if code is not None:
            self.uc.mem_write(INJECT, code)
            self.uc.mem_write(FUNC, arm_branch(FUNC, INJECT))
        self.fx = fx
        self.log, self.fault, self.stopped = [], None, False
        self.helper_counts = {}
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for i, value in enumerate(fx["regs"]):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        for i in range(8):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i+8}"), 0x1122334455667700+i)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_INVALID, self._invalid)

    def _invalid(self, uc, access, address, size, value, _):
        self.fault = {"access":int(access),"address":hex(address),"size":size}
        return False

    def _r(self, n): return self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{n}")) & 0xffffffff
    def _read(self, address, length): return bytes(self.uc.mem_read(address, length))
    def _u32(self, address): return struct.unpack("<I", self._read(address,4))[0]
    def _f32(self, address): return struct.unpack("<f", self._read(address,4))[0]

    def _apply_mutations(self, helper, occurrence):
        applied=[]
        for mutation in self.fx["mutations"]:
            if mutation["after"] != helper or mutation.get("occurrence",1) != occurrence:
                continue
            kind=mutation["kind"]
            if kind == "context_field_u32":
                address=self._u32(GLOBAL_CONTEXT)+mutation["offset"]
                value=mutation["value"]
                self.uc.mem_write(address,struct.pack("<I",value))
            elif kind == "context_field_u16":
                address=self._u32(GLOBAL_CONTEXT)+mutation["offset"]
                value=mutation["value"]
                self.uc.mem_write(address,struct.pack("<H",value&0xffff))
            elif kind == "global_context":
                value=mutation["value"]
                self.uc.mem_write(GLOBAL_CONTEXT,struct.pack("<I",value))
            elif kind == "resource_word_u32":
                address=mutation["resource"]+mutation["offset"]
                value=mutation["value"]
                self.uc.mem_write(address,struct.pack("<I",value))
            else:
                raise ValueError(f"unknown mutation kind: {kind}")
            applied.append({"stimulus":"post_call_fixture_mutation",
                            "after_helper":helper,"occurrence":occurrence,
                            **mutation})
        return applied

    def _code(self, uc, address, size, _):
        if address == RETURN:
            self.stopped = True; uc.emu_stop(); return
        if address not in HELPERS: return
        name = HELPERS[address]
        occurrence=self.helper_counts.get(name,0)+1
        self.helper_counts[name]=occurrence
        args = [self._r(i) for i in range(4)]
        lr = self._r(14)
        index = len([x for x in self.log if x["helper"] == "poll"])
        result = None
        if name == "sky_id":
            entry = {"helper":name,"args":[args[0]],"result":self.fx["sky_result"]}
            result = self.fx["sky_result"]
        elif name == "create":
            entry = {"helper":name,"args":args[:3],"result":ALLOC_RESOURCE}
            result = ALLOC_RESOURCE
        elif name == "load":
            path = self._read(args[0],128).split(b"\0",1)[0].decode("ascii")
            entry = {"helper":name,"path":path,"size":args[1],"result":FILE_RESOURCE}
            result = FILE_RESOURCE
        elif name == "poll":
            poll_results = self.fx["poll_results"]
            result = poll_results[min(index,len(poll_results)-1)] if poll_results else 0
            entry = {"helper":name,"args":[args[0]],"result":result}
        elif name == "setup":
            entry = {"helper":name,"args":args[:2]}
        elif name in ("set_a","set_b"):
            entry = {"helper":name,"args":args[:2],"s0_bits":uc.reg_read(arm.UC_ARM_REG_S0)&0xffffffff}
        elif name == "set_vector":
            entry = {"helper":name,"args":args[:2],"values":list(struct.unpack("<fff",self._read(args[2],12)))}
        elif name == "format":
            fmt = self._read(args[1],64).split(b"\0",1)[0].decode("ascii")
            if fmt == "map/sky/sky_%02d.bam":
                values = [args[2]]
                path = fmt % tuple(values)
            elif fmt == "map/m%03d/m%03d_%02d.bam":
                values = [args[2],args[3],struct.unpack("<i",self._read(uc.reg_read(arm.UC_ARM_REG_SP),4))[0]]
                path = fmt % tuple(values)
            else:
                self.fault={"error":"unknown format string","format":fmt}; uc.emu_stop(); return
            encoded=path.encode("ascii")+b"\0"
            uc.mem_write(args[0],encoded)
            entry={"helper":name,"format":fmt,"values":values,"path":path}
            result=len(encoded)-1
        else:
            self.fault={"error":"unexpected helper","address":hex(address)}; uc.emu_stop(); return
        mutations=self._apply_mutations(name,occurrence)
        if mutations: entry["mutations"]=mutations
        self.log.append(entry)
        if result is not None: uc.reg_write(arm.UC_ARM_REG_R0,result & 0xffffffff)
        cpsr=uc.reg_read(arm.UC_ARM_REG_CPSR)
        uc.reg_write(arm.UC_ARM_REG_CPSR,cpsr & ~(1<<5))
        uc.reg_write(arm.UC_ARM_REG_PC,lr & ~1)

    def run(self):
        try:
            self.uc.emu_start(FUNC,0,count=20000)
        except unicorn.UcError as exc:
            self.fault={"error":str(exc)}
        regs={f"r{i}":self._r(i) for i in range(13)}
        regs.update({"sp":self.uc.reg_read(arm.UC_ARM_REG_SP)&0xffffffff,
                     "pc":self.uc.reg_read(arm.UC_ARM_REG_PC)&0xffffffff,
                     "d8_d15":[self.uc.reg_read(getattr(arm,f"UC_ARM_REG_D{i}")) for i in range(8,16)]})
        ctx=self._u32(GLOBAL_CONTEXT)
        return {"regs":regs,"log":self.log,"fault":self.fault,"stopped":self.stopped,
                "context":self._read(ctx,0x40),"global_context":ctx,
                "setting":self._u32(GLOBAL_SETTING),"data":self._read(DATA,DATA_SIZE)}

def execute(image,code,fx): return Machine(image,code,fx).run()

def compare(old,new):
    if old["fault"] or new["fault"]: return f"fault old={old['fault']} new={new['fault']}"
    if not old["stopped"] or not new["stopped"]: return "expected return address not reached"
    for key in ("r0","r4","r5","r6","r7","r8","r9","r10","r11","sp","pc","d8_d15"):
        if old["regs"][key] != new["regs"][key]: return f"register/ABI difference at {key}"
    if old["context"] != new["context"]: return "context bytes differ"
    if old["global_context"] != new["global_context"] or old["setting"] != new["setting"]: return "global state differs"
    if old["log"] != new["log"]: return "helper trace or formatted path differs"
    if old["data"] != new["data"]: return "fixture data page differs"
    return None

def directed_cases(seed):
    rows=[]
    add=lambda label,**kw: rows.append((label,kw))
    add("state0-clear",state=0,setting=1)
    add("state0-embedded-extra",state=0,embedded0=DATA+0x7200,map_id=0x13)
    add("state0-embedded-no-extra",state=0,embedded0=DATA+0x7200,map_id=0x12)
    add("state0-create-changes-context-pointer",state=0,embedded0=DATA+0x7200,
        mutations=({"after":"create","kind":"global_context","value":CONTEXT_ALT},))
    add("state0-sky-helper-changes-context-pointer",state=0,sky_result=4,
        mutations=({"after":"sky_id","kind":"global_context","value":CONTEXT_ALT},))
    add("state0-sky-nonpositive",state=0,sky_result=0)
    add("state0-sky-negative",state=0,sky_result=-2)
    add("state0-sky-pending",state=0,sky_result=4,poll_results=(0,))
    add("state0-sky-ready-extra",state=0,sky_result=4,poll_results=(1,),map_id=0x13)
    add("state0-sky-ready",state=0,sky_result=4,poll_results=(1,),map_id=0x12)
    add("state1-pending",state=1,poll_results=(0,))
    add("state1-ready-extra",state=1,poll_results=(1,),map_id=0x13)
    add("state1-ready",state=1,poll_results=(1,),map_id=0x12)
    add("state1-setup-mutates-context-resource",state=1,poll_results=(1,),map_id=0x12,
        mutations=({"after":"setup","kind":"context_field_u32","offset":0x10,"value":ALLOC_RESOURCE},))
    add("state1-set-a-mutates-context-resource",state=1,poll_results=(1,),map_id=0x12,
        mutations=({"after":"set_a","kind":"context_field_u32","offset":0x10,"value":ALLOC_RESOURCE},))
    add("state1-setup-mutates-resource-target",state=1,poll_results=(1,),map_id=0x12,
        mutations=({"after":"setup","kind":"resource_word_u32","resource":FILE_RESOURCE,"offset":8,"value":RESOURCE_TARGET_A},))
    add("state1-context-pointer-changes-after-setup",state=1,poll_results=(1,),map_id=0x12,
        mutations=({"after":"setup","kind":"global_context","value":CONTEXT_ALT},))
    add("state1-poll-changes-context-resource",state=1,poll_results=(1,),map_id=0x12,
        mutations=({"after":"poll","kind":"context_field_u32","offset":0x10,"value":ALLOC_RESOURCE},))
    add("state1-set-b-changes-extra-gate",state=1,poll_results=(1,),map_id=0x12,
        mutations=({"after":"set_b","kind":"context_field_u16","offset":4,"value":0x13},))
    add("state10-embedded",state=10,embedded10=DATA+0x7300)
    add("state10-create-changes-context-pointer",state=10,embedded10=DATA+0x7300,
        mutations=({"after":"create","kind":"global_context","value":CONTEXT_ALT},))
    for idv in (0x29,0x2a,0x2b): add(f"map-special-{idv:x}",state=10,map_id=idv,variant=0xffff)
    for idv in (-32768,-1,0,1,32767): add(f"map-boundary-{idv}",state=10,map_id=idv,variant=0xffff if idv<0 else 0x7fff)
    add("state10-load-changes-context-pointer",state=10,map_id=0x13,
        mutations=({"after":"load","kind":"global_context","value":CONTEXT_ALT},))
    add("state11-pending",state=11,poll_results=(0,))
    add("state11-ready",state=11,poll_results=(1,))
    add("state11-set-a-mutates-resource-target",state=11,poll_results=(1,),
        mutations=({"after":"set_a","kind":"resource_word_u32","resource":FILE_RESOURCE,"offset":8,"value":RESOURCE_TARGET_A},))
    add("state99-return-one",state=99)
    add("state-negative",state=0xffff)
    add("state-high",state=12)
    rng=random.Random(seed)
    for i in range(8):
        add(f"random-{i}",state=rng.choice((0,1,10,11,99,12,0xffff)),
            map_id=rng.choice((0x13,0x29,0x2b,0xffff,0x8000)),
            sky_result=rng.choice((-1,0,1,8)), setting=rng.choice((0,1)),
            embedded0=rng.choice((0,DATA+0x7400)),embedded10=rng.choice((0,DATA+0x7500)),
            poll_results=(rng.choice((0,1)),))
    return rows

def run(image_path:Path,output:Path,seed=7):
    output.mkdir(parents=True,exist_ok=True)
    image=image_path.read_bytes()
    if hashlib.sha256(image).hexdigest()!=REFERENCE: raise ValueError("pinned image hash mismatch")
    if image[FUNC-TEXT:FUNC-TEXT+len(ENTRY_PROLOGUE)]!=ENTRY_PROLOGUE: raise ValueError("handler entry bytes changed")
    code,compile_info=compile_candidate(output)
    outcomes=[]
    for i,(label,kwargs) in enumerate(directed_cases(seed)):
        fx=fixture(seed,i,**kwargs)
        old=execute(image,None,fx); new=execute(image,code,fx); reason=compare(old,new)
        outcomes.append({"label":label,"passed":reason is None,"reason":reason,
                         "return":hex(old["regs"]["r0"]),"helpers":[x["helper"] for x in old["log"]],
                         "original_trace":old["log"] if kwargs.get("mutations") else None,
                         "candidate_trace":new["log"] if kwargs.get("mutations") else None})
    source=SOURCE.read_text(encoding="utf-8")
    neg_specs=[
        ("state99_wrong_return","if (state == 99) return 1;","if (state == 99) return 0;",{"state":99}),
        ("sky_zero_wrong_branch","if (id <= 0)","if (id < 0)",{"state":0,"sky_result":0}),
        ("special_map_wrong_case","map_id == 0x2B","map_id == 0x2C",{"state":10,"map_id":0x2b}),
    ]
    negatives=[]
    for j,(name,before,after,kwargs) in enumerate(neg_specs):
        if source.count(before)!=1: raise ValueError(f"nonunique negative-control anchor: {name}")
        mutant=output/f"{name}.cpp"; mutant.write_text(source.replace(before,after),encoding="utf-8")
        bad,_=compile_candidate(output,mutant,name)
        fx=fixture(seed^0xBAD,j,**kwargs)
        old=execute(image,None,fx); changed=execute(image,bad,fx); reason=compare(old,changed)
        negatives.append({"name":name,"detected":reason is not None,"difference":reason})
    report={"schema":1,"address":hex(FUNC),"catalog_block":hex(CATALOG_BLOCK),"seed":seed,
            "reference_sha256":REFERENCE,**compile_info,
            "passed":all(x["passed"] for x in outcomes) and all(x["detected"] for x in negatives),
            "direct":{"passed":all(x["passed"] for x in outcomes),"cases":len(outcomes),"results":outcomes},
            "negative_controls":negatives,
            "helper_models":{
              "default_side_effect_policy":{
                "context_or_resource_objects":"no_modelled_writes_by_default",
                "formatter_output_buffer":"the format helper writes the two recognized NUL-terminated paths",
                "interpretation":"Configured returns and call logging are the default helper model. This policy does not describe real helper behavior."
              },
              "post_call_fixture_mutation_policy":{
                "mode":"explicit_test_stimulus_applied_after_the_configured_helper_returns",
                "attributed_to_helper":False,
                "mutation_kinds":["context_field_u16","context_field_u32","global_context","resource_word_u32"]
              },
              "helpers":{
                "sky_id":"returns the configured signed result; no context/resource writes by default",
                "create":"returns the fixed synthetic allocation handle; no context/resource writes by default",
                "load":"returns the fixed synthetic file handle; no context/resource writes by default",
                "poll":"returns the configured result sequence; no context/resource writes by default",
                "setup":"records resource and mode; no context/resource writes by default",
                "set_a/set_b/set_vector":"records arguments and float values; no context/resource writes by default",
                "format":"formats the two observed path formats and writes that path to the destination buffer"
              },
              "configured_stimuli":[{"case":label,"events":[dict(mutation) for mutation in kwargs.get("mutations",())]}
                for label,kwargs in directed_cases(seed) if kwargs.get("mutations")]
            },
            "caller":{"status":"not_run","reason":"No real caller/dispatcher for 0x00207FFC is identified."},
            "runtime":"not_run",
            "limitations":["Helper models are synthetic and intentionally do not model resource ownership, readiness side effects, object mutation, or actual formatter behavior beyond the two observed formats.",
              "Valid aligned pointers, controlled context bytes, and deterministic helper results only; invalid pointers, aliasing, races and runtime object lifetime are outside scope.",
              "No actual caller composition, production integration, emulator run, or whole-game equivalence claim."]}
    (output/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--image",type=Path,default=ROOT/"extracted/exefs/code.bin")
    p.add_argument("--output",type=Path,required=True); p.add_argument("--seed",type=int,default=7)
    a=p.parse_args(); report=run(a.image,a.output,a.seed)
    print(json.dumps({"passed":report["passed"],"cases":report["direct"]["cases"],"report":str(a.output/"report.json")}))
    return 0 if report["passed"] else 1
if __name__=="__main__": raise SystemExit(main())
