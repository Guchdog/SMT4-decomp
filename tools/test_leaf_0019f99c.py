#!/usr/bin/env python3
"""Differential test for engine_func_0019f99c (0x0019f99c) using Unicorn ARM.

The candidate in src/engine/leaf_batch41_c.cpp is compiled, its direct calls
are relocated to deterministic stubs placed at the original target addresses,
and both the pinned original (extracted/exefs/code.bin) and the candidate run
on identical fixtures in separate executions.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and d8-d15;
  * the ordered call log for all six direct helpers, including the exact raw
    bits of every floating-point argument and every argument-order register;
  * the complete 0x00400000..0x00500000 data fixture (both camera entries,
    the default triples at 0x004D4924/0x004D493C and the manager table);
  * any emulated write outside the private stack and the data fixture.

Coverage: both loop iterations (ARK aspect 5/3 then 4/3), both manager slots
(+0x80/+0x84), the constructor flag byte taken and not taken, selector byte
truncation, zero/negative-zero/denormal/max-finite/infinity/NaN header values,
and three different default-vector fixtures.  There are no indirect calls in
this function; every branch is a direct conditional or the two-entry loop.

Negative controls mutate the entry stride, one aspect-ratio literal, the
3600.0f scale, the constructor-flag branch, and the first manager slot; each
mutant must be detected by the same comparison.
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
OUT_DIR = ROOT / "build/test_leaf_0019f99c"

FUNC_ADDR = 0x0019F99C
FUNC_SIZE = 432

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every direct-call target
DATA_ADDR = 0x00400000
DATA_SIZE = 0x00100000  # covers 0x0044EA58 and the 0x004D49xx camera block
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Storage addresses read by the original literal pool.
DEFAULT_VECTOR_ADDR = 0x004D4924
EXTRA_DEFAULT_ADDR = 0x004D493C
HEADER_ADDR = 0x004D4948
ENTRY_ARRAY_ADDR = 0x004D494C
ENTRY_STRIDE = 0x544
ENTRY_COUNT = 2
MANAGER_GLOBAL = 0x0044EA58
MANAGER_OBJECT = 0x00490000
MANAGER_OBJECT_ALT = 0x00490400

# Original direct-call targets; deterministic stubs live at these addresses so
# both the original bytes and the relocated candidate resolve to them.
STUB_2C2210 = 0x002C2210
STUB_2C20A8 = 0x002C20A8
STUB_2B761C = 0x002B761C
STUB_2BC0B4 = 0x002BC0B4
STUB_2B7AA8 = 0x002B7AA8
STUB_2B7584 = 0x002B7584

STUB_NAMES = {
    STUB_2C2210: "engine_func_002c2210",
    STUB_2C20A8: "engine_func_002c20a8",
    STUB_2B761C: "ui_func_002b761c",
    STUB_2BC0B4: "engine_func_002bc0b4",
    STUB_2B7AA8: "ui_func_002b7aa8",
    STUB_2B7584: "func_002b7584",
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


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0019f99c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0019f99c not found in {obj_file}: {sorted(funcs)}"
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
        struct.pack_into(
            "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
        )
    return bytes(code), b""


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
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


def write_u32(page: bytearray, address: int, value: int) -> None:
    struct.pack_into("<I", page, address - DATA_ADDR, value & 0xFFFFFFFF)


def write_u8(page: bytearray, address: int, value: int) -> None:
    page[address - DATA_ADDR] = value & 0xFF


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)

    # Default triples consumed by the original `ldm`/`ldmib` sequences.
    for index, word in enumerate(case.get("defaults", (0x3F800000, 0xC0000000,
                                                       0x40400000))):
        write_u32(page, DEFAULT_VECTOR_ADDR + index * 4, word)
    write_u32(page, DEFAULT_VECTOR_ADDR + 12, 0x5A5A5A11)
    write_u32(page, DEFAULT_VECTOR_ADDR + 16, 0x5A5A5A22)
    write_u32(page, DEFAULT_VECTOR_ADDR + 20, 0x5A5A5A33)
    for index, word in enumerate(case.get("extra", (0x3E800000, 0xBF000000,
                                                    0x3F400000))):
        write_u32(page, EXTRA_DEFAULT_ADDR + index * 4, word)

    # The selector byte sees a non-zero sentinel before the function stores it.
    write_u8(page, HEADER_ADDR, 0x5A)
    write_u8(page, HEADER_ADDR + 1, 0xA5)
    write_u8(page, HEADER_ADDR + 2, 0x5A)
    write_u8(page, HEADER_ADDR + 3, 0xA5)

    # Camera entries: 0xCC shows every field the function fails to write.
    entry_bytes = ENTRY_STRIDE * ENTRY_COUNT
    start = ENTRY_ARRAY_ADDR - DATA_ADDR
    page[start : start + entry_bytes] = b"\xCC" * entry_bytes

    # Manager global and manager table object.
    manager_object = case.get("manager_object", MANAGER_OBJECT)
    write_u32(page, MANAGER_GLOBAL, 0x11111111)
    write_u32(page, MANAGER_GLOBAL + 4, manager_object)
    write_u32(page, manager_object + 0x80, 0xA0A08080)
    write_u32(page, manager_object + 0x84, 0xA0A08484)
    write_u32(page, manager_object + 0x88, 0x51515151)
    return bytes(page)


class CameraRunner:
    """One Unicorn machine with deterministic helpers at the ROM targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Unicorn's default CPU has no enabled VFP; select a VFP-capable model
        # and enable CP10/CP11 through CPACR plus FPEXC, as the target does at
        # boot.  The function's arithmetic and save/restore are VFP-heavy.
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_CORTEX_A15)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
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
        self.stub_serial = 0

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    @staticmethod
    def _rotl(value: int, count: int) -> int:
        mask = 0xFFFFFFFF
        count &= 31
        return ((value << count) | (value >> (32 - count))) & mask

    def _matrix_pattern(self, s0: int, s1: int, s2: int, s3: int) -> bytes:
        seed = (
            s0
            ^ self._rotl(s1, 5)
            ^ self._rotl(s2, 11)
            ^ self._rotl(s3, 17)
            ^ 0xA5A5A5A5
        ) & 0xFFFFFFFF
        words = [(seed + index * 0x9E3779B9) & 0xFFFFFFFF for index in range(16)]
        return struct.pack("<16I", *words)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        s0 = uc.reg_read(arm.UC_ARM_REG_S0)
        s1 = uc.reg_read(arm.UC_ARM_REG_S1)
        s2 = uc.reg_read(arm.UC_ARM_REG_S2)
        s3 = uc.reg_read(arm.UC_ARM_REG_S3)

        if address == STUB_2C2210:
            self._log(address, r0, r1)
            # The real constructor finishes with `strb r1,[r0]`; the caller
            # re-reads that byte to gate 0x002B7584.
            constructor_byte = self.case.get("constructor_byte")
            if constructor_byte is None:
                constructor_byte = r1 & 0xFF
            uc.mem_write(r0, struct.pack("<B", constructor_byte & 0xFF))
        elif address == STUB_2C20A8:
            self._log(address, r0, r1, r2, r3)
            # The caller must overwrite this word with the far-plane copy.
            uc.mem_write(r0 + 0x30, struct.pack("<I", 0xDEADBEEF))
        elif address == STUB_2B761C:
            self._log(address, r0, s0, s1, s2, s3)
            uc.mem_write(r0, self._matrix_pattern(s0, s1, s2, s3))
        elif address == STUB_2BC0B4:
            self._log(address, r0, r1)
            word = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            uc.mem_write(
                r0, struct.pack("<I", word ^ ((r1 * 0x11111111) & 0xFFFFFFFF))
            )
        elif address == STUB_2B7AA8:
            self._log(address, r0, r1)
            uc.mem_write(r0, bytes(uc.mem_read(r1, 0x40)))
        elif address == STUB_2B7584:
            self._log(address, r0, r1)
            source = bytes(uc.mem_read(r1, 0x40))
            output = bytearray(0x20)
            for index in range(8):
                word = struct.unpack_from("<I", source, index * 4)[0]
                struct.pack_into(
                    "<I", output, index * 4,
                    word ^ ((index + 1) * 0x01010101) & 0xFFFFFFFF,
                )
            uc.mem_write(r0, bytes(output))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.stub_serial = 0

        # Reset every region the function or a helper can observe.
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        self.uc.mem_write(FUNC_ADDR, code)
        # The same machine alternates original and candidate code at one
        # address; discard any translated block from the previous body.
        self.uc.ctl_flush_tb()

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("header", 0x12345678))
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("selector", 0x5A))
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for index, (name, reg) in enumerate(FLOAT_SAVED.items()):
            self.uc.reg_write(reg, 0x1122334455667788 + index)
        self.uc.reg_write(
            arm.UC_ARM_REG_S0, case.get("value_bits", f32_bits(1.0))
        )

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_data = DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_data and not in_stack:
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
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def first_data_difference(orig: bytes, cand: bytes) -> str:
    limit = min(len(orig), len(cand))
    for index in range(limit):
        if orig[index] != cand[index]:
            return (
                f"first difference at 0x{DATA_ADDR + index:08x}: "
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
    if orig["data"] != cand["data"]:
        problems.append("data fixture: " + first_data_difference(
            orig["data"], cand["data"]))
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "header": 0x12345678,
        "selector": 0x5A,
        "value_bits": f32_bits(1.0),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Two-entry loop, both ARK slots and both aspect ratios.
    cases.append(base_case("baseline entry pair"))

    # Value boundaries and IEEE-754 classes.
    for label, bits in (
        ("+0.0", 0x00000000),
        ("-0.0", 0x80000000),
        ("+1.0", f32_bits(1.0)),
        ("-1.0", f32_bits(-1.0)),
        ("3600.0", f32_bits(3600.0)),
        ("min denormal", 0x00000001),
        ("negative denormal", 0x80000001),
        ("max finite", 0x7F7FFFFF),
        ("negative max finite", 0xFF7FFFFF),
        ("+inf", 0x7F800000),
        ("-inf", 0xFF800000),
        ("quiet NaN", 0x7FC00000),
        ("signalling NaN", 0x7F800001),
        ("123.456", f32_bits(123.456)),
        ("-18.267", f32_bits(-18.267)),
    ):
        cases.append(base_case(f"value {label}", value_bits=bits))

    # Selector is stored as one byte; only the low eight bits are observable.
    for selector in (0x00, 0xA5, 0x100, 0x1FF, 0xFFFFFFFF):
        cases.append(base_case(f"selector 0x{selector:08x}", selector=selector))

    # Header pair (word + zero) and the manager slot per iteration.
    for header in (0x00000000, 0xFFFFFFFF, 0x7FFF8000, 0xDEADBEEF):
        cases.append(base_case(f"header 0x{header:08x}", header=header))
    cases.append(base_case("alternate manager object",
                           manager_object=MANAGER_OBJECT_ALT))

    # Constructor flag byte: real constructor leaves 1; the stub lets the test
    # exercise both the taken and skipped 0x002B7584 paths.
    cases.append(base_case("constructor flag zero", constructor_byte=0x00))
    cases.append(base_case("constructor flag 0x80", constructor_byte=0x80))
    cases.append(base_case("constructor flag 0xFF", constructor_byte=0xFF))

    # Default triples copied verbatim into entry+0x1C and passed to 0x002C20A8.
    cases.append(base_case("defaults zero", defaults=(0, 0, 0)))
    cases.append(base_case(
        "defaults negative/NaN",
        defaults=(0x80000000, 0x7FC00001, 0x3F800000),
    ))
    cases.append(base_case(
        "defaults pattern",
        defaults=(0x11111111, 0x22222222, 0x33333333),
        extra=(0x44444444, 0x55555555, 0x66666666),
    ))

    # Combined branch/loop stress.
    cases.append(base_case(
        "loop and branch stress",
        header=0xCAFEBABE,
        selector=0x80,
        value_bits=f32_bits(-3600.0),
        constructor_byte=0x7F,
        defaults=(0x00000000, 0xFFFFFFFF, 0x80000000),
    ))
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    runner = CameraRunner()
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
        entered_branch = names.count("func_002b7584")
        expected_branch = 2 if case.get("constructor_byte", 1) != 0 else 0
        if entered_branch != expected_branch:
            print(
                f"  [FAIL] {case['name']} branch coverage: "
                f"expected {expected_branch} 0x002B7584 calls, saw {entered_branch}"
            )
            raise SystemExit(1)
        if names.count("ui_func_002b761c") != 4:
            print(f"  [FAIL] {case['name']}: expected four matrix builds")
            raise SystemExit(1)

        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_0019f99c (0x0019f99c)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("entry_stride",
         "constexpr u32 kEntryStride = 0x544;",
         "constexpr u32 kEntryStride = 0x540;"),
        ("wide_aspect",
         "constexpr f32 kWideAspect = __builtin_bit_cast(f32, 0x3FD55555u);  // 5/3",
         "constexpr f32 kWideAspect = __builtin_bit_cast(f32, 0x3FD55554u);  // 5/3"),
        ("seconds_per_hour",
         "value * kSecondsPerHour",
         "value * (kSecondsPerHour * 0.5f)"),
        ("constructor_flag_branch",
         "if (camera[kConstructorFlagOffset] != 0) {",
         "if (false) {"),
        ("manager_first_slot",
         "constexpr u32 kManagerFirstSlot = 0x80;",
         "constexpr u32 kManagerFirstSlot = 0x88;"),
    ):
        mutant_code, _ = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = CameraRunner().run(orig_code, case)
            bad = CameraRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
