#!/usr/bin/env python3
"""Differential test for shop_func_003a0bb8 (0x003A0BB8) using Unicorn ARM.

The candidate C++ in src/engine/leaf_batch41_c.cpp is compiled with
`compile_tu_armv6k`, its body extracted from the object, and every direct-call
and rodata relocation is re-pointed at deterministic helpers.  The pinned
original (extracted/exefs/code.bin) and the relocated candidate then run in
separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument (and the three hard-float
    arguments of 0x0029A2B0 as raw bits);
  * the NUL-terminated text argument observed by 0x00291018;
  * the shop controller page, slot/inner-record page, and helper scratch page
    byte-for-byte, plus any emulated write outside the private stack.

Coverage: phases 0, 1, and every other value; the signed gate at transform+0x8A;
modes 0..6, 7, 8, 9 and 0xFFFFFFFF; the 0x0029E398 poll returning zero/non-zero;
both text branches with zero/negative/high entry handles; absent and dead slots;
and the signed state boundary at slot->inner+0xC (-2^31, -1, 0, 1, 2^31-1,
0xFFFFFFFF).  Negative controls mutate the buy result, the sell-off text, the
epilogue slot offset and the mode limit.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_003a0bb8"

FUNC_ADDR = 0x003A0BB8
FUNC_SIZE = 476

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every direct helper below 0x400000
OBJECT_ADDR = 0x00430000
OBJECT_SIZE = 0x00020000  # covers self+0x15D48
SCRATCH_ADDR = 0x00460000
SCRATCH_SIZE = 0x00001000
INNER_ADDR = 0x00500000
INNER_SIZE = 0x00010000
RODATA_ADDR = 0x00750000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_230F84 = 0x00230F84
STUB_2333D4 = 0x002333D4
STUB_2B9220 = 0x002B9220
STUB_2BEF70 = 0x002BEF70
STUB_2BEF7C = 0x002BEF7C
STUB_2313D4 = 0x002313D4
STUB_29E398 = 0x0029E398
STUB_291018 = 0x00291018
STUB_2971E4 = 0x002971E4
STUB_19DFBC = 0x0019DFBC
STUB_2AE16C = 0x002AE16C
STUB_2A06C8 = 0x002A06C8
STUB_29A2B0 = 0x0029A2B0

STUB_NAMES = {
    STUB_230F84: "func_00230f84",
    STUB_2333D4: "func_002333d4",
    STUB_2B9220: "func_002b9220",
    STUB_2BEF70: "func_002bef70",
    STUB_2BEF7C: "func_002bef7c",
    STUB_2313D4: "func_002313d4",
    STUB_29E398: "func_0029e398",
    STUB_291018: "func_00291018",
    STUB_2971E4: "func_002971e4",
    STUB_19DFBC: "func_0019dfbc",
    STUB_2AE16C: "func_002ae16c",
    STUB_2A06C8: "func_002a06c8",
    STUB_29A2B0: "func_0029a2b0",
}

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

# Distinct sentinels for the text/format pointers handed to the text helpers.
TEXT_OBJECT = 0x00A0A160
FORMAT_OBJECT = 0x00B0B168

# Offsets inside the shop controller page.
OFF_RESULT4 = 0x4
OFF_PHASE8 = 0x8
OFF_TEXT160 = 0x160
OFF_FORMAT168 = 0x168
OFF_TRANSFORM = 0x3C8
OFF_TRANSFORM_X_C = 0x0C
OFF_TRANSFORM_Y_10 = 0x10
OFF_TRANSFORM_GATE8A = 0x8A
OFF_MODE860 = 0x860
OFF_SLOT15D48 = 0x15D48

INNER_RECORD = 0x100


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - (1 << 32) if value & 0x80000000 else value


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "003a0bb8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"shop_func_003a0bb8 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address in STUB_NAMES:
                if f"{address:08x}" in rel.symbol_name:
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 against a section symbol
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )

    rodata = elf_sections(obj_file).get(".rodata", b"")
    return bytes(code), rodata


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
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


def read_c_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        try:
            byte = uc.mem_read(address + index, 1)[0]
        except Exception:
            break
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class ShopRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(SCRATCH_ADDR, SCRATCH_SIZE)
        self.uc.mem_map(INNER_ADDR, INNER_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _s32(self, address: int) -> int:
        return s32(self._u32(address))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_230F84:
            self._log(address, r0)
            self.uc.mem_write(SCRATCH_ADDR + 0x32, bytes([r0 & 0xFF]))
        elif address == STUB_2333D4:
            self._log(address, r0, r1)
        elif address == STUB_2B9220:
            self._log(address, r0, r1)
        elif address == STUB_2BEF70:
            value = self._s32(r0 + OFF_TRANSFORM_Y_10) >> 12
            self._log(address, r0, value)
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_2BEF7C:
            value = self._s32(r0 + OFF_TRANSFORM_X_C) >> 12
            self._log(address, r0, value)
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
        elif address == STUB_2313D4:
            x = s32(r1)
            y = s32(r2)
            self._log(address, r0, x, y)
            self.uc.mem_write(r0, struct.pack("<ff", float(x), float(y)))
        elif address == STUB_29E398:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("poll", 1) & 0xFFFFFFFF)
        elif address == STUB_291018:
            text = read_c_string(self.uc, r1)
            self._log(address, r0, text)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("entry", 0x1000) & 0xFFFFFFFF
            )
        elif address == STUB_2971E4:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_19DFBC:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2AE16C:
            if r0 == 0:
                result = 0
            else:
                inner = self._u32(r0 + 8)
                result = 1 if (inner != 0 and self._u32(inner + 4) != 0) else 0
            self._log(address, r0, result)
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_2A06C8:
            self._log(address, r0, r1)
            if r0 != 0:
                word = self._u32(r0)
                self.uc.mem_write(r0, struct.pack("<I", word & ~0x200000))
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_29A2B0:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc.reg_read(arm.UC_ARM_REG_S1)
            s2 = uc.reg_read(arm.UC_ARM_REG_S2)
            self._log(address, r0, r1, s0, s1, s2)
            uc.reg_write(
                arm.UC_ARM_REG_R0, self.case.get("flush_ret", 0x29A2B0) & 0xFFFFFFFF
            )
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(RODATA_ADDR, b"\x00" * RODATA_SIZE)
        if rodata:
            self.uc.mem_write(RODATA_ADDR, rodata)

        object_page = bytearray(OBJECT_SIZE)
        struct.pack_into("<I", object_page, OFF_RESULT4, case.get("result4", 0x11111111))
        struct.pack_into("<I", object_page, OFF_PHASE8, case.get("phase", 0) & 0xFFFFFFFF)
        struct.pack_into("<I", object_page, OFF_TEXT160, TEXT_OBJECT)
        struct.pack_into("<I", object_page, OFF_FORMAT168, FORMAT_OBJECT)
        struct.pack_into("<I", object_page, OFF_MODE860, case.get("mode", 0) & 0xFFFFFFFF)
        struct.pack_into(
            "<I",
            object_page,
            OFF_TRANSFORM + OFF_TRANSFORM_X_C,
            case.get("x_q12", 0x00001234) & 0xFFFFFFFF,
        )
        struct.pack_into(
            "<I",
            object_page,
            OFF_TRANSFORM + OFF_TRANSFORM_Y_10,
            case.get("y_q12", 0xFFFFF000) & 0xFFFFFFFF,
        )
        object_page[OFF_TRANSFORM + OFF_TRANSFORM_GATE8A] = (
            case.get("gate", 0) & 0xFF
        )
        slot_pointer = 0
        if case.get("slot", "live") != "none":
            slot_pointer = INNER_ADDR
        struct.pack_into("<I", object_page, OFF_SLOT15D48, slot_pointer)
        self.uc.mem_write(OBJECT_ADDR, bytes(object_page))

        inner_page = bytearray(INNER_SIZE)
        struct.pack_into("<I", inner_page, 0, case.get("slot_flags", 0x00C00000))
        inner_pointer = 0 if case.get("inner_pointer_null") else INNER_ADDR + INNER_RECORD
        struct.pack_into("<I", inner_page, 8, inner_pointer)
        record = INNER_ADDR + INNER_RECORD
        struct.pack_into("<I", inner_page, INNER_RECORD + 4, case.get("inner_live", 1))
        struct.pack_into(
            "<I",
            inner_page,
            INNER_RECORD + 0x0C,
            case.get("signed_state", 0) & 0xFFFFFFFF,
        )
        self.uc.mem_write(INNER_ADDR, bytes(inner_page))

        self.uc.mem_write(SCRATCH_ADDR, b"\x00" * SCRATCH_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        # Unicorn's ARM core leaves the VFP unit disabled (FPEXC.EN clear), so
        # the original's vldr/vmov sequence would raise an invalid-instruction
        # fault.  Enable it exactly as the 3DS system does at boot.
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJECT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_object = OBJECT_ADDR <= address < OBJECT_ADDR + OBJECT_SIZE
            in_inner = INNER_ADDR <= address < INNER_ADDR + INNER_SIZE
            in_scratch = SCRATCH_ADDR <= address < SCRATCH_ADDR + SCRATCH_SIZE
            if not (in_stack or in_object or in_inner or in_scratch):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
                "inner": bytes(self.uc.mem_read(INNER_ADDR, INNER_SIZE)),
                "scratch": bytes(self.uc.mem_read(SCRATCH_ADDR, SCRATCH_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "phase": 1,
        "gate": 1,
        "mode": 0,
        "poll": 1,
        "entry": 0x1000,
        "slot": "live",
        "inner_live": 1,
        "signed_state": 0,
        "x_q12": 0x00001234,
        "y_q12": 0x00005678,
        "flush_ret": 0x29A2B0,
        "result4": 0x11111111,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- phase dispatch
    cases.append(base_case("phase 0", phase=0))
    cases.append(base_case("phase 0 with dead slot", phase=0, slot="none"))
    cases.append(base_case("phase 1 gate clear", phase=1, gate=0))
    cases.append(base_case("phase 2 skips phase work", phase=2))
    cases.append(base_case("phase 0xFFFFFFFF skips phase work", phase=0xFFFFFFFF))

    # --- mode dispatch on the phase-1 / gate-set path
    for mode in list(range(0, 9)) + [9, 0xFFFFFFFF, 0x80000000]:
        cases.append(base_case(f"mode {mode:#x} poll 1", mode=mode, poll=1))
        cases.append(base_case(f"mode {mode:#x} poll 0", mode=mode, poll=0))

    # --- entry-handle variants for the text branches
    for entry in (0, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, 0x12345678):
        cases.append(base_case(f"mode 7 entry {entry:#x}", mode=7, entry=entry))
        cases.append(base_case(f"mode 8 entry {entry:#x}", mode=8, entry=entry))

    # --- signed gate values (read with ldrsb)
    for gate in (0x00, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"gate {gate:#x} mode 7", gate=gate, mode=7))

    # --- Q12 pair boundaries and signed right shift
    for x, y in (
        (0x00000000, 0x00000000),
        (0x7FFFFFFF, 0x7FFFFFFF),
        (0x80000000, 0x80000000),
        (0x80000FFF, 0x7FFFF000),
        (0xFFFFFFFF, 0x00000001),
    ):
        cases.append(base_case(f"q12 x={x:#x} y={y:#x}", x_q12=x, y_q12=y))

    # --- slot / inner-record states
    cases.append(base_case("slot absent", slot="none"))
    cases.append(base_case("slot present inner pointer null", slot="live",
                           inner_pointer_null=True))
    cases.append(base_case("slot present inner dead", slot="live", inner_live=0))

    # --- signed state at inner+0xC (bge boundary)
    for state in (0, 1, 2, -1, -2, 0x7FFFFFFF, 0x80000000, 0x80000001,
                  0xFFFFFFFF):
        cases.append(
            base_case(f"inner signed state {state:#x}", signed_state=state)
        )
        cases.append(
            base_case(f"inner signed state {state:#x} phase 0",
                      signed_state=state, phase=0, gate=0)
        )

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = ShopRunner().run(orig_code, b"", case)
        cand = ShopRunner().run(cand_code, rodata, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
    return passed


def main() -> None:
    print("Testing shop_func_003a0bb8 (0x003A0BB8)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)
    print(f"  [PASS] {passed}/{len(cases)} differential cases")

    print("Negative controls:")
    for name, old, new in (
        ("buy_result", "constexpr u32 kItemBuyResult4 = 5;",
         "constexpr u32 kItemBuyResult4 = 4;"),
        ("selloff_text", 'constexpr char kSellOffText[] = "shop_selloff";',
         'constexpr char kSellOffText[] = "shop_sellofx";'),
        ("slot_offset", "constexpr u32 kSlotWord15D48 = 0x15D48;",
         "constexpr u32 kSlotWord15D48 = 0x15D44;"),
        ("mode_limit", "constexpr u32 kModeLimit = 9;",
         "constexpr u32 kModeLimit = 8;"),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = ShopRunner().run(orig_code, b"", case)
            bad = ShopRunner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
