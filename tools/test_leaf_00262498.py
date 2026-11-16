#!/usr/bin/env python3
"""Differential test for camp_func_00262498 (0x00262498) using Unicorn ARM.

The candidate in src/engine/leaf_batch41_c.cpp is compiled, its eight direct
calls are relocated to deterministic stubs placed at the original ROM targets,
and the pinned original (extracted/exefs/code.bin) runs against the candidate
in separate executions on identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and d8-d15;
  * the ordered call log with every integer argument and the exact raw bits of
    every floating-point argument, including the 0x2841A0 destination pointer
    (normalised to "<stack>" because the two bodies have different frames);
  * the full self, interaction-table, indexed-object, record and scale-table
    pages, which must be identical after the run;
  * any emulated write outside the private stack and the fixture pages.

Coverage: both inactive-self gate tests, the signed arg2 branch, a null indexed
object, the fixed nine-entry scan (zero ids, null records, kind mismatch, and
selections 5/6/other), weights 0..18, the 0xFA0 special path for every high
nibble, the low-flag boundaries 0/1/0x7FF/0x800/0xFFE/0xFFF, the +0x43 percent
path (0/1/0x7F/0x80/0xFF), signed arg2 boundaries, and helper-mutated state that
clears the low flags mid-loop to exercise the otherwise-unreachable post-loop
zero-flag/zero-byte return.

Negative controls mutate the low-flag mask, the special value, the record kind,
the selection addend, the object word offset, and the entry count; each mutant
must be detected by the same comparison.
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
OUT_DIR = ROOT / "build/test_leaf_00262498"

FUNC_ADDR = 0x00262498
FUNC_SIZE = 432

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the body and every direct-call target
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00100000  # covers the 0x00446D30 scale table
SELF_ADDR = 0x00710000
SELF_SIZE = 0x00001000
TABLE_ADDR = 0x00720000
TABLE_SIZE = 0x00001000
OBJECT_ADDR = 0x00730000
OBJECT_SIZE = 0x00002000
RECORD_ADDR = 0x00740000
RECORD_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SCALE_TABLE_ADDR = 0x00446D30
RECORD_STRIDE = 0x40

# Original direct-call targets; deterministic stubs live at these addresses so
# both the original bytes and the relocated candidate resolve to them.
STUB_2B66EC = 0x002B66EC
STUB_2841A0 = 0x002841A0
STUB_2AE394 = 0x002AE394
STUB_28412C = 0x0028412C
STUB_2A89E4 = 0x002A89E4
STUB_2840B8 = 0x002840B8
STUB_3BF764 = 0x003BF764
STUB_3BF7AC = 0x003BF7AC

STUB_NAMES = {
    STUB_2B66EC: "script_vm_func_002b66ec",
    STUB_2841A0: "script_vm_func_002841a0",
    STUB_2AE394: "script_vm_func_002ae394",
    STUB_28412C: "func_0028412c",
    STUB_2A89E4: "camp_func_002a89e4",
    STUB_2840B8: "camp_func_002840b8",
    STUB_3BF764: "func_003bf764",
    STUB_3BF7AC: "func_003bf7ac",
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
FLOAT_SAVED = {f"d{i}": getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16)}

MASK32 = 0xFFFFFFFF


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & MASK32))[0]


def round_f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def as_s32(value: int) -> int:
    value &= MASK32
    return value - 0x100000000 if value & 0x80000000 else value


def trunc_s32(value: float) -> int:
    """ARM VCVT.S32.F32: round towards zero; overflow yields 0x80000000."""
    if value != value:  # NaN
        return -0x80000000
    if value >= 2147483648.0 or value < -2147483648.0:
        return -0x80000000
    return int(value)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00262498" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_00262498 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        if target & 3:
            raise RuntimeError(f"unaligned direct-call target 0x{target:08x}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    # The pool is part of the symbol for this TU; no rodata relocation is used.
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def pack_u16_words(values: list[int]) -> list[int]:
    if len(values) % 2:
        values = values + [0]
    return [
        (values[i] & 0xFFFF) | ((values[i + 1] & 0xFFFF) << 16)
        for i in range(0, len(values), 2)
    ]


def record_word(kind: int, selection: int, tag: int = 0xABC) -> int:
    """Build a +0x38 record word with the observed bit layout."""
    return (
        ((tag & 0xFFF) << 20)
        | ((selection & 0xF) << 16)
        | ((kind & 0x1F) << 11)
        | 0x03FF
    )


def write_u32(page: bytearray, base: int, address: int, value: int) -> None:
    struct.pack_into("<I", page, address - base, value & MASK32)


def write_u16(page: bytearray, base: int, address: int, value: int) -> None:
    struct.pack_into("<H", page, address - base, value & 0xFFFF)


def write_u8(page: bytearray, base: int, address: int, value: int) -> None:
    page[address - base] = value & 0xFF


def build_self(case: dict) -> bytes:
    page = bytearray([0xCC]) * SELF_SIZE
    write_u16(page, SELF_ADDR, SELF_ADDR + 0x36, case.get("flags", 0x0234))
    write_u8(page, SELF_ADDR, SELF_ADDR + 0x43, case.get("byte43", 0))
    write_u16(page, SELF_ADDR, SELF_ADDR + 0x20, case.get("lookup_id", 0x1234))
    return bytes(page)


def build_table(case: dict) -> bytes:
    page = bytearray(TABLE_SIZE)
    write_u16(page, TABLE_ADDR, TABLE_ADDR + 0x24, case.get("table_sign", -7))
    entries = list(case.get("entries", ()))
    entries = (entries + [0] * 9)[:9]
    words = pack_u16_words(entries[:8])
    for index, word in enumerate(words):
        write_u32(page, TABLE_ADDR, TABLE_ADDR + 0x34 + index * 4, word)
    write_u16(page, TABLE_ADDR, TABLE_ADDR + 0x44, entries[8])
    return bytes(page)


def build_objects(case: dict) -> bytes:
    page = bytearray([0xCC]) * OBJECT_SIZE
    for slot in (0, 1):
        base = OBJECT_ADDR + slot * 0x100
        words = case.get("obj_words_b" if slot else "obj_words", ())
        words = (list(words) + [0] * 4)[:4]
        write_u16(page, OBJECT_ADDR, base + 0x16, case.get("obj_sign", 9))
        for index, word in enumerate(words):
            write_u32(page, OBJECT_ADDR, base + 0x34 + index * 4, word)
    return bytes(page)


def build_records(case: dict) -> bytes:
    page = bytearray([0xCC]) * RECORD_SIZE
    for ident, word in case.get("records", {}).items():
        base = RECORD_ADDR + (ident & 0xFF) * RECORD_STRIDE
        write_u32(page, RECORD_ADDR, base + 0x38, word)
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    table = case.get("scale_table")
    if table is None:
        # f32 values 1.0 .. 20.0 so every weight 0..18 is distinguishable.
        table = [f32_bits(float(index + 1)) for index in range(20)]
    for index, bits in enumerate(table[:20]):
        write_u32(page, DATA_ADDR, SCALE_TABLE_ADDR + index * 4, bits)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class WeightRunner:
    """One Unicorn machine with deterministic stubs at the ROM targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The tail scalers and the original body use VFP; enable it exactly as
        # the target does at boot.
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_CORTEX_A15)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(OBJECT_ADDR, OBJECT_SIZE)
        self.uc.mem_map(RECORD_ADDR, RECORD_SIZE)
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

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _is_stack(self, value: int) -> bool:
        return STACK_ADDR <= value < STACK_ADDR + STACK_SIZE

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        s0 = uc.reg_read(arm.UC_ARM_REG_S0) & MASK32
        s1 = uc.reg_read(arm.UC_ARM_REG_S1) & MASK32
        s2 = uc.reg_read(arm.UC_ARM_REG_S2) & MASK32
        s3 = uc.reg_read(arm.UC_ARM_REG_S3) & MASK32

        if address == STUB_2B66EC:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, TABLE_ADDR)
        elif address == STUB_2841A0:
            dst = "<stack>" if self._is_stack(r0) else f"0x{r0:08x}"
            self._log(address, dst, r1)
            words = struct.unpack(
                "<4I", bytes(uc.mem_read(TABLE_ADDR + 0x34, 16))
            )
            uc.mem_write(r0, struct.pack("<4I", *words))
            if r1 != 0:
                fifth = struct.unpack(
                    "<H", bytes(uc.mem_read(TABLE_ADDR + 0x44, 2))
                )[0]
                uc.mem_write(r0 + 0x10, struct.pack("<H", fifth))
        elif address == STUB_2AE394:
            self._log(address, r0)
            result = self.case.get("lookup_result")
            if result is None:
                result = (r0 * 3 + 1) & 0xFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result & MASK32)
        elif address == STUB_28412C:
            self._log(address, r0, r1, r2)
            bonus = self.case.get("bonus")
            if bonus is None:
                bonus = (r1 * 2 - 5) & MASK32
            uc.reg_write(arm.UC_ARM_REG_R0, bonus & MASK32)
        elif address == STUB_2A89E4:
            self._log(address, r0)
            if self.case.get("object_null", False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    OBJECT_ADDR + (r0 & 1) * 0x100,
                )
        elif address == STUB_2840B8:
            self._log(address, r0)
            records = self.case.get("records", {})
            if r0 not in records:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(
                    arm.UC_ARM_REG_R0,
                    RECORD_ADDR + (r0 & 0xFF) * RECORD_STRIDE,
                )
                if self.case.get("clear_flags_on_id") == r0:
                    uc.mem_write(
                        SELF_ADDR + 0x36, struct.pack("<H", 0)
                    )
        elif address == STUB_3BF764:
            self._log(address, r0, r1, r2, s0, s1, s2, s3)
            product = round_f32(bits_f32(s0) * bits_f32(s3))
            result = (trunc_s32(product) + as_s32(r1) + as_s32(r2)) & MASK32
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_3BF7AC:
            self._log(address, r0, s0)
            if as_s32(s0) >= as_s32(0x3F800000):
                result = r0
            else:
                product = round_f32(float(as_s32(r0)) * bits_f32(s0))
                result = trunc_s32(product) & MASK32
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(SELF_ADDR, build_self(case))
        self.uc.mem_write(TABLE_ADDR, build_table(case))
        self.uc.mem_write(OBJECT_ADDR, build_objects(case))
        self.uc.mem_write(RECORD_ADDR, build_records(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.ctl_flush_tb()
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("arg1", 0x12345678))
        self.uc.reg_write(
            arm.UC_ARM_REG_R2, case.get("arg2", 0) & MASK32
        )
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for index, (name, reg) in enumerate(FLOAT_SAVED.items()):
            self.uc.reg_write(reg, 0x1122334455667788 + index)
        self.uc.reg_write(arm.UC_ARM_REG_S0, 0x7F7FFFFF)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_self = SELF_ADDR <= address < SELF_ADDR + SELF_SIZE
            if not in_stack and not in_self:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "float_saved": {
                name: self.uc.reg_read(reg) for name, reg in FLOAT_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "object": bytes(self.uc.mem_read(OBJECT_ADDR, OBJECT_SIZE)),
                "record": bytes(self.uc.mem_read(RECORD_ADDR, RECORD_SIZE)),
                "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def first_difference(orig: bytes, cand: bytes) -> str:
    limit = min(len(orig), len(cand))
    for index in range(limit):
        if orig[index] != cand[index]:
            return (
                f"first difference at byte {index}: "
                f"orig=0x{orig[index]:02x} cand=0x{cand[index]:02x}"
            )
    if len(orig) != len(cand):
        return f"length differs: orig={len(orig)} cand={len(cand)}"
    return ""


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "float_saved"):
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
            problems.append(
                f"fixture {key}: " + first_difference(value, cand["fixtures"][key])
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


MIXED_RECORDS = {
    0x0101: record_word(0x14, 5),
    0x0202: record_word(0x14, 6),
    0x0303: record_word(0x15, 5),  # kind mismatch
    0x0505: record_word(0x14, 7),  # selection neither 5 nor 6
    0x0606: record_word(0x14, 0),
    0x0707: record_word(0x14, 15),
    0x0808: record_word(0x14, 6),
}
MIXED_ENTRIES = [
    0x0101, 0x0202, 0x0303, 0x0404, 0x0000, 0x0505, 0x0606, 0x0707, 0x0808
]
# 0x0101 +1, 0x0202 +2, 0x0808 +2 -> weight 5.  0x0404 is null.


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "flags": 0x0234,
        "byte43": 0x20,
        "arg1": 0x12345678,
        "arg2": -1,
        "lookup_id": 0x1234,
        "table_sign": -7,
        "obj_sign": 9,
        "entries": MIXED_ENTRIES,
        "records": dict(MIXED_RECORDS),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- inactive-self gate (0x002624A8..0x002624BC)
    cases.append(base_case("gate: low flags zero, byte zero", flags=0x0000,
                           byte43=0x00))
    cases.append(base_case("gate: low flags zero, byte 1", flags=0x0000,
                           byte43=0x01))
    cases.append(base_case("gate: high nibble only", flags=0xF000,
                           byte43=0x00))
    cases.append(base_case("gate: high nibble only, byte 1", flags=0xF000,
                           byte43=0x01))
    cases.append(base_case("gate: low bit set", flags=0x1001, byte43=0x00))

    # --- signed arg2 branch and the fixed nine-entry scan
    cases.append(base_case("negative arg2 / mixed records"))
    cases.append(base_case("arg2 zero / object path", arg2=0))
    cases.append(base_case("arg2 one / object path", arg2=1))
    cases.append(base_case("arg2 INT_MIN / table path", arg2=-0x80000000))
    cases.append(base_case("arg2 INT_MAX / object path", arg2=0x7FFFFFFF))
    cases.append(base_case("object null", arg2=2, object_null=True))
    cases.append(base_case("table all zero entries", entries=[0] * 9))
    cases.append(base_case("table all selection 6", entries=[0x0202] * 9,
                           records={0x0202: record_word(0x14, 6)}))
    cases.append(base_case("table all selection 5", entries=[0x0101] * 9,
                           records={0x0101: record_word(0x14, 5)}))
    cases.append(base_case(
        "table all kind mismatch",
        entries=[0x0303] * 9,
        records={0x0303: record_word(0x1F, 6)},
    ))
    cases.append(base_case(
        "table all records null",
        entries=[0x0999] * 9,
        records={},
    ))
    cases.append(base_case(
        "object path mixed records",
        arg2=4,
        obj_words=pack_u16_words(MIXED_ENTRIES[:8]),
        obj_sign=-3,
    ))
    cases.append(base_case(
        "object path all selection 6",
        arg2=5,
        obj_words=pack_u16_words([0x0202] * 8),
        records={0x0202: record_word(0x14, 6)},
    ))
    cases.append(base_case(
        "object parity distinct words",
        arg2=1,
        obj_words=pack_u16_words(MIXED_ENTRIES[:8]),
        obj_words_b=pack_u16_words([0x0202, 0x0202, 0x0202, 0x0202,
                                    0x0202, 0x0202, 0x0202, 0x0202]),
        records={0x0202: record_word(0x14, 6)},
    ))

    # --- post-loop low-flag boundaries and special value
    for low in (0x001, 0x002, 0x7FF, 0x800, 0xFFE, 0xFFF):
        cases.append(base_case(f"low flags 0x{low:03x}", flags=low,
                               byte43=0x00))
    for flags in (0x0FA0, 0x1FA0, 0x7FA0, 0xFFA0):
        cases.append(base_case(f"special flags 0x{flags:04x}", flags=flags))
    cases.append(base_case("near-special low flags 0xFA1", flags=0x0FA1))

    # --- fixed-point percentage path (low flags zero, +0x43 non-zero)
    for percent in (0x00, 0x01, 0x32, 0x63, 0x64, 0x7F, 0x80, 0xFF):
        cases.append(base_case(
            f"percent 0x{percent:02x}",
            flags=0x0000,
            byte43=percent,
        ))
    cases.append(base_case("percent path, weight ignored", flags=0xF000,
                           byte43=0x64, arg2=7))

    # --- helper-mutated state: low flags cleared after the guard
    cases.append(base_case(
        "helper clears flags, byte non-zero",
        flags=0x0123,
        byte43=0x40,
        clear_flags_on_id=0x0101,
    ))
    cases.append(base_case(
        "helper clears flags, byte zero",
        flags=0x0123,
        byte43=0x00,
        clear_flags_on_id=0x0101,
    ))
    cases.append(base_case(
        "helper clears flags, all entries zero",
        flags=0x0123,
        byte43=0x00,
        entries=[0] * 9,
        clear_flags_on_id=0x0101,
    ))

    # --- helper result boundaries
    for lookup in (0x00000000, 0x00000001, 0xFFFFFFFF, 0x7FFFFFFF,
                   0x80000000):
        cases.append(base_case(f"lookup result 0x{lookup:08x}",
                               lookup_result=lookup))
    for bonus in (0x00000000, 0x00001234, 0xFFFFFFFF, 0x7FFFFFFF,
                  0x80000000):
        cases.append(base_case(f"bonus 0x{bonus:08x}", bonus=bonus))
    for sign in (-0x8000, -1, 0, 1, 0x7FFF):
        cases.append(base_case(f"table sign {sign}", table_sign=sign))
        cases.append(base_case(f"object sign {sign}", arg2=0, obj_sign=sign))

    # --- scale-table values and important float products
    cases.append(base_case(
        "rom scale table",
        scale_table=[f32_bits(1.0), f32_bits(1.25), f32_bits(1.5),
                     f32_bits(1.875)] + [0] * 16,
    ))
    cases.append(base_case(
        "fractional scale table",
        scale_table=[f32_bits(0.5), f32_bits(0.25), f32_bits(0.125),
                     f32_bits(0.0625), f32_bits(1.0), f32_bits(2.0)] + [0] * 14,
    ))
    cases.append(base_case(
        "negative scale table",
        scale_table=[f32_bits(-1.0), f32_bits(-1.5), f32_bits(0.0),
                     f32_bits(-0.0)] + [f32_bits(2.0)] * 16,
    ))
    cases.append(base_case("arg1 forwarded raw", flags=0x0FA0,
                           arg1=0xDEADBEEF))
    cases.append(base_case(
        "combined stress",
        flags=0x0F23,
        byte43=0xA5,
        arg1=0xCAFEBABE,
        arg2=-1,
        table_sign=-0x8000,
        entries=[0x0101, 0x0202, 0x0303, 0x0404, 0x0505, 0x0606, 0x0707,
                 0x0808, 0x0101],
        bonus=0x7FFFFFFF,
        lookup_result=0x80000000,
    ))
    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    runner = WeightRunner()
    passed = 0
    for case in cases:
        orig = runner.run(orig_code, case)
        cand = runner.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)

        # Coverage sanity checks on the original trace.
        names = [name for name, _args in orig["call_log"]]
        inactive = (
            (case.get("flags", 0x0234) & 0x0FFF) == 0
            and case.get("byte43", 0) == 0
        )
        table_path = case.get("arg2", 0) < 0
        if inactive:
            if names:
                print(f"  [FAIL] {case['name']}: inactive gate made calls")
                raise SystemExit(1)
        elif table_path:
            if names.count("script_vm_func_002b66ec") != 1:
                print(f"  [FAIL] {case['name']}: expected one table lookup")
                raise SystemExit(1)
            if "camp_func_002a89e4" in names:
                print(f"  [FAIL] {case['name']}: unexpected object lookup")
                raise SystemExit(1)
        elif not case.get("object_null", False):
            if names.count("camp_func_002a89e4") != 1:
                print(f"  [FAIL] {case['name']}: expected one object lookup")
                raise SystemExit(1)
            if "script_vm_func_002b66ec" in names:
                print(f"  [FAIL] {case['name']}: unexpected table lookup")
                raise SystemExit(1)

        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing camp_func_00262498 (0x00262498)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("low_flag_mask",
         "constexpr u32 kLowFlagsMask = 0x0FFF;",
         "constexpr u32 kLowFlagsMask = 0x0FFE;"),
        ("special_low_flags",
         "constexpr u32 kSpecialLowFlags = 0x0FA0;",
         "constexpr u32 kSpecialLowFlags = 0x0FA1;"),
        ("record_kind",
         "constexpr u32 kRecordKindValue = 0x14;",
         "constexpr u32 kRecordKindValue = 0x15;"),
        ("selection_add",
         "constexpr u32 kSelectAddTwo = 6;",
         "constexpr u32 kSelectAddTwo = 7;"),
        ("object_word_offset",
         "constexpr u32 kObjectWordsOffset = 0x34;",
         "constexpr u32 kObjectWordsOffset = 0x30;"),
        ("entry_count",
         "constexpr u32 kEntryCount = 9;",
         "constexpr u32 kEntryCount = 8;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = WeightRunner().run(orig_code, case)
            bad = WeightRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
