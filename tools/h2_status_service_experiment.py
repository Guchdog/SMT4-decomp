#!/usr/bin/env python3
"""Final-VMA differential for 0x002A8A8C and typed-selector composition."""
from __future__ import annotations
import argparse, hashlib, json, random, struct, sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
STATUS_SOURCE = ROOT / "src/engine/leaf_batch23_b.cpp"
SELECTOR_SOURCE = ROOT / "src/engine/leaf_batch44_c.cpp"
ENTRY, SLOT = 0x002A8A8C, 36
SELECTOR, SELECTOR_SLOT = 0x002B85BC, 472
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
DATA_BASE, DATA_SIZE = 0x00600000, 0x00200000
STACK, STACK_SIZE, SP, STOP = 0x08000000, 0x10000, 0x08008000, 0x08009000
GLOBAL = 0x0043DCB0
MANAGER_ROOT = 0x0043DA28
MANAGER = DATA_BASE + 0x10000
ALT_MANAGER = DATA_BASE + 0x20000
OBJECT = DATA_BASE + 0x30000
OLD_PROFILE, NEW_PROFILE = DATA_BASE + 0x90000, DATA_BASE + 0x90100
INVALID = DATA_BASE + DATA_SIZE
U32 = 0xFFFFFFFF
SYMBOLS = {
    "camp_func_002aea28": 0x002AEA28,
    "ui_func_002a8a8c": ENTRY,
    "camp_func_002bf030": 0x002BF030,
    "camp_func_002bdac0": 0x002BDAC0,
    "camp_func_002aa268": 0x002AA268,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_symbol(source: Path, symbol: str, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / (source.stem + ".o")
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or f"ARMv6K compile failed: {source}")
    body, relocs = extract_elf_functions_detailed(obj)[symbol]
    return body, relocs, list(result.args), obj


def stage_slot(image: bytes, entry: int, slot: int, body: bytes):
    if len(body) > slot or len(body) % 4:
        raise ValueError(f"body does not fit slot {entry:#x}: {len(body)}/{slot}")
    offset = entry - CODE_BASE
    fixed = body + image[offset + len(body):offset + slot]
    staged = bytearray(image)
    staged[offset:offset + slot] = fixed
    staged = bytes(staged)
    patch = encode_ips([(offset, fixed)], len(image))
    if apply_ips(image, patch) != staged:
        raise AssertionError(f"IPS replay failed at {entry:#x}")
    return staged, patch, fixed


def relocate_selector(body: bytes, relocs):
    relocated = bytearray(body)
    targets = []
    for reloc in relocs:
        if reloc.relocation_type != 28:
            raise ValueError(f"unsupported selector relocation {reloc}")
        target = SYMBOLS.get(reloc.symbol_name)
        if target is None or target & 1:
            raise ValueError(f"unsupported or Thumb target: {reloc.symbol_name} -> {target}")
        place = SELECTOR + reloc.offset
        displacement = target - (place + 8)
        if displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
            raise ValueError(f"ARM call out of range: {reloc.symbol_name}")
        word = struct.unpack_from("<I", relocated, reloc.offset)[0]
        if (word & 0x0E000000) != 0x0A000000:
            raise ValueError(f"relocation site is not ARM B/BL: {word:#x}")
        word = (word & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF)
        struct.pack_into("<I", relocated, reloc.offset, word)
        targets.append({"offset": reloc.offset, "symbol": reloc.symbol_name,
                        "target": hex(target), "target_bit0_clear": True,
                        "relocation_type": reloc.relocation_type})
    return bytes(relocated), targets


class Machine:
    def __init__(self, image: bytes, seed: int = 8102):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM,
                             unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
        self.uc.mem_map(CODE_BASE, CODE_SIZE)
        self.uc.mem_write(CODE_BASE, image)
        self.uc.mem_map(DATA_BASE, DATA_SIZE)
        self.uc.mem_map(STACK, STACK_SIZE)
        rng = random.Random(seed)
        self.uc.mem_write(DATA_BASE, bytes(rng.randrange(256) for _ in range(DATA_SIZE)))
        self.events, self.writes = [], []
        self.fault_detail = None
        self.stop = STOP
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_INVALID, self._on_invalid)

    def _read_counter(self):
        try:
            p = struct.unpack("<I", self.uc.mem_read(GLOBAL + 4, 4))[0]
            return p, p + 0x64C & U32, struct.unpack("<h", self.uc.mem_read((p + 0x64C) & U32, 2))[0]
        except unicorn.UcError:
            return None, None, None

    def _on_code(self, uc, address, _size, _data):
        if address == self.stop:
            uc.emu_stop()
            return
        if address == ENTRY:
            self.events.append({"address": hex(address), "name": "ui_func_002a8a8c",
                                "r0": uc.reg_read(arm.UC_ARM_REG_R0),
                                "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0,
                                "counter_before": self._read_counter()[2]})
            return
        if address == 0x002AEA28:
            arg = uc.reg_read(arm.UC_ARM_REG_R0)
            result = OLD_PROFILE if arg == 3 else NEW_PROFILE
            self.events.append({"address": hex(address), "name": "camp_func_002aea28",
                                "args": [arg],
                                "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
            uc.reg_write(arm.UC_ARM_REG_R0, result)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
            return
        if address == 0x002BF030:
            event_args = [uc.reg_read(arm.UC_ARM_REG_R0), uc.reg_read(arm.UC_ARM_REG_R1)]
            self.events.append({"address": hex(address), "name": "camp_func_002bf030",
                                "args": event_args,
                                "sp_aligned": (uc.reg_read(arm.UC_ARM_REG_SP) & 7) == 0})
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def _on_write(self, _uc, _access, address, size, value, _data):
        if not STACK <= address < STACK + STACK_SIZE:
            self.writes.append([address, size, value & U32])

    def _on_invalid(self, _uc, access, address, size, _value, _data):
        self.fault_detail = {"access": int(access), "address": int(address), "size": int(size)}
        return False

    def run(self, entry: int, call_regs: tuple[int, int, int], setup=None,
            stop=STOP, readonly_page: int | None = None):
        if setup:
            setup(self.uc)
        if readonly_page is not None:
            self.uc.mem_protect(readonly_page, 0x1000, unicorn.UC_PROT_READ)
        self.events.clear(); self.writes.clear(); self.fault_detail = None; self.stop = stop
        initial = [(0xA2000000 + i * 0x01010101) & U32 for i in range(13)]
        for i, value in enumerate(initial):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value)
        for i, value in enumerate(call_regs):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), value & U32)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, stop)
        fault = None
        try:
            self.uc.emu_start(entry, 0, count=100000)
        except unicorn.UcError as error:
            fault = str(error)
        regs = [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(13)]
        return {"fault": fault, "fault_detail": self.fault_detail,
                "registers": regs, "r0": regs[0], "r1": regs[1], "r2": regs[2],
                "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                "callee_saved": regs[4:12] == initial[4:12],
                "data": bytes(self.uc.mem_read(DATA_BASE, DATA_SIZE)),
                "global_words": bytes(self.uc.mem_read(GLOBAL - 4, 16)),
                "manager_root": bytes(self.uc.mem_read(MANAGER_ROOT, 8)),
                "events": self.events.copy(), "writes": self.writes.copy()}


def direct_setup(pointer: int, counter_value: int, incoming_r0: int,
                 alternative_pointer: int = ALT_MANAGER, readonly=False):
    def setup(uc):
        uc.mem_write(GLOBAL + 4, struct.pack("<I", pointer & U32))
        uc.mem_write(GLOBAL + 8, struct.pack("<I", alternative_pointer & U32))
        counter = (pointer + 0x64C) & U32
        if DATA_BASE <= counter and counter + 2 <= DATA_BASE + DATA_SIZE:
            uc.mem_write(counter, struct.pack("<H", counter_value & 0xFFFF))
    return setup


def compare_direct(original: bytes, staged: bytes, label: str, pointer: int,
                   counter: int, r0: int, readonly_page=None):
    setup = direct_setup(pointer, counter, r0)
    call_regs = (r0, 0xAABBCCDD, 0x12345678)
    ref = Machine(original).run(ENTRY, call_regs, setup, readonly_page=readonly_page)
    got = Machine(staged).run(ENTRY, call_regs, setup, readonly_page=readonly_page)
    keys = ("fault", "fault_detail", "r0", "r1", "r2", "sp", "callee_saved",
            "data", "global_words", "writes")
    equal = all(ref[k] == got[k] for k in keys)
    return {"label": label, "equal": equal, "fault": got["fault"],
            "fault_detail": got["fault_detail"], "r0": hex(got["r0"]),
            "r1": got["r1"], "writes": got["writes"]}, ref, got


def mutate_word(body: bytes, offset: int, expected: int, replacement: int):
    changed = bytearray(body)
    actual = struct.unpack_from("<I", changed, offset)[0]
    if actual != expected:
        raise ValueError(f"mutation instruction mismatch at {offset:#x}: {actual:#x}")
    struct.pack_into("<I", changed, offset, replacement)
    return bytes(changed)


def caller_setup(counter_value: int):
    statuses = [0, 1, 7, 8, 9, 2]
    def setup(uc):
        uc.mem_write(MANAGER_ROOT + 4, struct.pack("<I", OBJECT))
        uc.mem_write(GLOBAL + 4, struct.pack("<I", MANAGER))
        uc.mem_write(GLOBAL + 8, struct.pack("<I", ALT_MANAGER))
        uc.mem_write(OBJECT, bytes(0x800))
        uc.mem_write(OBJECT + 0x4C9, b"\x03")
        for i, value in enumerate(statuses):
            uc.mem_write(OBJECT + 0x494 + i * 4, bytes([value]))
        uc.mem_write(OLD_PROFILE, bytes(0x40))
        uc.mem_write(NEW_PROFILE, bytes(0x40))
        uc.mem_write(OLD_PROFILE + 0x0C, b"\x01")
        uc.mem_write(NEW_PROFILE + 0x0C, b"\0")
        uc.mem_write((MANAGER + 0x64C) & U32, struct.pack("<H", counter_value & 0xFFFF))
    return setup, statuses


def normalized_events(events):
    result=[]
    for e in events:
        if e["address"] == hex(ENTRY):
            result.append((e["address"], e["sp_aligned"]))
        else:
            result.append((e["address"], tuple(e.get("args", ())), e["sp_aligned"]))
    return result


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    original=IMAGE.read_bytes()
    if sha(original)!=IMAGE_SHA: raise SystemExit("pinned image SHA mismatch")
    body,relocs,compiler_args,obj=compile_symbol(STATUS_SOURCE,"ui_func_002a8a8c",args.out/"compile-status")
    if relocs: raise ValueError(f"status service has unexpected relocations: {relocs}")
    staged_status,ips,status_fixed=stage_slot(original,ENTRY,SLOT,body)

    # Compile the already-typed selector independently, then resolve its ARM calls
    # to their pinned even ARM entries so this composition executes the typed body.
    selector_body,selector_relocs,selector_args,selector_obj=compile_symbol(
        SELECTOR_SOURCE,"ui_func_002b85bc",args.out/"compile-selector")
    if len(selector_body)>SELECTOR_SLOT: raise ValueError("typed selector exceeds its slot")
    rebased_selector,targets=relocate_selector(selector_body,selector_relocs)
    composed=bytearray(staged_status)
    selector_offset=SELECTOR-CODE_BASE
    selector_fixed=rebased_selector+original[selector_offset+len(rebased_selector):selector_offset+SELECTOR_SLOT]
    composed[selector_offset:selector_offset+SELECTOR_SLOT]=selector_fixed
    composed=bytes(composed)
    (args.out/"staged-status-image.bin").write_bytes(staged_status)
    (args.out/"staged-status.ips").write_bytes(ips)
    (args.out/"typed-selector-composition-image.bin").write_bytes(composed)
    composition_ips=encode_ips([(ENTRY-CODE_BASE,status_fixed),(selector_offset,selector_fixed)],len(original))
    if apply_ips(original,composition_ips)!=composed: raise AssertionError("composition IPS replay mismatch")
    (args.out/"typed-selector-composition.ips").write_bytes(composition_ips)

    direct_specs=[
        ("halfword_neg32768",MANAGER,0x8000,0x11111111,None),
        ("halfword_neg1",MANAGER,0xFFFF,0x22222222,None),
        ("halfword_zero",MANAGER,0,0x33333333,None),
        ("halfword_one",MANAGER,1,0x44444444,None),
        ("halfword_two",MANAGER,2,0x55555555,None),
        ("halfword_max_positive",MANAGER,0x7FFF,0x66666666,None),
        ("incoming_r0_ignored",MANAGER,2,0,None),
        ("byte_neighbors_preserved",MANAGER,0x0100,0x77777777,None),
        ("null_manager_pointer_fault",0,1,0x88888888,None),
        ("unmapped_counter_read_fault",INVALID-0x64C,1,0x99999999,None),
        ("positive_counter_store_fault",DATA_BASE+0x11000,1,0xAAAAAAAA,DATA_BASE+0x11000),
    ]
    direct=[]; mismatches=[]
    for label,pointer,value,r0,ro_page in direct_specs:
        result,ref,got=compare_direct(original,staged_status,label,pointer,value,r0,ro_page)
        direct.append(result)
        if not result["equal"]: mismatches.append({"case":label,"ref_fault":ref["fault"],"got_fault":got["fault"]})

    caller_results=[]
    for starting_counter in (3,1):
        setup,statuses=caller_setup(starting_counter)
        ref=Machine(original,seed=991).run(SELECTOR,(0xDC,0,0),setup,stop=STOP)
        got=Machine(composed,seed=991).run(SELECTOR,(0xDC,0,0),setup,stop=STOP)
        ref_key=("fault","fault_detail","r0","sp","callee_saved","data","manager_root","writes")
        event_eq=normalized_events(ref["events"])==normalized_events(got["events"])
        equal=all(ref[k]==got[k] for k in ref_key) and event_eq
        counter_addr=MANAGER+0x64C
        after_counter=struct.unpack("<h",got["data"][counter_addr-DATA_BASE:counter_addr-DATA_BASE+2])[0]
        status_after=[got["data"][OBJECT+0x494+i*4-DATA_BASE] for i in range(6)]
        service_events=[e for e in got["events"] if e["address"]==hex(ENTRY)]
        call={"label":f"typed_selector_initial_counter_{starting_counter}","equal":equal,
              "request":"0xdc","status_before":statuses,"status_after":status_after,
              "status_bytes_unchanged":status_after==statuses,
              "counter_before":starting_counter,"counter_after":after_counter,
              "status_service_calls":len(service_events),
              "status_call_r0":[hex(e["r0"]) for e in service_events],
              "status_call_sp_aligned":all(e["sp_aligned"] for e in service_events),
              "counter_writes":[w for w in got["writes"] if w[0]==counter_addr],
              "events":got["events"],"fault":got["fault"],"r0":hex(got["r0"])}
        caller_results.append(call)
        if not equal or not call["status_bytes_unchanged"]:
            mismatches.append({"caller":call,"ref_fault":ref["fault"],"got_fault":got["fault"]})

    # Machine-word controls retain a slot-fitting body while altering one rule.
    baseline=body
    controls={}
    cases={
        "zero_boundary": ("cmp_zero",MANAGER,0,0x12345678,None),
        "unsigned_signedness": ("negative_one",MANAGER,0xFFFF,0x12345678,None),
        "halfword_store_width": ("byte_neighbors_preserved",MANAGER,0x0100,0x12345678,None),
        "global_pointer_offset": ("alternate_global_pointer",MANAGER,2,0x12345678,None),
    }
    mutant_bodies={
        "zero_boundary": mutate_word(baseline,0x10,0xE3510001,0xE3510000),
        "unsigned_signedness": mutate_word(mutate_word(baseline,0x14,0xA2411001,0x82411001),
                                            0x18,0xA1C014BC,0x81C014BC),
        "halfword_store_width": mutate_word(baseline,0x18,0xA1C014BC,0xA5C0104C),
        "global_pointer_offset": mutate_word(baseline,0x20,0x0043DCB4,0x0043DCB8),
    }
    for name,mut_body in mutant_bodies.items():
        mutant=stage_slot(original,ENTRY,SLOT,mut_body)[0]
        label,pointer,value,r0,ro_page=cases[name]
        setup=direct_setup(pointer,value,r0,alternative_pointer=ALT_MANAGER)
        if name=="halfword_store_width":
            setup=direct_setup(pointer,value,r0)
        if name=="global_pointer_offset":
            def setup(uc,pointer=pointer,value=value,r0=r0):
                uc.mem_write(GLOBAL+4,struct.pack("<I",pointer))
                uc.mem_write(GLOBAL+8,struct.pack("<I",ALT_MANAGER))
                uc.mem_write((pointer+0x64C)&U32,struct.pack("<H",value))
                uc.mem_write((ALT_MANAGER+0x64C)&U32,struct.pack("<H",7))
        result,ref,got=compare_direct(original,mutant,label,pointer,value,r0,ro_page)
        controls[name]={"detected":not result["equal"],"case":label,"mutant_fault":got["fault"],"mutant_writes":got["writes"]}
        if not controls[name]["detected"]: mismatches.append({"mutation":name,"result":result})

    changed_status=any(a!=b and not (ENTRY-CODE_BASE)<=i<(ENTRY-CODE_BASE)+SLOT
                       for i,(a,b) in enumerate(zip(original,staged_status)))
    report={"schema_version":1,"image_sha256":sha(original),"status_source_sha256":sha(STATUS_SOURCE.read_bytes()),
            "selector_source_sha256":sha(SELECTOR_SOURCE.read_bytes()),"status_object_sha256":sha(obj.read_bytes()),
            "selector_object_sha256":sha(selector_obj.read_bytes()),"entry":hex(ENTRY),"slot_size":SLOT,
            "compiled_body_size":len(body),"status_relocations":[],"exact_matching":staged_status[ENTRY-CODE_BASE:ENTRY-CODE_BASE+SLOT]==original[ENTRY-CODE_BASE:ENTRY-CODE_BASE+SLOT],
            "selector_body_size":len(selector_body),"selector_relocations":targets,
            "direct_cases":direct,"caller_compositions":caller_results,"mutation_controls":controls,
            "mismatch_count":len(mismatches),"mismatches":mismatches,
            "ips_replay":apply_ips(original,ips)==staged_status,"changed_outside_slot":changed_status,
            "composition_ips_replay":apply_ips(original,composition_ips)==composed,
            "composition_changed_outside_slots":any(a!=b and not ((ENTRY-CODE_BASE)<=i<(ENTRY-CODE_BASE)+SLOT or (SELECTOR-CODE_BASE)<=i<(SELECTOR-CODE_BASE)+SELECTOR_SLOT) for i,(a,b) in enumerate(zip(original,composed))),
            "status_compiler_command":compiler_args,"selector_compiler_command":selector_args}
    (args.out/"report.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"body_size":len(body),"slot_size":SLOT,"relocations":len(relocs),
        "direct_cases":[{"label":x["label"],"equal":x["equal"],"fault":x["fault"]} for x in direct],
        "caller_compositions":[{"label":c["label"],"equal":c["equal"],"calls":c["status_service_calls"],"counter_after":c["counter_after"],"status_bytes_unchanged":c["status_bytes_unchanged"]} for c in caller_results],
        "controls":controls,"mismatch_count":len(mismatches),"ips_replay":report["ips_replay"],
        "composition_ips_replay":report["composition_ips_replay"],"changed_outside_slot":changed_status,
        "composition_changed_outside_slots":report["composition_changed_outside_slots"]},indent=2))
    return 1 if mismatches or changed_status or report["composition_changed_outside_slots"] else 0

if __name__=="__main__": raise SystemExit(main())
