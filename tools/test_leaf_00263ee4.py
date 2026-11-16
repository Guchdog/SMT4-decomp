#!/usr/bin/env python3
"""Differential test for script_vm_func_00263ee4 (0x00263EE4).

The function has no branches: every path is the single straight-line sequence
of field stores, two helper calls and the slot stores.  The tests therefore
cover the complete parameter surface instead of branch arms:

  * four core-register arguments, all fifteen stack words and all seven VFP
    arguments s0..s6;
  * the pre-call global count (including 0xFFFFFFFF wrap-around), the first
    helper's return/index (0, small, 0x7F, 160 = work-record alias, -1,
    0x80000000) and the second helper's return (-1, 0x80000000, 0x7FFFFFFF);
  * helper rewrites of the global count between/before the calls, which prove
    the final increment re-reads memory while slot indexing keeps the old
    value;
  * every stored byte/halfword/word and every pointer field is fed a distinct
    value so a wrong offset, width or source argument changes memory;
  * float bit patterns including +0.0, -0.0, infinities, FLT_MAX, FLT_MIN,
    the smallest subnormal, quiet NaNs and signalling NaNs.

Compared outputs: return r0, continuation PC, final SP, callee-saved r4-r11,
callee-saved d8-d15, the ordered call log (all integer and VFP arguments of
both helpers), and the full table (0x00447xxx) and work/slot (0x004Axxxx)
regions.  Negative controls mutate the two strides, the store sources, the
constant fields, the pointer field and the final count increment; each mutant
must be detected.

The helpers are deterministic stubs: 0x0021C598 logs r0/r1/r2 and returns
case["ret1"]; 0x002526FC logs r0-r3 and s0-s3 and returns case["ret2"].
A case may ask either stub to overwrite the global count at 0x00447A2C before
returning.  Neither stub otherwise writes memory.  The real 0x0021C598 body is
unresolved (its own transcription is still raw ARM); 0x002526FC is likewise
exercised only through its return contract.
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
OUT_DIR = ROOT / "build/test_leaf_00263ee4"

FUNC_ADDR = 0x00263EE4
FUNC_SIZE = 408

COUNT_ADDR = 0x00447A2C

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and both helpers below 0x3F0000
LOW_ADDR = 0x00440000
LOW_SIZE = 0x00010000
HIGH_ADDR = 0x004A0000
HIGH_SIZE = 0x00020000  # slot table at +0x1264, work table at +0xFD64
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original helper addresses; the stubs live at the same addresses so the
# pinned original and the relocated candidate both reach them directly.
STUB_FIRST = 0x0021C598   # smt4::battle::Btl_StatusEffectCalc
STUB_SECOND = 0x002526FC  # script_vm_func_002526fc

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
VFP_CALLEE_SAVED = {f"d{i}": getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16)}
VFP_CALLEE_SAVED_START = {
    f"d{i}": (0x1111000000000000 * (i - 7)) | (0x0100000000000000 * (i - 7))
    for i in range(8, 16)
}

S_REGISTERS = [getattr(arm, f"UC_ARM_REG_S{i}") for i in range(7)]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00263ee4" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"script_vm_func_00263ee4 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        name = rel.symbol_name
        if "Btl_StatusEffectCalc" in name or "0021c598" in name:
            target = STUB_FIRST
        elif "002526fc" in name:
            target = STUB_SECOND
        else:
            raise RuntimeError(f"unexpected relocation symbol: {name}")
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} for {name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        if rel.relocation_type == 28:
            instruction = 0xEB000000 | (displacement & 0x00FFFFFF)
        else:
            instruction = 0xEA000000 | (displacement & 0x00FFFFFF)
        struct.pack_into("<I", code, rel.offset, instruction)
    return bytes(code)


def compile_candidate(source: Path = SOURCE,
                      obj_name: str = "leaf_batch41_c.o") -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / obj_name
    result = compile_tu_armv6k(source, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, f"mutant_{name}.o")


class EffectRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(unicorn.arm_const.UC_CPU_ARM_11MPCORE)
        # Enable the VFP coprocessor (CP10/CP11) before executing vpush/vmov.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(LOW_ADDR, LOW_SIZE)
        self.uc.mem_map(HIGH_ADDR, HIGH_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address, hook in (
            (STUB_FIRST, self._on_first),
            (STUB_SECOND, self._on_second),
        ):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)

        self.call_log: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _on_first(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        self.call_log.append(("Btl_StatusEffectCalc", r0, r1, r2))
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["ret1"] & 0xFFFFFFFF)
        if "count_after_first" in self.case:
            uc.mem_write(
                COUNT_ADDR,
                struct.pack("<I", self.case["count_after_first"] & 0xFFFFFFFF),
            )

    def _on_second(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        s0, s1, s2, s3 = (uc.reg_read(register) for register in S_REGISTERS[:4])
        self.call_log.append(
            ("script_vm_func_002526fc", r0, r1, r2, r3, s0, s1, s2, s3)
        )
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["ret2"] & 0xFFFFFFFF)
        if "count_after_second" in self.case:
            uc.mem_write(
                COUNT_ADDR,
                struct.pack("<I", self.case["count_after_second"] & 0xFFFFFFFF),
            )

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)

        # Pre-fill the observable regions with non-zero patterns so untouched
        # bytes are compared too and every real store is visible.
        low = bytearray(b"\x5A" * LOW_SIZE)
        struct.pack_into("<I", low, 0x447A2C - LOW_ADDR, case["count"] & 0xFFFFFFFF)
        self.uc.mem_write(LOW_ADDR, bytes(low))
        self.uc.mem_write(HIGH_ADDR, b"\xC3" * HIGH_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        sp = ENTRY_SP
        stack_words = list(case["stack"]) + [0xDEADBEEF]
        self.uc.mem_write(
            sp, b"".join(struct.pack("<I", word & 0xFFFFFFFF) for word in stack_words)
        )

        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["id"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["handle"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["kind"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["type"] & 0xFFFFFFFF)
        for index, register in enumerate(S_REGISTERS):
            self.uc.reg_write(register, case["floats"][index] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_CALLEE_SAVED_START.items():
            self.uc.reg_write(VFP_CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "vfp_callee_saved": {
                name: self.uc.reg_read(register)
                for name, register in VFP_CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "memory": {
                "low": bytes(self.uc.mem_read(LOW_ADDR, LOW_SIZE)),
                "high": bytes(self.uc.mem_read(HIGH_ADDR, HIGH_SIZE)),
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for region in ("low", "high"):
        left = orig["memory"][region]
        right = cand["memory"][region]
        if left != right:
            first = next(
                (index for index, (a, b) in enumerate(zip(left, right)) if a != b),
                None,
            )
            problems.append(
                f"memory {region} differs at offset {first:#x}: "
                f"orig={left[first]:#04x} cand={right[first]:#04x}"
            )
    return problems


def default_stack() -> list[int]:
    # Every low byte is distinct and differs from the pre-filled memory.
    return [0xA5A50000 | (index << 8) | (0x30 + index) for index in range(15)]


DEFAULT_FLOATS = [f32_bits(value) for value in (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0)]


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "count": 0,
        "id": 0x11223344,
        "handle": 0x55667788,
        "kind": 0x00710000,
        "type": 0x39,
        "stack": default_stack(),
        "floats": list(DEFAULT_FLOATS),
        "ret1": 0,
        "ret2": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline and record indices
    cases.append(base_case("baseline count 0"))
    for count in (1, 2, 7, 300, 0xFFFFFFFF):
        cases.append(base_case(f"count {count:#x}", count=count))
    cases.append(base_case("count 0xFFFFFFFF with wrapped slot",
                           count=0xFFFFFFFF, ret1=-1))

    # --- helper rewrites of the global count: the final increment must use
    # the value live after both calls, while slot indexing keeps the old one.
    cases.append(base_case("first helper advances count", count=2, ret1=1,
                           count_after_first=0x40))
    cases.append(base_case("second helper wraps count", count=0,
                           count_after_second=0xFFFFFFFF))
    cases.append(base_case("both helpers change count", count=5,
                           count_after_first=0x10, count_after_second=0x20))

    # --- first helper return: the slot index, including aliasing boundaries
    for ret1 in (1, 3, 0x7F, 160, -1, 0x80000000):
        cases.append(base_case(f"slot index {ret1:#x}", ret1=ret1))
    cases.append(base_case("slot index 160 aliases work record",
                           count=0, ret1=160))
    cases.append(base_case("slot index 160 with count 160",
                           count=160, ret1=160))

    # --- second helper return: stored as a full 32-bit word
    for ret2 in (-1, 0x7FFFFFFF, 0x80000000):
        cases.append(base_case(f"allocator return {ret2:#x}", ret2=ret2))

    # --- core-register argument boundaries
    cases.append(base_case("zero id/handle", id=0, handle=0))
    cases.append(base_case("all-ones id/handle", id=0xFFFFFFFF,
                           handle=0xFFFFFFFF))
    cases.append(base_case("zero kind pointer", kind=0))
    cases.append(base_case("type -1", type=0xFFFFFFFF))
    cases.append(base_case("type 0", type=0))

    # --- stack-word boundaries and byte truncation
    stack = default_stack()
    stack[0] = 0xFFFFFFFF
    stack[1] = 0
    stack[14] = 0
    cases.append(base_case("stack 0/1/14 boundaries", stack=stack))
    stack = default_stack()
    for index in range(2, 11):
        stack[index] = 0xFFFFFF00 | index
    cases.append(base_case("stack bytes 2..10 truncate", stack=stack))
    stack = default_stack()
    for index in range(15):
        stack[index] = 0xFFFFFFFF if index & 1 else 0
    cases.append(base_case("alternating stack words", stack=stack))

    # --- VFP argument boundaries, including NaN payload preservation
    cases.append(base_case("zero and negative zero", floats=[
        f32_bits(0.0), f32_bits(-0.0), f32_bits(0.0),
        f32_bits(-0.0), f32_bits(0.0), f32_bits(-0.0), f32_bits(0.0),
    ]))
    cases.append(base_case("infinities and extreme finites", floats=[
        0x7F800000,  # +inf
        0xFF800000,  # -inf
        0x7F7FFFFF,  # FLT_MAX
        0x00800000,  # FLT_MIN
        0x00000001,  # smallest subnormal
        0x80000001,  # negative smallest subnormal
        0x3F800000,  # 1.0
    ]))
    cases.append(base_case("quiet NaNs", floats=[
        0x7FC00000, 0xFFC00000, 0x7FC00001,
        0xFFC00001, 0x7FFFFFFF, 0xFFFFFFFF, 0x7FC12345,
    ]))
    cases.append(base_case("signalling NaNs", floats=[
        0x7F800001, 0xFF800001, 0x7F800002,
        0xFFBFFFFF, 0x7FA00000, 0xFFA00001, 0x7F800123,
    ]))

    return cases


def run_case(orig_code: bytes, cand_code: bytes, case: dict,
             label: str = "") -> None:
    orig = EffectRunner().run(orig_code, case)
    cand = EffectRunner().run(cand_code, case)
    problems = compare(orig, cand)
    if problems:
        print(f"  [FAIL] {label}{case['name']}")
        for problem in problems:
            print(f"    {problem}")
        raise SystemExit(1)
    print(f"  [PASS] {label}{case['name']}  ({len(orig['call_log'])} calls)")


def main() -> None:
    print("Testing script_vm_func_00263ee4 (0x00263ee4)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    for case in cases:
        run_case(orig_code, cand_code, case)

    print("\nNegative controls:")
    mutants = (
        ("work_stride", "constexpr u32 kWorkStride = 0x8C;",
         "constexpr u32 kWorkStride = 0x90;"),
        ("slot_stride", "constexpr u32 kSlotStride = 0x178;",
         "constexpr u32 kSlotStride = 0x174;"),
        ("constant_word", "work->field_24 = 1;", "work->field_24 = 2;"),
        ("float_six_source", "work->field_54 = f6;", "work->field_54 = f5;"),
        ("previous_byte_source",
         "previous->field_16D = static_cast<u8>(stack9);",
         "previous->field_16D = static_cast<u8>(stack8);"),
        ("second_call_stack14",
         "id, stack0, stack1, stack14, f0, f1, f2, f6);",
         "id, stack0, stack1, stack13, f0, f1, f2, f6);"),
        ("count_increment", "++Table()->count_04;",
         "Table()->count_04 += 2;"),
        ("stale_count", "++Table()->count_04;",
         "Table()->count_04 = old_count + 1;"),
        ("previous_uses_post_call_count",
         "SlotRecord* const previous = SlotAt(old_count);",
         "SlotRecord* const previous = SlotAt(Table()->count_04);"),
        ("zero_constant", "constexpr f32 kZero = 0.0f;",
         "constexpr f32 kZero = 1.0f;"),
        ("unset_constant", "slot->field_134 = kSlotUnset;",
         "slot->field_134 = 0;"),
        ("byte_source", "work->field_38 = static_cast<u8>(stack2);",
         "work->field_38 = static_cast<u8>(stack3);"),
    )
    probe_cases = [base_case("probe A"), base_case("probe B", count=3, ret1=1,
                                                   ret2=0xFFFFFFFF),
                   base_case("probe C", count=2, ret1=1,
                             count_after_first=0x40,
                             count_after_second=0x50)]
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in probe_cases:
            orig = EffectRunner().run(orig_code, case)
            bad = EffectRunner().run(mutant, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {len(cases)}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
