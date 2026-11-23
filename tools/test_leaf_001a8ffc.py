#!/usr/bin/env python3
"""Differential test for script_vm_func_001a8ffc (0x001a8ffc) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the reconstructed body, resolves
its R_ARM_CALL relocations to deterministic stubs placed at the original call
targets, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log (helper name plus every register argument);
  * the seed/selection global page at 0x0049F91C, the root context page and the
    row page returned by 0x00287B10;
  * any emulated write outside the private stack or the three fixture pages.

Coverage: pending-entry early return (positive/maximum/negative stored ids);
kind 0 and kind 1 index walks; inactive and unknown kinds; non-null/absent slot
results; every plot mode of both reporters (0x2E8558 modes 6/7/8/9/0xA/0xB and
0x2E876C modes 0/1/2/3/4/5); zero, positive and negative amounts; signed target
boundaries; the cross-index suppression flag; the 0x64..0x18F loop bounds; and
the pending fallback result.
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_001a8ffc"

FUNC_ADDR = 0x001A8FFC
FUNC_SIZE = 1036

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000
GLOBAL_ADDR = 0x0049E000  # contains the 0x0049F91C state block
GLOBAL_SIZE = 0x00002000
CTX_ADDR = 0x00710000
CTX_SIZE = 0x00002000  # covers root + 0x1066
ROW_ADDR = 0x00730000
ROW_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SCRIPT_GLOBAL_OFF = 0x0049F91C - GLOBAL_ADDR
PENDING_OFF = SCRIPT_GLOBAL_OFF + 0xAC
STORED_OFF = SCRIPT_GLOBAL_OFF + 0xB0

STUB_2C2B1C = 0x002C2B1C
STUB_287B10 = 0x00287B10
STUB_295CBC = 0x00295CBC
STUB_287AB4 = 0x00287AB4
STUB_299064 = 0x00299064
STUB_287AFC = 0x00287AFC
STUB_287ADC = 0x00287ADC
STUB_2990DC = 0x002990DC
STUB_28F460 = 0x0028F460
STUB_2E8558 = 0x002E8558
STUB_2E876C = 0x002E876C
STUB_287A68 = 0x00287A68

STUB_NAMES = {
    STUB_2C2B1C: "engine_func_002c2b1c",
    STUB_287B10: "script_vm_func_00287b10",
    STUB_295CBC: "script_vm_func_00295cbc",
    STUB_287AB4: "engine_func_00287ab4",
    STUB_299064: "script_vm_func_00299064",
    STUB_287AFC: "script_vm_func_00287afc",
    STUB_287ADC: "script_vm_func_00287adc",
    STUB_2990DC: "script_vm_func_002990dc",
    STUB_28F460: "script_vm_func_0028f460",
    STUB_2E8558: "script_vm_func_002e8558",
    STUB_2E876C: "script_vm_func_002e876c",
    STUB_287A68: "script_vm_func_00287a68",
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

ABSENT = None  # read_slot reports no entry for this slot


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = None
    for name, value in funcs.items():
        if "001a8ffc" in name:
            entry = value
            break
    if entry is None:
        raise RuntimeError(f"script_vm_func_001a8ffc not in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = entry
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for "
                f"{rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name in rel.symbol_name:
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


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate(obj_file)


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
    return relocate(obj_file)


# --------------------------------------------------------------------- fixtures
def make_case(name: str, entries=None, pending: int = 0, entry_id: int = 0x1234,
              row_value: int = 0x0042, has_pending: int = 0, **fields) -> dict:
    case = {
        "name": name,
        "entries": entries or {},
        "pending": pending & 0xFF,
        "entry_id": entry_id,
        "row_value": row_value,
        "has_pending": has_pending,
    }
    case.update(fields)
    return case


def entry(kind: int, slots, active: int = 1, any_entry: int = 1) -> dict:
    return {"kind": kind, "slots": list(slots), "active": active, "any": any_entry}


def build_ctx(case: dict) -> bytes:
    page = bytearray(b"\xA5" * CTX_SIZE)
    struct.pack_into("<h", page, 0x2A, _s16(case["entry_id"]))
    struct.pack_into("<h", page, 0x1060, _s16(case.get("lower_limit", 0)))
    struct.pack_into("<h", page, 0x1062, _s16(case.get("zero_target", 0)))
    struct.pack_into("<h", page, 0x1064, _s16(case.get("low_target", 0)))
    struct.pack_into("<h", page, 0x1066, _s16(case.get("high_target", 0)))
    return bytes(page)


def build_global(case: dict) -> bytes:
    page = bytearray(b"\x5A" * GLOBAL_SIZE)
    page[PENDING_OFF] = case["pending"]
    struct.pack_into("<I", page, STORED_OFF, 0xDEADBEEF)
    return bytes(page)


def build_row(case: dict) -> bytes:
    page = bytearray(b"\x3C" * ROW_SIZE)
    struct.pack_into("<h", page, 0x12, _s16(case["row_value"]))
    return bytes(page)


def _s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(ROW_ADDR, ROW_SIZE)
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
        self.reported_plots: list = []

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _entry(self, index: int) -> dict:
        return self.case["entries"][index]

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        if address == STUB_2C2B1C:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
            return
        if address == STUB_287B10:
            entry_id = uc.reg_read(arm.UC_ARM_REG_R0)
            self._log(address, entry_id)
            uc.reg_write(arm.UC_ARM_REG_R0, ROW_ADDR)
            return
        if address == STUB_295CBC:
            self._log(address, uc.reg_read(arm.UC_ARM_REG_R0),
                      uc.reg_read(arm.UC_ARM_REG_R1))
            return
        if address == STUB_287AB4:
            self._log(address, uc.reg_read(arm.UC_ARM_REG_R0),
                      uc.reg_read(arm.UC_ARM_REG_R1))
            return
        if address in (STUB_299064, STUB_287AFC, STUB_287ADC, STUB_28F460):
            index = uc.reg_read(arm.UC_ARM_REG_R0)
            self._log(address, index)
            if address == STUB_299064:
                result = 1 if index in self.case["entries"] else 0
            elif address == STUB_287AFC:
                result = self._entry(index)["kind"]
            elif address == STUB_287ADC:
                result = self._entry(index)["active"]
            else:  # STUB_28F460
                result = self._entry(index)["any"]
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
            return
        if address == STUB_2990DC:
            index = uc.reg_read(arm.UC_ARM_REG_R0)
            slot = uc.reg_read(arm.UC_ARM_REG_R1)
            out = uc.reg_read(arm.UC_ARM_REG_R2)
            self._log(address, index, slot, out)
            value = self._entry(index)["slots"][slot]
            if value is ABSENT:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
                return
            amount, ident = value
            buffer = struct.pack("<iH2xI", _s32(amount), ident & 0xFFFF, 0)
            uc.mem_write(out, buffer)
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
            return
        if address in (STUB_2E8558, STUB_2E876C):
            mode = uc.reg_read(arm.UC_ARM_REG_R0)
            arg1 = uc.reg_read(arm.UC_ARM_REG_R1)
            arg2 = uc.reg_read(arm.UC_ARM_REG_R2)
            self._log(address, mode, arg1, arg2)
            self.reported_plots.append((STUB_NAMES[address], mode, arg1, arg2))
            return
        if address == STUB_287A68:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["has_pending"])
            return
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

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.reported_plots = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOBAL_ADDR, build_global(case))
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(ROW_ADDR, build_row(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for reg in (
            arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1,
            arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3,
        ):
            self.uc.reg_write(reg, 0x11111111)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=10_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            if GLOBAL_ADDR <= address < GLOBAL_ADDR + GLOBAL_SIZE:
                continue
            if CTX_ADDR <= address < CTX_ADDR + CTX_SIZE:
                continue
            if ROW_ADDR <= address < ROW_ADDR + ROW_SIZE:
                continue
            unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "plots": list(self.reported_plots),
            "fixtures": {
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "ctx": bytes(self.uc.mem_read(CTX_ADDR, CTX_SIZE)),
                "row": bytes(self.uc.mem_read(ROW_ADDR, ROW_SIZE)),
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
            "call_log:\n    orig=" + repr(orig["call_log"]) +
            "\n    cand=" + repr(cand["call_log"])
        )
    if orig["plots"] != cand["plots"]:
        problems.append(
            "plots:\n    orig=" + repr(orig["plots"]) +
            "\n    cand=" + repr(cand["plots"])
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


def _s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- pending-entry early return
    cases.append(make_case("pending entry positive", pending=1,
                           entry_id=0x1234, row_value=0x7FFF))
    cases.append(make_case("pending entry negative", pending=1,
                           entry_id=-1, row_value=-0x8000))
    cases.append(make_case("pending entry zero", pending=1,
                           entry_id=0, row_value=0))
    cases.append(make_case("no pending entry", pending=0))

    # --- empty walk / pending fallback
    cases.append(make_case("empty walk returns 0", has_pending=0))
    cases.append(make_case("empty walk fallback returns 3", has_pending=1))

    # --- kind 1: present < 2, total == 0 -> mode 0xA, result 1
    cases.append(make_case(
        "kind1 short zero total", low_target=5,
        entries={100: entry(1, [(0, 5)] + [ABSENT] * 5)}))
    # --- kind 1: present < 2, total != 0 -> mode 0xB
    cases.append(make_case(
        "kind1 short positive total", high_target=7,
        entries={100: entry(1, [(3, 7)] + [ABSENT] * 5)}))
    cases.append(make_case(
        "kind1 short negative total", high_target=7,
        entries={100: entry(1, [(-4, 7)] + [ABSENT] * 5)}))
    # --- kind 1: present >= 2, total == 0 -> mode 6, result 1
    cases.append(make_case(
        "kind1 long zero total", low_target=5,
        entries={100: entry(1, [(0, 5), (0, 9)] + [ABSENT] * 4)}))
    # --- kind 1: present >= 2, total != 0, low target 0 -> mode 9
    cases.append(make_case(
        "kind1 low target zero", low_target=0, high_target=7,
        entries={100: entry(1, [(0, 0), (9, 7)] + [ABSENT] * 4)}))
    # --- kind 1: remaining >= 2 -> mode 7
    cases.append(make_case(
        "kind1 remaining at least two", low_target=5, high_target=7,
        entries={100: entry(1, [(1, 7), (2, 9), (3, 9)] + [ABSENT] * 3)}))
    # --- kind 1: remaining < 2 -> mode 8
    cases.append(make_case(
        "kind1 remaining below two", low_target=5, high_target=7,
        entries={100: entry(1, [(0, 5), (4, 9)] + [ABSENT] * 4)}))
    # --- kind 1: no match -> release only
    cases.append(make_case(
        "kind1 no match releases", low_target=5, high_target=7,
        entries={100: entry(1, [(1, 9), (0, 8)] + [ABSENT] * 4)}))
    # --- kind 1: all slots absent
    cases.append(make_case(
        "kind1 all slots absent",
        entries={100: entry(1, [ABSENT] * 6)}))
    # --- kind 1: inactive / unknown kind
    cases.append(make_case(
        "kind1 inactive", low_target=5,
        entries={100: entry(1, [(0, 5)] + [ABSENT] * 5, active=0)}))
    cases.append(make_case(
        "unknown kind skipped", low_target=5,
        entries={100: entry(2, [(0, 5)] + [ABSENT] * 5)}))
    # --- signed target boundaries cannot match zero-extended slot ids
    cases.append(make_case(
        "kind1 negative high target", low_target=5, high_target=-0x8000,
        entries={100: entry(1, [(1, 0x8000), (0, 5)] + [ABSENT] * 4)}))
    cases.append(make_case(
        "kind1 negative low target", low_target=-0x8000, high_target=7,
        entries={100: entry(1, [(0, 0x8000), (3, 7)] + [ABSENT] * 4)}))

    # --- kind 0 branches
    cases.append(make_case(
        "kind0 short zero total", zero_target=8,
        entries={100: entry(0, [(0, 8)] + [ABSENT] * 5)}))
    cases.append(make_case(
        "kind0 short positive total", lower_limit=11,
        entries={100: entry(0, [(6, 11)] + [ABSENT] * 5)}))
    cases.append(make_case(
        "kind0 long zero total", zero_target=8,
        entries={100: entry(0, [(0, 8), (0, 8)] + [ABSENT] * 4)}))
    cases.append(make_case(
        "kind0 long zero target zero", lower_limit=11, zero_target=0,
        entries={100: entry(0, [(4, 11), (1, 9)] + [ABSENT] * 4)}))
    cases.append(make_case(
        "kind0 remaining at least two", lower_limit=11, zero_target=8,
        entries={100: entry(0, [(4, 11), (1, 9), (2, 9)] + [ABSENT] * 3)}))
    cases.append(make_case(
        "kind0 remaining below two", lower_limit=11, zero_target=8,
        entries={100: entry(0, [(0, 8), (5, 9)] + [ABSENT] * 4)}))
    cases.append(make_case(
        "kind0 no match releases", lower_limit=11, zero_target=8,
        entries={100: entry(0, [(5, 9), (0, 7)] + [ABSENT] * 4)}))
    cases.append(make_case(
        "kind0 lacks entries releases", lower_limit=11, zero_target=8,
        entries={100: entry(0, [(4, 11)] + [ABSENT] * 5, any_entry=0)}))
    cases.append(make_case(
        "kind0 inactive",
        entries={100: entry(0, [(4, 11)] + [ABSENT] * 5, active=0)}))
    cases.append(make_case(
        "kind0 negative targets", lower_limit=-0x8000, zero_target=-0x8000,
        entries={100: entry(0, [(0, 0x8000), (1, 0x8000)] + [ABSENT] * 4)}))

    # --- repeated lower-limit match keeps only the latest positive amount
    cases.append(make_case(
        "kind0 repeated lower match", lower_limit=11, zero_target=8,
        entries={100: entry(0, [(4, 11), (9, 11)] + [ABSENT] * 4)}))

    # --- suppression carries across indices (kind 1 then kind 0)
    cases.append(make_case(
        "kind1 suppresses later kind0", low_target=5, lower_limit=11,
        zero_target=8,
        entries={
            100: entry(1, [(0, 5)] + [ABSENT] * 5),
            101: entry(0, [(4, 11)] + [ABSENT] * 5),
        }))
    # --- two kind 1 indices independently reporting
    cases.append(make_case(
        "two kind1 indices", low_target=5, high_target=7,
        entries={
            100: entry(1, [(0, 5)] + [ABSENT] * 5),
            150: entry(1, [(2, 7)] + [ABSENT] * 5),
        }))

    # --- loop bounds: first and last index processed, index 0x190 ignored
    cases.append(make_case(
        "loop bounds 0x64 and 0x18f", low_target=5,
        entries={
            0x64: entry(1, [(0, 5)] + [ABSENT] * 5),
            0x18F: entry(1, [(0, 5)] + [ABSENT] * 5),
            0x190: entry(1, [(0, 5)] + [ABSENT] * 5),
        }))

    # --- plot without a result still consults the pending fallback
    cases.append(make_case(
        "mode 0xB then pending fallback", high_target=7, has_pending=1,
        entries={100: entry(1, [(1, 7)] + [ABSENT] * 5)}))

    return cases


def run_cases(orig_code: bytes, cand_code: bytes, cases) -> int:
    runner_orig = Runner()
    runner_cand = Runner()
    passed = 0
    for case in cases:
        orig = runner_orig.run(orig_code, case)
        cand = runner_cand.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
              f"{len(orig['plots'])} plots, ret={orig['ret']})")
    return passed


def main() -> None:
    print("Testing script_vm_func_001a8ffc (0x001a8ffc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_cases(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("high_target_offset", "constexpr u32 kHighTargetOffset = 0x66;",
         "constexpr u32 kHighTargetOffset = 0x68;"),
        ("kind_one_mode_b", "plot_kind_one(0xB, static_cast<u16>(high_target),",
         "plot_kind_one(0xC, static_cast<u16>(high_target),"),
        ("zero_target_offset", "constexpr u32 kZeroTargetOffset = 0x62;",
         "constexpr u32 kZeroTargetOffset = 0x64;"),
    ):
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
