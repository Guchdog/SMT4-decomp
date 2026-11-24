#!/usr/bin/env python3
"""Differential test for engine_func_00159a44 (0x00159a44, 896 B).

Compiles src/engine/leaf_batch45_b.cpp, extracts the engine_func_00159a44 body,
resolves its five direct calls to deterministic stubs at the original targets,
and runs the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn ARM machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log with every register argument, including the raw s0/s1
    bit patterns forwarded to the 0x2B9CF8 powf helper;
  * the 0x34-byte frame captured at the 0x00156208 submission, both raw bytes
    and the pointer-normalised frame argument in the call log;
  * self, params, selected table, table-global, context and buffer bytes;
  * any emulated write outside the private stack.

Coverage: mode 0/1 accepted and every other sign-extended byte rejected; null
buffer base and capacity; each float gate positive/negative/zero/-0.0/NaN/
negative-NaN/just-above-1.0; the 0.95 clamp boundary; the +0x20 selector 0/1/255;
s17 divisor zero and nonzero; sign-extended table quantisers (0, 1, 32767,
-32768, -1 through 16-bit truncation); default and explicit table pointers; and
all four cumulative buffer-capacity checks at one-below, exact and one-above.

Negative controls mutate the pow exponent factor, the 0.95 clamp constant, the
packet count, the default table address, the address encoding and the slot
stride; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_00159a44"

FUNC_ADDR = 0x00159A44
FUNC_SIZE = 896

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x2C4000
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00100000
TABLE_ADDR = 0x00600000
TABLE_SIZE = 0x00001000
SELF_ADDR = 0x00610000
SELF_SIZE = 0x00001000
PARAMS_ADDR = 0x00620000
PARAMS_SIZE = 0x00001000
BUFFER_ADDR = 0x00480000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

TABLE_GLOBAL = 0x00473278
CONTEXT_GLOBAL = 0x004E6F08

FRAME_SIZE = 0x34

STUB_2B9CF8 = 0x002B9CF8
STUB_2C3B48 = 0x002C3B48
STUB_2A4DB4 = 0x002A4DB4
STUB_2BB7B0 = 0x002BB7B0
STUB_156208 = 0x00156208

STUB_NAMES = {
    STUB_2B9CF8: "camp_func_002b9cf8",
    STUB_2C3B48: "engine_func_002c3b48",
    STUB_2A4DB4: "func_002a4db4",
    STUB_2BB7B0: "engine_func_002bb7b0",
    STUB_156208: "func_00156208",
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

POW_RETURN_BITS = struct.unpack("<I", struct.pack("<f", 0.5))[0]
CALL_RETURN = 0x600DF00D


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def signed32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def signed16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def quantise_1000(value: int) -> int:
    product = (0xD6853CC1 * ((value * 1000) & 0xFFFFFFFF)) & 0xFFFFFFFFFFFFFFFF
    result = (product >> 32) >> 12
    if signed32(result) < 1:
        result = 1
    return result & 0xFFFFFFFF


def divide_160(value: int) -> int:
    product = 0xCCCCCCCD * (value & 0xFFFFFFFF)
    return ((product >> 32) >> 7) & 0xFFFFFFFF


def encode_address(address: int) -> int:
    address &= 0xFFFFFFFF
    return (((address + 0x0C000000) & 0xFFFFFFFF) >> 16) | (
        (address << 16) & 0xFFFFFFFF
    )


def default_table_values() -> dict:
    return {"table0": 640, "table1": 800, "table2": 1120}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "00159a44" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_00159a44 not found in {obj_file}: {sorted(functions)}"
        )

    code_raw, relocations = candidate
    code = bytearray(code_raw)
    for rel in relocations:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for "
                f"{rel.symbol_name}"
            )
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name.lower():
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
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


# --------------------------------------------------------------------- fixtures
def build_self(case: dict) -> bytes:
    page = bytearray(SELF_SIZE)
    page[0x0D] = case.get("mode", 0) & 0xFF
    struct.pack_into("<I", page, 0x00, case.get("base", BUFFER_ADDR) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x08, case.get("capacity", 0x10000) & 0xFFFFFFFF)
    for offset in (0x00, 0x04, 0x08, 0x0C):
        page[0x20 + offset] = 0xC0 | offset
    return bytes(page)


def build_params(case: dict) -> bytes:
    page = bytearray(PARAMS_SIZE)
    struct.pack_into("<I", page, 0x00, case.get("param0", 5) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x04, case.get("param4", 1000) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x08, case.get("param8", 5) & 0xFFFFFFFF)
    struct.pack_into(
        "<I", page, 0x0C, case.get("bits_0c", f32_bits(0.5)) & 0xFFFFFFFF
    )
    struct.pack_into(
        "<I", page, 0x10, case.get("bits_10", f32_bits(0.5)) & 0xFFFFFFFF
    )
    struct.pack_into("<I", page, 0x14, case.get("table", 0) & 0xFFFFFFFF)
    struct.pack_into(
        "<I", page, 0x18, case.get("bits_18", f32_bits(0.5)) & 0xFFFFFFFF
    )
    struct.pack_into(
        "<I", page, 0x1C, case.get("bits_1c", f32_bits(0.5)) & 0xFFFFFFFF
    )
    page[0x20] = case.get("selector", 0) & 0xFF
    return bytes(page)


def build_table(case: dict) -> bytes:
    page = bytearray(TABLE_SIZE)
    values = default_table_values()
    values.update(case.get("table_values", {}))
    for index, key in enumerate(("table0", "table1", "table2")):
        struct.pack_into("<I", page, index * 4, values[key] & 0xFFFFFFFF)
    return bytes(page)


def build_table_global(case: dict) -> bytes:
    values = default_table_values()
    values.update(case.get("global_values", {}))
    page = bytearray(16)
    for index, key in enumerate(("table0", "table1", "table2")):
        struct.pack_into("<I", page, index * 4, values[key] & 0xFFFFFFFF)
    return bytes(page)


def expected_offsets(case: dict) -> tuple[int, int, int, int]:
    slot_a = quantise_1000(case.get("param0", 5))
    slot_b = quantise_1000(case.get("param8", 5))
    values = default_table_values()
    values.update(case.get("table_values", {}))
    if case.get("table", 0) == 0:
        values.update(case.get("global_values", {}))
    divide0 = divide_160(values["table0"]) & 0xFFFF
    divide1 = divide_160(values["table1"]) & 0xFFFF
    offset0 = (slot_a * 0x500) & 0xFFFFFFFF
    offset1 = (offset0 + slot_b * 0x500) & 0xFFFFFFFF
    offset2 = (offset1 + (((signed16(divide0) * 5) & 0xFFFFFFFF) << 8)) & 0xFFFFFFFF
    offset3 = (offset2 + (((signed16(divide1) * 5) & 0xFFFFFFFF) << 8)) & 0xFFFFFFFF
    return offset0, offset1, offset2, offset3


class Runner:
    """One Unicorn ARM machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Enable the VFP coprocessor (CP10/CP11) used by the prologue and maths.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(PARAMS_ADDR, PARAMS_SIZE)
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
        self.frame_bytes = b""
        self.case: dict = {}

    def _stack_rebased(self, args) -> tuple:
        normalised = []
        for arg in args:
            if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                normalised.append("<stack>")
            else:
                normalised.append(arg)
        return tuple(normalised)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2B9CF8:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc.reg_read(arm.UC_ARM_REG_S1)
            self.call_log.append(
                ("camp_func_002b9cf8", (s0, s1))
            )
            uc.reg_write(arm.UC_ARM_REG_S0, POW_RETURN_BITS)
        elif address == STUB_2C3B48:
            self.call_log.append(("engine_func_002c3b48", (r0, r1)))
        elif address == STUB_2A4DB4:
            self.call_log.append(("func_002a4db4", (r0, r1)))
        elif address == STUB_2BB7B0:
            context = struct.unpack(
                "<I", uc.mem_read(CONTEXT_GLOBAL, 4)
            )[0]
            self.call_log.append(("engine_func_002bb7b0", (context,)))
            uc.reg_write(arm.UC_ARM_REG_R0, context)
        elif address == STUB_156208:
            frame = bytes(uc.mem_read(r2, FRAME_SIZE))
            self.frame_bytes = frame
            self.call_log.append(
                ("func_00156208", self._stack_rebased((r0, r1, r2)))
            )
            uc.reg_write(arm.UC_ARM_REG_R0, CALL_RETURN)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.frame_bytes = b""
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SELF_ADDR, build_self(case))
        self.uc.mem_write(PARAMS_ADDR, build_params(case))
        self.uc.mem_write(TABLE_ADDR, build_table(case))
        self.uc.mem_write(DATA_ADDR + (TABLE_GLOBAL - DATA_ADDR), build_table_global(case))
        self.uc.mem_write(
            DATA_ADDR + (CONTEXT_GLOBAL - DATA_ADDR),
            struct.pack("<I", case.get("context", 0x55AA1234) & 0xFFFFFFFF),
        )
        self.uc.mem_write(BUFFER_ADDR, bytes(range(0x100)))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, PARAMS_ADDR)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "frame": self.frame_bytes,
            "fixtures": {
                "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
                "params": bytes(self.uc.mem_read(PARAMS_ADDR, PARAMS_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "table_global": bytes(self.uc.mem_read(TABLE_GLOBAL, 16)),
                "context": bytes(self.uc.mem_read(CONTEXT_GLOBAL, 4)),
                "buffer": bytes(self.uc.mem_read(BUFFER_ADDR, 0x100)),
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
    if orig["frame"] != cand["frame"]:
        problems.append(
            f"frame:\n    orig={orig['frame']!r}\n    cand={cand['frame']!r}"
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} differs")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "mode": 0,
        "base": BUFFER_ADDR,
        "capacity": 0x10000,
        "param0": 5,
        "param4": 1000,
        "param8": 5,
        "bits_0c": f32_bits(0.5),
        "bits_10": f32_bits(0.5),
        "bits_18": f32_bits(0.5),
        "bits_1c": f32_bits(0.5),
        "table": 0,
        "selector": 0,
        "context": 0x55AA1234,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- mode gate: 0 and 1 proceed, every other sign-extended byte returns 0.
    for mode in (0x00, 0x01, 0x02, 0x7F, 0x80, 0xFF):
        cases.append(base_case(f"mode 0x{mode:02x}", mode=mode))

    # --- null buffer base / capacity.
    cases.append(base_case("null buffer base", base=0))
    cases.append(base_case("null capacity", capacity=0))
    cases.append(base_case("null base and capacity", base=0, capacity=0))

    # --- each float gate independently, with all other fields valid.
    gate_offsets = {
        0x0C: "bits_0c",
        0x10: "bits_10",
        0x18: "bits_18",
        0x1C: "bits_1c",
    }
    gate_values = {
        "negative": f32_bits(-1.0),
        "negative small": f32_bits(-1e-30),
        "negative zero": 0x80000000,
        "zero": 0x00000000,
        "one": f32_bits(1.0),
        "just above one": f32_bits(1.0) + 1,
        "positive nan": 0x7FC00000,
        "negative nan": 0xFFC00000,
        "infinity": f32_bits(float("inf")),
    }
    for offset, key in gate_offsets.items():
        for label, bits in gate_values.items():
            cases.append(
                base_case(f"gate +0x{offset:02X} {label}", **{key: bits})
            )

    # --- 0.95 clamp boundary on +0x10, plus the selector paths.
    for bits, label in (
        (f32_bits(0.95) - 1, "just below 0.95"),
        (f32_bits(0.95), "exactly 0.95"),
        (f32_bits(0.95) + 1, "just above 0.95"),
        (f32_bits(1.0), "one"),
    ):
        cases.append(base_case(f"clamp {label}", bits_10=bits))
        cases.append(base_case(f"clamp {label} selector 1", bits_10=bits,
                               selector=1))
    for selector in (0x00, 0x01, 0x02, 0x7F, 0xFF):
        cases.append(base_case(f"selector 0x{selector:02x}", selector=selector))

    # --- s17 divisor: zero, small, and the full unsigned range.
    for param4 in (0, 1, 999, 1000, 0x7FFFFFFF, 0xFFFFFFFF):
        cases.append(base_case(f"param4 0x{param4:08x}", param4=param4))

    # --- slot quantisers: zero clamps up, and large signed results truncate.
    for param0, param8 in (
        (0, 0),
        (5, 5),
        (10, 10),
        (0xFFFFFFFF, 0xFFFFFFFF),
        (0x80000000, 0x7FFFFFFF),
        (123, 456),
    ):
        cases.append(
            base_case(f"param0/8 0x{param0:08x}/0x{param8:08x}",
                      param0=param0, param8=param8)
        )

    # --- table quantiser -> sign-extended loop samples.
    table_vectors = [
        # (table0, table1, table2, label)
        (0, 0, 0, "zero"),
        (160, 160, 160, "one"),
        (159, 161, 319, "below/above one"),
        (0xFFFF, 0x8000, 0x7FFF, "12-bit-ish mix"),
        ((0x7FFF * 160) & 0xFFFFFFFF, ((0x8000 * 160) & 0xFFFFFFFF),
         ((0xFFFF * 160) & 0xFFFFFFFF), "16-bit boundaries"),
        (0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, "all ones"),
        (0x7FFFFFFF, 0x80000000, 0x40000000, "32-bit extremes"),
    ]
    for table0, table1, table2, label in table_vectors:
        cases.append(
            base_case(
                f"table values {label}",
                table_values={
                    "table0": table0,
                    "table1": table1,
                    "table2": table2,
                },
            )
        )

    # --- explicit table pointer vs the default global table.
    for table in (0, TABLE_ADDR):
        cases.append(
            base_case(
                f"table pointer 0x{table:08x}",
                table=table,
                table_values={
                    "table0": 320,
                    "table1": 480,
                    "table2": 640,
                },
                global_values={
                    "table0": 640,
                    "table1": 800,
                    "table2": 1120,
                },
            )
        )

    # --- capacity checks at every cumulative offset: below, exact, above.
    boundary_case = base_case("capacity boundaries")
    offsets = expected_offsets(boundary_case)
    for index, offset in enumerate(offsets):
        for delta, label in ((-1, "below"), (0, "exact"), (1, "above")):
            capacity = (offset + delta) & 0xFFFFFFFF
            cases.append(
                base_case(
                    f"capacity 0x{capacity:08x} ({label} offset{index})",
                    capacity=capacity,
                )
            )
    cases.append(base_case("capacity all offsets", capacity=offsets[-1] + 1))
    cases.append(base_case("capacity max", capacity=0xFFFFFFFF))

    # --- encoded-address inputs across 32-bit base values.
    for base in (0x00000001, 0x00010000, 0x12345678, 0x7FFFFFFF, 0xFFFFFFF0,
                 0xFFFFFFFF):
        cases.append(
            base_case(f"buffer base 0x{base:08x}", base=base,
                      capacity=0xFFFFFFFF)
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
    print(f"  {passed}/{len(cases)} cases passed")
    return passed


def main() -> None:
    print("Testing engine_func_00159a44 (0x00159a44)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = [
        ("pow_exponent_factor", "const f32 exponent_factor = -3.0f;",
         "const f32 exponent_factor = -2.0f;"),
        ("ratio_clamp", "const f32 ratio_max = 0.9499999880790710f;",
         "const f32 ratio_max = 0.9000000000000000f;"),
        ("packet_count", "frame.count = 6;", "frame.count = 5;"),
        ("default_table", "0x00473278u", "0x0047327Cu"),
        ("address_encoding", "(address + 0x0C000000u)",
         "(address + 0x0C000001u)"),
        ("slot_stride", "slot_a * 0x500u", "slot_a * 0x501u"),
    ]
    for name, old, new in controls:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
