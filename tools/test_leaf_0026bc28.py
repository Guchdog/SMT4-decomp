#!/usr/bin/env python3
"""Differential test for camp_func_0026bc28 (0x0026BC28) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the camp_func_0026bc28 body,
resolves every direct call to a deterministic stub at the original target
address, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn ARM machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log, including every helper's slot pointer (normalised to
    a manager-page offset) and the two architected stack words of the four
    0x0029FAE8 layout calls;
  * the full 64 KiB camp-state page (holds the manager pointer), the full
    64 KiB manager page (count/mode words and the 24 sparse slot dwords), and
    the full 64 KiB camp-base page (24 signed slot bytes and the mode byte);
  * any emulated write outside the manager page, base page or private stack.

Coverage:
  * live-slot values -128/-1/0/1/127, all-negative, all-zero and all-positive
    lists so the non-negative count is 0, 12 and 24;
  * mode byte 0x00/0x01/0x03/0x04/0x0B (``< 0x0C`` branch), 0x0C exactly,
    0x0D/0x1F/0x80/0xFF (``>= 0x0C`` branch) and the +0x2C flag zero/non-zero;
  * signed-byte boundaries and the derived ceil(mode/4) column count;
  * zero and non-zero helper results for all four widget slots, forwarded to
    the ordered 0x0029EB58 / 0x0029EDFC calls;
  * a stub that rewrites the mode byte during a 0x0029FAE8 call to prove each
    later 0x0029FAE8 argument is re-read from memory after the previous call.
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
OUT_DIR = ROOT / "build/test_leaf_0026bc28"

FUNC_ADDR = 0x0026BC28
FUNC_SIZE = 688

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x0026BC28 and every helper target
STATE_ADDR = 0x0043D000
STATE_SIZE = 0x00010000  # globals page, incl. the 0x0043DCF0 pointer slot
BASE_ADDR = 0x00600000
BASE_SIZE = 0x00010000  # camp_func_002a8a08 result
MANAGER_ADDR = 0x00610000
MANAGER_SIZE = 0x00010000  # 0x0043DCF0 points here
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2A8A08 = 0x002A8A08
STUB_26BED8 = 0x0026BED8
STUB_29EBA8 = 0x0029EBA8
STUB_29F248 = 0x0029F248
STUB_29FAE8 = 0x0029FAE8
STUB_29EB58 = 0x0029EB58
STUB_29EDFC = 0x0029EDFC

# Declaration name emitted by the candidate -> original call target.
RELOC_TARGETS = {
    "camp_func_002a8a08": STUB_2A8A08,
    "camp_func_0026bed8": STUB_26BED8,
    "engine_func_0029eba8": STUB_29EBA8,
    "camp_func_0029f248": STUB_29F248,
    "camp_func_0029fae8": STUB_29FAE8,
    "camp_func_0029eb58": STUB_29EB58,
    "camp_func_0029edfc": STUB_29EDFC,
}
STUB_NAMES = {address: name for name, address in RELOC_TARGETS.items()}

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

# Camp-base page offsets recovered from the ARM body.
OFF_LIVE_SLOTS = 0x90F0
LIVE_SLOT_COUNT = 24
OFF_MODE_BYTE = 0x910B

# Manager-page offsets.
OFF_COUNT = 0x28
OFF_FLAG = 0x2C
OFF_MODE = 0x30
OFF_SPARSE_BASE = 0x738
SPARSE_STRIDE = 8

SLOT_A = 0x940
SLOT_B = 0xA08
SLOT_C = 0x9A4
SLOT_D = 0xA6C
SLOTS = (SLOT_A, SLOT_B, SLOT_C, SLOT_D)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0026bc28" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"camp_func_0026bc28 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        target = RELOC_TARGETS.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved relocation: {rel.symbol_name}")
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        if target & 3:
            raise RuntimeError(f"unaligned call target 0x{target:08x}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


# --------------------------------------------------------------------- fixtures
def build_state(case: dict) -> bytes:
    page = bytearray(STATE_SIZE)
    for offset in range(0, STATE_SIZE, 4):
        struct.pack_into("<I", page, offset, 0x51510000 | ((offset * 3) & 0xFFFF))
    struct.pack_into("<I", page, 0x0043DCF0 - STATE_ADDR, MANAGER_ADDR)
    return bytes(page)


def build_base(case: dict) -> bytes:
    page = bytearray(BASE_SIZE)
    for offset in range(0, BASE_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xB0B00000 | ((offset * 5) & 0xFFFF))
    slots = case.get("slots")
    if slots is None:
        slots = [(index * 5) - 40 for index in range(LIVE_SLOT_COUNT)]
    if len(slots) != LIVE_SLOT_COUNT:
        raise ValueError("slots must contain 24 entries")
    for index, value in enumerate(slots):
        page[OFF_LIVE_SLOTS + index] = value & 0xFF
    page[OFF_MODE_BYTE] = case.get("mode_byte", 0x05) & 0xFF
    return bytes(page)


def build_manager(case: dict) -> bytes:
    page = bytearray(MANAGER_SIZE)
    for offset in range(0, MANAGER_SIZE, 4):
        struct.pack_into("<I", page, offset, 0xC0C00000 | ((offset * 7) & 0xFFFF))
    struct.pack_into("<I", page, OFF_COUNT, case.get("count", 0x12345678))
    struct.pack_into("<I", page, OFF_FLAG, case.get("flag", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, OFF_MODE, case.get("mode_word", 0x87654321))
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
        self.uc.mem_map(BASE_ADDR, BASE_SIZE)
        self.uc.mem_map(MANAGER_ADDR, MANAGER_SIZE)
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
        self.fae8_index = 0

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _offset(value: int) -> int:
        return value - MANAGER_ADDR

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        case = self.case

        if address == STUB_2A8A08:
            # The getter ignores its argument and returns the camp base.
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, BASE_ADDR)
        elif address == STUB_26BED8:
            # Ignores the leftover r0 (original and candidate differ there).
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_29EBA8:
            offset = self._offset(r0)
            self._log(address, offset)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                case.get("engine_returns", {}).get(offset, 0xE0000000 | offset),
            )
        elif address == STUB_29F248:
            offset = self._offset(r0)
            self._log(address, offset)
            uc.reg_write(
                arm.UC_ARM_REG_R0,
                case.get("camp_returns", {}).get(offset, 0xC0000000 | offset),
            )
        elif address == STUB_29FAE8:
            offset = self._offset(r0)
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            sp0, sp1 = struct.unpack("<II", uc.mem_read(sp, 8))
            self._log(address, offset, r1, r2, r3, sp0, sp1)
            mutation = case.get("mutate_fae8")
            if mutation is not None and self.fae8_index == mutation[0]:
                self.uc.mem_write(BASE_ADDR + OFF_MODE_BYTE, bytes([mutation[1] & 0xFF]))
            self.fae8_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0xFAE80000 | offset)
        elif address == STUB_29EB58:
            self._log(address, self._offset(r0), r1)
        elif address == STUB_29EDFC:
            offset = self._offset(r0)
            self._log(address, offset, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0xE0000000 | offset)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = dict(case)
        self.fae8_index = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(STATE_ADDR, build_state(case))
        self.uc.mem_write(BASE_ADDR, build_base(case))
        self.uc.mem_write(MANAGER_ADDR, build_manager(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size in self.writes:
            in_manager = MANAGER_ADDR <= address < MANAGER_ADDR + MANAGER_SIZE
            in_base = BASE_ADDR <= address < BASE_ADDR + BASE_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if not (in_manager or in_base or in_stack):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
            "base": bytes(self.uc.mem_read(BASE_ADDR, BASE_SIZE)),
            "manager": bytes(self.uc.mem_read(MANAGER_ADDR, MANAGER_SIZE)),
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
    for key in ("state", "base", "manager"):
        if orig[key] != cand[key]:
            first = next(
                (
                    index
                    for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                    if left != right
                ),
                None,
            )
            problems.append(f"{key} differs first at +0x{first:x}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "slots": None,
        "mode_byte": 0x05,
        "flag": 0,
        "count": 0x12345678,
        "mode_word": 0x87654321,
        "engine_returns": {},
        "camp_returns": {},
        "mutate_fae8": None,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- live-slot counts: 0, 12, 24 non-negative entries, all boundaries
    cases.append(base_case("all slots negative", slots=[-1] * LIVE_SLOT_COUNT))
    cases.append(base_case("all slots zero", slots=[0] * LIVE_SLOT_COUNT))
    cases.append(base_case("all slots positive", slots=[1] * LIVE_SLOT_COUNT))
    cases.append(
        base_case(
            "signed slot boundaries",
            slots=[-128, -1, 0, 1, 127] * 4 + [-128, -1, 0, 127],
        )
    )
    cases.append(
        base_case(
            "alternating slots",
            slots=[-1 if index & 1 else index for index in range(LIVE_SLOT_COUNT)],
        )
    )

    # --- mode byte < 0x0C: columns = ceil(byte / 4)
    for mode in (0x00, 0x01, 0x03, 0x04, 0x0B):
        cases.append(base_case(f"mode byte 0x{mode:02x}", mode_byte=mode))

    # --- mode byte == 0x0C exactly, both +0x2C flag states
    cases.append(base_case("mode byte 0x0c flag 0", mode_byte=0x0C, flag=0))
    cases.append(base_case("mode byte 0x0c flag 1", mode_byte=0x0C, flag=1))
    cases.append(
        base_case("mode byte 0x0c flag 0xffffffff", mode_byte=0x0C, flag=0xFFFFFFFF)
    )

    # --- mode byte > 0x0C with both flag states
    for mode in (0x0D, 0x1F, 0x80, 0xFF):
        cases.append(base_case(f"mode byte 0x{mode:02x} flag 0", mode_byte=mode))
        cases.append(base_case(f"mode byte 0x{mode:02x} flag 1", mode_byte=mode,
                               flag=1))

    # --- helper return values: zero and non-zero per slot
    for zero_slot in SLOTS:
        engine = {slot: (0 if slot == zero_slot else 0xE0000000 | slot)
                  for slot in SLOTS}
        cases.append(
            base_case(f"engine zero for 0x{zero_slot:03x}", engine_returns=engine,
                      mode_byte=0x05)
        )
        camp = {slot: (0 if slot == zero_slot else 0xC0000000 | slot)
                for slot in SLOTS}
        cases.append(
            base_case(f"camp zero for 0x{zero_slot:03x}", camp_returns=camp,
                      mode_byte=0x05)
        )
    cases.append(
        base_case(
            "all helper results zero",
            engine_returns={slot: 0 for slot in SLOTS},
            camp_returns={slot: 0 for slot in SLOTS},
            mode_byte=0x0C,
            flag=1,
        )
    )
    cases.append(
        base_case(
            "all helper results distinct",
            engine_returns={slot: 0x11110000 | slot for slot in SLOTS},
            camp_returns={slot: 0x22220000 | slot for slot in SLOTS},
            mode_byte=0x0B,
        )
    )

    # --- the layout argument is re-read after every 0x0029FAE8 call
    cases.append(base_case("mutate mode after first layout call",
                           mode_byte=0x0B, mutate_fae8=(0, 0x03)))
    cases.append(base_case("mutate mode after second layout call",
                           mode_byte=0x05, mutate_fae8=(1, 0x25)))
    cases.append(base_case("mutate mode after third layout call",
                           mode_byte=0x0C, flag=1, mutate_fae8=(2, 0x07)))
    cases.append(base_case("mutate mode to 0xff after fourth layout call",
                           mode_byte=0x0D, flag=0, mutate_fae8=(3, 0xFF)))

    # --- initial manager words must be fully overwritten
    cases.append(
        base_case(
            "sentinel manager words",
            count=0xFFFFFFFF,
            mode_word=0x00000000,
            flag=0x80000000,
            mode_byte=0x0C,
        )
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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing camp_func_0026bc28 (0x0026bc28)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(all call relocations resolved)."
    )
    if len(cand_code) > FUNC_SIZE:
        raise RuntimeError("candidate no longer fits the original function slot")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("mode_split", "constexpr u8 kModeByteSplit = 0x0Cu;",
         "constexpr u8 kModeByteSplit = 0x0Du;"),
        ("column_count", "constexpr s32 kColumnCount = 4;",
         "constexpr s32 kColumnCount = 5;"),
        ("sparse_stride", "constexpr u32 kSparseSlotStride = 8u;",
         "constexpr u32 kSparseSlotStride = 4u;"),
        ("slot_c", "constexpr u32 kSlotC = 0x9A4u;",
         "constexpr u32 kSlotC = 0x9A8u;"),
        ("mode_word", "constexpr u32 kModeWordOffset = 0x30u;",
         "constexpr u32 kModeWordOffset = 0x34u;"),
    ):
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
