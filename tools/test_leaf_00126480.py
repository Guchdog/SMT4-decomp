#!/usr/bin/env python3
"""Differential test for engine_func_00126480 (0x00126480) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the readable
engine_func_00126480 body, resolves its five direct calls to deterministic
stubs, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and d8-d10;
  * the ordered call log with every register argument, the architected stack
    words, the manager virtual target read through [manager+0x184], and the
    0x0014BEF8 activation performed by the 0x002BCDF8 contract;
  * the float target bits passed to 0x002BCD94;
  * full observable manager, stream-slot, voice, and virtual-dispatch pages;
  * any emulated write outside the private stack.

Coverage: null/all-occupied/free-slot scans over every index, each of the three
manager gates false and true, allocation status low byte 0/non-zero and
0x100 masking, null and non-null allocated voice, level 0 plus the
64-bias/0x40000000 bit-clamp boundaries, and verbatim fade bit patterns.
Negative controls mutate the slot count, level step, clamp threshold, registry
offset, allocation mask, and the conditional return.
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
OUT_DIR = ROOT / "build/test_leaf_00126480"

FUNC_ADDR = 0x00126480
FUNC_SIZE = 424

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x300000

MANAGER_ADDR = 0x004E0000
MANAGER_SIZE = 0x00004000
MANAGER_BASE = 0x004E1F68
MANAGER_FIELD_004 = MANAGER_BASE + 0x0004
MANAGER_REGISTRY_PTR = MANAGER_BASE + 0x0184   # passed to 0x002BCDF8
MANAGER_ACTIVE_STREAM = MANAGER_BASE + 0x1204  # SoundSystem.field_1204

STREAM_ADDR = 0x00700000
STREAM_SIZE = 0x00001000
VOICE_ADDR = 0x00710000
VOICE_SIZE = 0x00001000
VTABLE_ADDR = 0x00720000
VTABLE_SIZE = 0x00001000
VTABLE_OBJECT = VTABLE_ADDR + 0x100
VTABLE_TARGET_A = VTABLE_ADDR + 0x200
VTABLE_TARGET_B = VTABLE_ADDR + 0x300

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets.  Stubs are placed at the same addresses so the
# original bytes and the relocated candidate resolve to the same code.
STUB_2BF85C = 0x002BF85C
STUB_141940 = 0x00141940
STUB_2C1F44 = 0x002C1F44
STUB_2BCDF8 = 0x002BCDF8
STUB_2BCD94 = 0x002BCD94
STUB_14BEF8 = 0x0014BEF8

STUB_NAMES = {
    STUB_2BF85C: "engine_func_002bf85c",
    STUB_141940: "engine_func_00141940",
    STUB_2C1F44: "func_002c1f44",
    STUB_2BCDF8: "func_002bcdf8",
    STUB_2BCD94: "func_002bcd94",
    STUB_14BEF8: "func_0014bef8",
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
FP_CALLEE_SAVED = {
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
    "d10": arm.UC_ARM_REG_D10,
}
FP_CALLEE_SAVED_START = {
    "d8": 0x1111222233334444,
    "d9": 0x5555666677778888,
    "d10": 0x9999AAAABBBBCCCC,
}

# A voice allocated by the emulated manager virtual lives at the base of the
# voice page; the pre-existing occupied slots use distinct sentinels.
ALLOCATED_VOICE = VOICE_ADDR
OCCUPIED_VOICE_BASE = VOICE_ADDR + 0x200


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00126480" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_00126480 not found in {obj_file}: {sorted(funcs)}"
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
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
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
def build_manager(case: dict) -> bytes:
    page = bytearray([0x5A]) * MANAGER_SIZE
    struct.pack_into("<I", page, MANAGER_FIELD_004 - MANAGER_ADDR,
                     case.get("state_word", 1) & 0xFFFFFFFF)
    struct.pack_into("<I", page, MANAGER_REGISTRY_PTR - MANAGER_ADDR,
                     VTABLE_OBJECT)
    struct.pack_into("<I", page, MANAGER_ACTIVE_STREAM - MANAGER_ADDR,
                     case.get("active_stream", STREAM_ADDR) & 0xFFFFFFFF)
    return bytes(page)


def build_stream(case: dict) -> bytes:
    page = bytearray([0x3C]) * STREAM_SIZE
    occupied = set(case.get("occupied", ()))
    for index in range(8):
        if index in occupied:
            pointer = OCCUPIED_VOICE_BASE + index * 0x40
        else:
            pointer = 0
        struct.pack_into("<I", page, 0x20 + index * 4, pointer)
    return bytes(page)


def build_voice(case: dict) -> bytes:
    page = bytearray([0x6D]) * VOICE_SIZE
    # The reading path clears +0x85 before the helper can set it.
    page[0x85] = 0
    struct.pack_into("<I", page, 0xB4, case.get("field_b4", 0x11111111))
    struct.pack_into("<I", page, 0xB8, case.get("field_b8", 0x22222222))
    return bytes(page)


def build_vtable(case: dict) -> bytes:
    page = bytearray([0x7E]) * VTABLE_SIZE
    struct.pack_into(
        "<I", page, VTABLE_OBJECT - VTABLE_ADDR + 8,
        case.get("vtable_target", VTABLE_TARGET_A),
    )
    return bytes(page)


def float_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


class VoiceRunner:
    """One Unicorn machine with deterministic manager/gate/voice stubs."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The original pushes d8-d10 and uses VFP arithmetic; enable CP10/CP11
        # access and the VFP unit before mapping/execution.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(MANAGER_ADDR, MANAGER_SIZE)
        self.uc.mem_map(STREAM_ADDR, STREAM_SIZE)
        self.uc.mem_map(VOICE_ADDR, VOICE_SIZE)
        self.uc.mem_map(VTABLE_ADDR, VTABLE_SIZE)
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
    def _read_u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def _write_u32(self, address: int, value: int) -> None:
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def _log(self, name: str, *args) -> None:
        self.call_log.append((name, args))

    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        raw = self.uc.mem_read(sp, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (size * 8)) - 1)))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2BF85C:
            # Contract of 0x002BF85C: return ([r0 + 4] != 0) ? 1 : 0.
            self._log(STUB_NAMES[address], r0, *self._stack_words(0))
            state = self._read_u32(r0 + 4)
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if state else 0)
        elif address == STUB_141940:
            self._log(STUB_NAMES[address], r0, r1, *self._stack_words(0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("gate2", 1) & 0xFFFFFFFF)
        elif address == STUB_2C1F44:
            self._log(STUB_NAMES[address], r0, *self._stack_words(0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("gate3", 1) & 0xFFFFFFFF)
        elif address == STUB_2BCDF8:
            self._log(STUB_NAMES[address], r0, r1, r2, r3,
                      *self._stack_words(0))
            object_address = self._read_u32(r0)
            target = (
                self._read_u32(object_address + 8) if object_address else 0
            )
            self._log(f"indirect@0x{target:08x}", object_address, r1, r2, r3)

            allocated = self.case.get("alloc_pointer", ALLOCATED_VOICE) & 0xFFFFFFFF
            self._write_u32(r1, allocated)
            result = self.case.get("alloc_result", 0) & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, result)
            if (result & 0xFF) == 0:
                voice = self._read_u32(r1)
                if voice:
                    # 0x0014BEF8 sets the enable byte at voice + 0x85.
                    uc.mem_write(voice + 0x85, b"\x01")
                    self._log(STUB_NAMES[STUB_14BEF8], voice,
                              *self._stack_words(0))
        elif address == STUB_2BCD94:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self._log(STUB_NAMES[address], r0, r1, s0 & 0xFFFFFFFF,
                      *self._stack_words(0))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(MANAGER_ADDR, build_manager(case))
        self.uc.mem_write(STREAM_ADDR, build_stream(case))
        self.uc.mem_write(VOICE_ADDR, build_voice(case))
        self.uc.mem_write(VTABLE_ADDR, build_vtable(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("object", 0x00600000))
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("level", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case.get("target", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_S0,
                          case.get("fade_a", float_bits(0.25)) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_S1,
                          case.get("fade_b", float_bits(0.75)) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in FP_CALLEE_SAVED_START.items():
            self.uc.reg_write(FP_CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not in_stack:
                unexpected_writes.append((address, size, value))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "fp_callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in FP_CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "manager": bytes(self.uc.mem_read(MANAGER_ADDR, MANAGER_SIZE)),
                "stream": bytes(self.uc.mem_read(STREAM_ADDR, STREAM_SIZE)),
                "voice": bytes(self.uc.mem_read(VOICE_ADDR, VOICE_SIZE)),
                "vtable": bytes(self.uc.mem_read(VTABLE_ADDR, VTABLE_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def _compare_call_logs(orig_log: list, cand_log: list) -> list[str]:
    problems = []
    if len(orig_log) != len(cand_log):
        return [
            "call log length:\n    orig="
            + repr(orig_log)
            + "\n    cand="
            + repr(cand_log)
        ]
    for index, ((orig_name, orig_args), (cand_name, cand_args)) in enumerate(
        zip(orig_log, cand_log)
    ):
        if orig_name != cand_name or len(orig_args) != len(cand_args):
            problems.append(
                f"call {index}:\n    orig={(orig_name, orig_args)!r}"
                f"\n    cand={(cand_name, cand_args)!r}"
            )
            continue
        if orig_args != cand_args:
            problems.append(
                f"call {index}:\n    orig={(orig_name, orig_args)!r}"
                f"\n    cand={(cand_name, cand_args)!r}"
            )
    return problems


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "fp_callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    problems.extend(_compare_call_logs(orig["call_log"], cand["call_log"]))
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            problems.append(f"fixture {key} was modified differently")
    if sorted(orig["unexpected_writes"]) != sorted(cand["unexpected_writes"]):
        problems.append(
            "unexpected writes:\n    orig="
            f"{orig['unexpected_writes']}\n    cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "object": 0x00600000,
        "level": 64,
        "target": 0,
        "fade_a": float_bits(0.25),
        "fade_b": float_bits(0.75),
        "state_word": 1,
        "gate2": 1,
        "gate3": 1,
        "alloc_result": 0,
        "alloc_pointer": ALLOCATED_VOICE,
        "vtable_target": VTABLE_TARGET_A,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- active stream pointer and the eight-entry free-slot scan
    cases.append(base_case("active stream null", active_stream=0))
    cases.append(base_case("all eight slots occupied",
                           occupied=set(range(8))))
    for free_index in range(8):
        cases.append(base_case(
            f"slot {free_index} is the first free entry",
            occupied=set(range(8)) - {free_index},
        ))
    cases.append(base_case("only slot 7 free", occupied=set(range(7))))

    # --- three manager gates: false and true at each step
    cases.append(base_case("first gate false", state_word=0))
    cases.append(base_case("first gate true word 0x80000000",
                           state_word=0x80000000))
    cases.append(base_case("second gate false", gate2=0))
    cases.append(base_case("second gate true 0xFFFFFFFF", gate2=0xFFFFFFFF))
    cases.append(base_case("third gate false", gate3=0))
    cases.append(base_case("third gate true 0x80000000", gate3=0x80000000))

    # --- allocation status low byte and the 0x100 mask
    for result in (0x00, 0x01, 0x7F, 0x80, 0xFF, 0x100, 0x1FF):
        cases.append(base_case(f"allocation result 0x{result:03x}",
                               alloc_result=result))
    cases.append(base_case("allocated voice pointer null", alloc_pointer=0))
    cases.append(base_case("allocated voice pointer null, status 0x7F",
                           alloc_pointer=0, alloc_result=0x7F))
    cases.append(base_case("allocated voice pointer null, status 0x100",
                           alloc_pointer=0, alloc_result=0x100))

    # --- level conversion: zero, bias boundary, clamp boundary, wrap values
    for level in (0, 1, 2, 63, 64, 65, 127, 128, 129, 255, 0xFFFF,
                  0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"level 0x{level:08x}", level=level))

    # --- target mode and fade endpoints are forwarded verbatim
    for target in (0, 1, 7, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(f"target 0x{target:08x}", target=target))
    for fade_a, fade_b in (
        (0x00000000, 0x80000000),
        (0x3F800000, 0xBF800000),
        (0x7F800000, 0xFF800000),
        (0x7FC00000, 0x7F800001),
        (0x00000001, 0x80000001),
    ):
        cases.append(base_case(
            f"fade bits 0x{fade_a:08x}/0x{fade_b:08x}",
            fade_a=fade_a, fade_b=fade_b,
        ))

    # --- manager virtual dispatch target variations
    cases.append(base_case("vtable target A", vtable_target=VTABLE_TARGET_A))
    cases.append(base_case("vtable target B", vtable_target=VTABLE_TARGET_B))

    # --- gate combinations that still perform the full voice update
    cases.append(base_case("full path slot 6 status 0x80",
                           occupied=set(range(6)), alloc_result=0x80))
    cases.append(base_case("full path slot 2 level 128",
                           occupied={0, 1, 3, 4, 5, 6, 7}, level=128))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = VoiceRunner().run(orig_code, case)
        cand = VoiceRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing engine_func_00126480 (0x00126480)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("slot_count", "index < kVoiceSlotCount;",
         "index < kVoiceSlotCount - 1;"),
        ("level_step", "constexpr u32 kLevelStepBits = 0x3C810204;",
         "constexpr u32 kLevelStepBits = 0x3C810205;"),
        ("clamp_threshold", "constexpr u32 kClampBits = 0x40000000;",
         "constexpr u32 kClampBits = 0x3F800000;"),
        ("registry_offset", "constexpr u32 kRegistryOffset = 0x0184;",
         "constexpr u32 kRegistryOffset = 0x0180;"),
        ("allocation_mask",
         "constexpr u32 kAllocationSuccessMask = 0xFF;",
         "constexpr u32 kAllocationSuccessMask = 0x0F;"),
        ("conditional_return", "return allocated ? slot : -1;",
         "return allocated ? -1 : -1;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = VoiceRunner().run(orig_code, case)
            try:
                bad = VoiceRunner().run(mutant_code, case)
            except Exception:
                # A mutant that faults where the original does not is a
                # detected behavioural difference.
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
