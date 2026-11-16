#!/usr/bin/env python3
"""Differential test for script_vm_func_00339d98 (0x00339d98) on Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the script_vm_func_00339d98
body, relocates its calls/jump table, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Observed and compared:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with the arguments each helper receives (the
    zero-argument helpers log only their name);
  * full work (0x10000-byte page containing the 0x4A58-byte object), full
    script-process page, and the 0x100-byte global window at 0x00435D80;
  * every write outside the private stack.

Coverage:
  * dispatch states 0..15 plus 0xFFFF, including the 14-entry table boundary
    (`cmp #0xd; bhi` in the compiled candidate);
  * the state-1 poll retry (returns 0 twice, then non-zero) and its failure;
  * every wait gate (states 2..8) passing and failing; a failing gate is
    observed with the iteration flag already set so the routine terminates
    exactly as the original does instead of looping forever;
  * both 0x0023EBC8 results, null and non-null pointer fields, distinct global
    pointer copies, and the script-process state clear at +0x108;
  * resume from each state so no list of actions is only observed once.

The unchecked fault path (0x002972F8 returning null, which the original
dereferences at +0x108 without a guard) and the genuinely non-terminating
default loop (state >= 14 with flag bit 0 clear) are documented in the function
record, not exercised here.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_00339d98"

FUNC_ADDR = 0x00339D98
FUNC_SIZE = 604

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00400000  # through 0x00500000: covers the function, stubs, globals
WORK_ADDR = 0x00600000
WORK_SIZE = 0x00010000
PROCESS_ADDR = 0x00700000
PROCESS_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

GLOBAL_ADDR = 0x00435D90
GLOBAL_WINDOW_ADDR = 0x00435D80
GLOBAL_WINDOW_SIZE = 0x100

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct-call targets.  Stubs live at the original addresses, so both the
# pinned bytes and the relocated candidate resolve to the same place.
STUB_2C3AA8 = 0x002C3AA8
STUB_394EE0 = 0x00394EE0
STUB_39493C = 0x0039493C
STUB_2972F8 = 0x002972F8
STUB_23EBC8 = 0x0023EBC8
STUB_328F60 = 0x00328F60
STUB_3291D8 = 0x003291D8
STUB_2C3A24 = 0x002C3A24

STUB_NAMES = {
    STUB_2C3AA8: "engine_func_002c3aa8",
    STUB_394EE0: "script_vm_func_00394ee0",
    STUB_39493C: "engine_func_0039493c",
    STUB_2972F8: "scrScriptProcess_func_002972f8",
    STUB_23EBC8: "script_vm_func_0023ebc8",
    STUB_328F60: "engine_func_00328f60",
    STUB_3291D8: "engine_func_003291d8",
    STUB_2C3A24: "engine_func_002c3a24",
}

ZERO_ARG_STUBS = {STUB_394EE0, STUB_39493C, STUB_328F60, STUB_3291D8}

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}

GLOBAL_FIELDS = {
    "field_0c": 0x0C,
    "field_10": 0x10,
    "field_14": 0x14,
    "field_18": 0x18,
    "field_1c": 0x1C,
    "field_20": 0x20,
    "field_24": 0x24,
    "field_28": 0x28,
    "field_2c": 0x2C,
}
GLOBAL_DEFAULTS = {
    name: 0x0C0C0C0C + offset * 0x01010101 for name, offset in GLOBAL_FIELDS.items()
}

WORK_FIELDS = (
    "field_2230",
    "field_2234",
    "field_2238",
    "field_223c",
    "field_2240",
    "field_2244",
    "field_2248",
    "field_224c",
    "field_2250",
    "field_2254",
)
WORK_OFFSETS = {
    "field_2230": 0x2230,
    "field_2234": 0x2234,
    "field_2238": 0x2238,
    "field_223c": 0x223C,
    "field_2240": 0x2240,
    "field_2244": 0x2244,
    "field_2248": 0x2248,
    "field_224c": 0x224C,
    "field_2250": 0x2250,
    "field_2254": 0x2254,
}
WORK_DEFAULTS = {
    name: 0x22300000 + offset for name, offset in
    (("field_2230", 0x30), ("field_2234", 0x34), ("field_2238", 0x38),
     ("field_223c", 0x3C), ("field_2240", 0x40), ("field_2244", 0x44),
     ("field_2248", 0x48), ("field_224c", 0x4C), ("field_2250", 0x50),
     ("field_2254", 0x54))
}

PROCESS_STATE_INIT = 0xA5A5BEEF


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def elf_symbol_value(obj_file: Path, wanted: str) -> int:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = next(s for s in sections if s[1] == 2)
    strtab = sections[symtab[6]]
    entsize = symtab[9] or 16
    for i in range(symtab[5] // entsize):
        st_name, st_val, _st_size, _st_info, _st_other, _st_shndx = (
            struct.unpack_from("<IIIBBH", data, symtab[4] + i * entsize)
        )
        name = data[strtab[4] + st_name :].split(b"\x00")[0].decode(
            "ascii", errors="replace")
        if name == wanted:
            return st_val & ~1
    raise RuntimeError(f"symbol {wanted} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    if "script_vm_func_00339d98" not in funcs:
        raise RuntimeError(
            f"script_vm_func_00339d98 not found in {obj_file}: {sorted(funcs)}"
        )
    code_raw, relocs = funcs["script_vm_func_00339d98"]
    code = bytearray(code_raw)
    func_sym = elf_symbol_value(obj_file, "script_vm_func_00339d98")

    for rel in relocs:
        symbol = rel.symbol_name
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address, name in STUB_NAMES.items():
                if name in symbol:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {symbol!r}")
            displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if symbol in ("", ".text"):
                target = FUNC_ADDR + (addend - func_sym)
            else:
                raise RuntimeError(
                    f"unexpected ABS32 relocation against {symbol!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {symbol!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def build_globals(case: dict) -> bytes:
    page = bytearray(GLOBAL_WINDOW_SIZE)
    base = GLOBAL_ADDR - GLOBAL_WINDOW_ADDR
    for i in range(0, GLOBAL_WINDOW_SIZE, 4):
        struct.pack_into("<I", page, i, 0xA5A50000 | i)
    for name, offset in GLOBAL_FIELDS.items():
        value = case.get(name, GLOBAL_DEFAULTS[name])
        struct.pack_into("<I", page, base + offset, value & 0xFFFFFFFF)
    return bytes(page)


def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    for i in range(0, WORK_SIZE, 4):
        struct.pack_into("<I", page, i, 0x5A5A0000 | (i & 0xFFFF))
    for name in WORK_FIELDS:
        value = case.get(name, WORK_DEFAULTS[name])
        struct.pack_into("<I", page, WORK_OFFSETS[name], value & 0xFFFFFFFF)
    struct.pack_into("<H", page, 0x49FC, case.get("flag", 0) & 0xFFFF)
    struct.pack_into("<H", page, 0x49FE, case.get("state", 0) & 0xFFFF)
    return bytes(page)


def build_process(case: dict) -> bytes:
    page = bytearray(PROCESS_SIZE)
    for i in range(0, PROCESS_SIZE, 4):
        struct.pack_into("<I", page, i, 0xC3C30000 | (i & 0xFFFF))
    struct.pack_into("<I", page, 0x108, PROCESS_STATE_INIT)
    return bytes(page)


def read_u16(page: bytes, offset: int) -> int:
    return struct.unpack_from("<H", page, offset)[0]


class StartRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(PROCESS_ADDR, PROCESS_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.poll_index = 0
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_2C3AA8:
            self._log(address, r0)
        elif address == STUB_2C3A24:
            self._log(address, r0)
        elif address == STUB_2972F8:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, PROCESS_ADDR)
        elif address == STUB_23EBC8:
            self._log(address, r0)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("ret_23ebc8", 1) & 0xFFFFFFFF)
        elif address == STUB_394EE0:
            self._log(address)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("ret_394ee0", 1) & 0xFFFFFFFF)
        elif address == STUB_39493C:
            self._log(address)
            sequence = self.case.get("ret_39493c", [1])
            value = sequence[min(self.poll_index, len(sequence) - 1)]
            self.poll_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address in (STUB_328F60, STUB_3291D8):
            self._log(address)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.poll_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        globals_page = build_globals(case)
        self.uc.mem_write(GLOBAL_WINDOW_ADDR, globals_page)
        process_page = build_process(case)
        self.uc.mem_write(PROCESS_ADDR, process_page)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = [
            (address, size) for address, size in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            and not (WORK_ADDR <= address < WORK_ADDR + WORK_SIZE)
            and not (PROCESS_ADDR <= address < PROCESS_ADDR + PROCESS_SIZE)
        ]

        work = bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE))
        process = bytes(self.uc.mem_read(PROCESS_ADDR, PROCESS_SIZE))
        globals_now = bytes(self.uc.mem_read(GLOBAL_WINDOW_ADDR,
                                             GLOBAL_WINDOW_SIZE))
        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self.call_log,
            "work": work,
            "process": process,
            "globals": globals_now,
            "work_state": read_u16(work, 0x49FE),
            "work_flag": read_u16(work, 0x49FC),
            "process_state": struct.unpack_from("<I", process, 0x108)[0],
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"]))
    for key in ("work", "process", "globals"):
        if orig[key] != cand[key]:
            differing = [
                i for i, (a, b) in enumerate(zip(orig[key], cand[key])) if a != b
            ]
            problems.append(
                f"{key} memory differs at {len(differing)} byte(s), first "
                f"offsets {[hex(i) for i in differing[:16]]}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {"name": name, "state": 0, "flag": 0, "ret_39493c": [1],
            "ret_394ee0": 1, "ret_23ebc8": 1}
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- full path and the state-1 poll loop
    cases.append(base_case("full path from state 0"))
    cases.append(base_case("state 1 poll retries twice then succeeds",
                           ret_39493c=[0, 0, 1]))
    cases.append(base_case("state 1 poll fails once with flag already set",
                           flag=1, ret_39493c=[0]))
    cases.append(base_case("state 1 poll succeeds with flag already set",
                           flag=1, ret_39493c=[1]))
    cases.append(base_case("resume at state 1", state=1, ret_39493c=[1]))
    cases.append(base_case("resume at state 1 with poll failure",
                           state=1, flag=1, ret_39493c=[0]))

    # --- every state-2..7 wait gate passing
    for state in range(2, 8):
        cases.append(base_case(f"resume at state {state} (gate passes)",
                               state=state))
    # ... and failing, with the flag already set so both terminate.
    for state, field in ((2, "field_2250"), (3, "field_2230"),
                         (4, "field_2234"), (5, "field_2238"),
                         (6, "field_2240"), (7, "field_223c")):
        cases.append(base_case(f"state {state} gate {field} null",
                               state=state, flag=1, **{field: 0}))

    # --- state 8 gate and state 9 argument result
    cases.append(base_case("state 8 gate null", state=8, flag=1,
                           field_2244=0))
    cases.append(base_case("state 8 gate passes", state=8, field_2244=0x99999999))
    cases.append(base_case("state 9 process id result zero", state=9, flag=1,
                           ret_23ebc8=0))
    cases.append(base_case("state 9 process id result non-zero", state=9))

    # --- resume from the tail states
    for state in (10, 11, 12, 13):
        cases.append(base_case(f"resume at state {state}", state=state))

    # --- dispatch boundary: 0..13 table, 14/15/0xFFFF default
    for state in (14, 15, 0xFFFF):
        cases.append(base_case(f"state {state} default with flag set",
                               state=state, flag=1))

    # --- script-process creation details
    cases.append(base_case("script process state cleared from 0xFFFFFFFF",
                           ret_394ee0=0xFFFFFFFF))
    cases.append(base_case("394ee0 result ignored (zero)", ret_394ee0=0))
    cases.append(base_case("23ebc8 sees id 0x3e only", state=8,
                           ret_23ebc8=1))
    cases.append(base_case("global field_14 null stops at state 2", flag=1,
                           field_14=0))
    cases.append(base_case("global field_18 null stops at state 3", flag=1,
                           field_18=0))
    cases.append(base_case("all global pointers null", flag=1,
                           **{name: 0 for name in GLOBAL_FIELDS}))
    cases.append(base_case("all work pointers null, state 0, flag set",
                           state=0, flag=1,
                           **{name: 0 for name in WORK_FIELDS}))

    # --- distinct pointer copies and 32-bit boundary values
    cases.append(base_case("distinct pointer values",
                           field_0c=0x00000001, field_10=0x7FFFFFFF,
                           field_14=0x80000000,
                           field_18=0xFFFFFFFE, field_1c=0x0000FFFF,
                           field_20=0xFFFF0000, field_24=0x12345678,
                           field_28=0x9ABCDEF0, field_2c=0xDEADBEEF))
    cases.append(base_case("distinct work pointer values", state=2,
                           field_2230=0x11111111, field_2234=0x22222222,
                           field_2238=0x33333333, field_223c=0x44444444,
                           field_2240=0x55555555, field_2244=0x66666666,
                           field_2250=0x77777777))
    cases.append(base_case("state 12 shares tail with state 13", state=12,
                           flag=0xFFFF))
    cases.append(base_case("flag bit 0 already set, state 13", state=13,
                           flag=0x0001))
    cases.append(base_case("flag other bits only, state 13", state=13,
                           flag=0xFFFE))
    cases.append(base_case("flag 0xFFFF, state 0", flag=0xFFFF))
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = StartRunner().run(orig_code, case)
        cand = StartRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  (state {case['state']}->"
            f"{orig['work_state']}, flag->{orig['work_flag']:#06x}, "
            f"{len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing script_vm_func_00339d98 (0x00339d98)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("process_id", "constexpr u32 kScriptProcessId = 0x3EU;",
         "constexpr u32 kScriptProcessId = 0x3FU;"),
        ("global_field_copy", "work->field_2238 = globals()->field_20;",
         "work->field_2238 = globals()->field_24;"),
        ("script_process_arguments",
         "scrScriptProcess_func_002972f8(\n"
         "                globals()->field_14, globals()->field_0c);",
         "scrScriptProcess_func_002972f8(\n"
         "                globals()->field_0c, globals()->field_14);"),
        ("tail_helper_identity", "engine_func_003291d8();",
         "engine_func_00328f60();"),
    ):
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = StartRunner().run(orig_code, case)
            bad = StartRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
