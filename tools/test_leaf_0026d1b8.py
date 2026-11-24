#!/usr/bin/env python3
"""Differential test for script_vm_func_0026d1b8 (0x0026d1b8) using Unicorn ARM.

Compiles ``src/engine/leaf_batch42_b.cpp``, extracts the
``script_vm_func_0026d1b8`` body (and its literal words), resolves the six
direct call relocations, and runs the pinned original
(``extracted/exefs/code.bin``) against the candidate on separate Unicorn ARM
machines with identical fixtures.

Compared output per case:
  * returned r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log (all six helpers are argument-free in the pinned
    implementation; the callback and tail target are logged by name);
  * the complete 0x800-byte object fixture, the alternate object used by the
    pointer-swap case, and the global-slot page.

The recovered contract is documented above the implementation.  In short:

  if (camp_func_0029e2cc() != 0) return that value;
  object = *(u8**)0x0043DCF0;                 # exactly one load, before the probes
  Status_GetSelectedActorPtr();               # result discarded
  event  = camp_func_002b8ccc();              # u8
  value6 = camp_func_002830e0();              # s32
  value8 = camp_func_00282f3c();              # s32
  flagged = OR over six event-id groups of the recovered predicates;
  if (flagged) script_vm_func_0026c480();
  if ((s16)object[0x3a] == value8 && (s8)object[0x44] == value6)
      return (s32)(s8)object[0x44];
  state = object[0x66c];
  if (state in {2,3,4,0xc,0xd,0xe,0xf,0x10})
      return func_001b0454();                 # tail branch in the original
  return state;

Helper stubs are deterministic and placed at the original call targets.  The
selected-actor stub can replace the global object pointer to prove the candidate
uses the pointer cached before the probes; the probe stubs can mutate object
fields to prove the fields are read after the probes.  The tail stub returns a
configured word so the forwarded r0 is visible.

Coverage: gate zero/non-zero signed values, every id in all six groups and
several non-members, value6 in {0, 1, -1} x value8 in {-1, 0, 1} x flag {0, 1},
the 0xe3 overlap across groups 2/4/6, the 0xcc multi-group accumulation, signed
halfword/byte comparison boundaries, every tail state plus neighbours,
cached-pointer swaps, and stub-driven field mutations.

Negative controls mutate the gate polarity, each group boundary and flag
polarity, the group-5 signed test, the tail-state set, both comparison
operators, the final return, the object-slot address, the probe order, the probe
values and the cached-pointer read; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch42_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_0026d1b8"

FUNC_ADDR = 0x0026D1B8
FUNC_SIZE = 504

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x001B0454 through 0x002B8CCC
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00020000  # contains the 0x0043DCF0 global slot
OBJ_ADDR = 0x00500000
OBJ_SIZE = 0x00010000
ALT_ADDR = 0x00510000
ALT_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

GLOBAL_SLOT = 0x0043DCF0

FLAG_OFFSET = 0x42
HALF_OFFSET = 0x3A
BYTE_OFFSET = 0x44
STATE_OFFSET = 0x66C

SNAPSHOT_SIZE = 0x800

STUB_GATE = 0x0029E2CC
STUB_SELECTED = 0x0029AF4C
STUB_EVENT = 0x002B8CCC
STUB_VALUE6 = 0x002830E0
STUB_VALUE8 = 0x00282F3C
STUB_CALLBACK = 0x0026C480
STUB_TAIL = 0x001B0454

STUB_NAMES = {
    "camp_func_0029e2cc": STUB_GATE,
    "Status_GetSelectedActorPtr": STUB_SELECTED,
    "camp_func_002b8ccc": STUB_EVENT,
    "camp_func_002830e0": STUB_VALUE6,
    "camp_func_00282f3c": STUB_VALUE8,
    "script_vm_func_0026c480": STUB_CALLBACK,
    "func_001b0454": STUB_TAIL,
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

BX_LR = 0xE12FFF1E

GROUP_IDS = {
    1: (0x1C, 0x1E, 0xB8, 0xBF, 0xCC),
    2: (0x1B, 0x1D, 0xB7, 0xBE, 0xE3),
    3: (0x22, 0x24, 0xB6, 0xC1, 0xCC),
    4: (0x21, 0x23, 0xB5, 0xC0, 0xE3),
    5: (0x26, 0x04, 0xBB, 0xC3, 0xCC),
    6: (0x25, 0x03, 0xBA, 0xC2, 0xE3),
}
TAIL_STATES = (2, 3, 4, 0x0C, 0x0D, 0x0E, 0x0F, 0x10)


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def symbol_offset(obj_file: Path, wanted: str) -> int:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = next(section for section in sections if section[1] == 2)
    strtab = sections[symtab[6]]
    for index in range(symtab[5] // 16):
        name, value, _size, _info, _other, _shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + index * 16
        )
        symbol = data[strtab[4] + name :].split(b"\x00")[0].decode(
            "ascii", errors="replace"
        )
        if symbol == wanted:
            return value
    raise RuntimeError(f"symbol {wanted} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("script_vm_func_0026d1b8")
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_0026d1b8 not found in {obj_file}: {sorted(funcs)}"
        )
    code_raw, relocs = candidate
    code = bytearray(code_raw)
    seen: list[str] = []

    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(f"unexpected relocation: {rel}")
        target = STUB_NAMES.get(rel.symbol_name or "")
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel}")
        seen.append(rel.symbol_name)
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        struct.pack_into(
            "<I",
            code,
            rel.offset,
            (original & 0xFF000000) | (displacement & 0x00FFFFFF),
        )

    expected = [
        "camp_func_0029e2cc",
        "Status_GetSelectedActorPtr",
        "camp_func_002b8ccc",
        "camp_func_002830e0",
        "camp_func_00282f3c",
        "script_vm_func_0026c480",
        "func_001b0454",
    ]
    if not set(seen) <= set(expected):
        raise RuntimeError(f"call relocations differ from expectation: {seen}")
    return bytes(code)


def compile_candidate(src: Path, obj: Path) -> bytes:
    obj.parent.mkdir(parents=True, exist_ok=True)
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compilation failed for {src}:\n{result.stderr}")
    return relocate_candidate(obj)


def compile_candidate_baseline() -> bytes:
    return compile_candidate(SOURCE, OUT_DIR / "leaf_batch42_b.o")


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant = OUT_DIR / f"mutant_{name}.cpp"
    mutant.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def build_object(page: bytearray, case: dict, prefix: int) -> None:
    for index in range(SNAPSHOT_SIZE):
        page[index] = (prefix + index * 7) & 0xFF
    struct.pack_into("<h", page, HALF_OFFSET, case["half"])
    page[FLAG_OFFSET] = case["flag"] & 0xFF
    struct.pack_into("<b", page, BYTE_OFFSET, case["byte44"])
    page[STATE_OFFSET] = case["state"] & 0xFF


def obj_image(case: dict) -> bytes:
    page = bytearray(OBJ_SIZE)
    build_object(page, case, 0x31)
    return bytes(page)


def alt_image(case: dict) -> bytes:
    page = bytearray(ALT_SIZE)
    alt = {
        "half": case.get("alt_half", 0x1234),
        "flag": case.get("alt_flag", 0xA5),
        "byte44": case.get("alt_byte44", 0x55),
        "state": case.get("alt_state", 0x11),
    }
    build_object(page, alt, 0xC7)
    return bytes(page)


def write_u32(uc, address: int, value: int) -> None:
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    """One Unicorn machine with deterministic stubs at the original addresses."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(ALT_ADDR, ALT_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES.values():
            self.uc.mem_write(address, struct.pack("<I", BX_LR))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_helper, begin=address, end=address
            )

        self.call_log: list = []
        self.case: dict = {}

    # -------------------------------------------------------------- stubs
    def _write_mutations(self, mutations: dict | None) -> None:
        if not mutations:
            return
        page = bytearray(self.uc.mem_read(OBJ_ADDR, SNAPSHOT_SIZE))
        if "half" in mutations:
            struct.pack_into("<h", page, HALF_OFFSET, mutations["half"])
        if "flag" in mutations:
            page[FLAG_OFFSET] = mutations["flag"] & 0xFF
        if "byte44" in mutations:
            struct.pack_into("<b", page, BYTE_OFFSET, mutations["byte44"])
        if "state" in mutations:
            page[STATE_OFFSET] = mutations["state"] & 0xFF
        self.uc.mem_write(OBJ_ADDR, bytes(page))

    def _on_helper(self, uc, address: int, size: int, user_data) -> None:
        case = self.case
        if address == STUB_GATE:
            self.call_log.append(("camp_func_0029e2cc",))
            uc.reg_write(arm.UC_ARM_REG_R0, case["gate"] & 0xFFFFFFFF)
        elif address == STUB_SELECTED:
            self.call_log.append(("Status_GetSelectedActorPtr",))
            if case["swap_object_on_selected"]:
                write_u32(uc, GLOBAL_SLOT, ALT_ADDR)
            uc.reg_write(arm.UC_ARM_REG_R0, case["selected_ret"] & 0xFFFFFFFF)
        elif address == STUB_EVENT:
            self.call_log.append(("camp_func_002b8ccc",))
            self._write_mutations(case.get("event_mutates"))
            uc.reg_write(arm.UC_ARM_REG_R0, case["event"] & 0xFF)
        elif address == STUB_VALUE6:
            self.call_log.append(("camp_func_002830e0",))
            self._write_mutations(case.get("value6_mutates"))
            uc.reg_write(arm.UC_ARM_REG_R0, case["value6"] & 0xFFFFFFFF)
        elif address == STUB_VALUE8:
            self.call_log.append(("camp_func_00282f3c",))
            self._write_mutations(case.get("value8_mutates"))
            uc.reg_write(arm.UC_ARM_REG_R0, case["value8"] & 0xFFFFFFFF)
        elif address == STUB_CALLBACK:
            self.call_log.append(("script_vm_func_0026c480",))
        elif address == STUB_TAIL:
            self.call_log.append(("func_001b0454",))
            uc.reg_write(arm.UC_ARM_REG_R0, case["tail_ret"] & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def _prepare_memory(self, code: bytes, case: dict) -> None:
        uc = self.uc
        uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        uc.mem_write(OBJ_ADDR, b"\x00" * OBJ_SIZE)
        uc.mem_write(ALT_ADDR, b"\x00" * ALT_SIZE)
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x400)
        uc.mem_write(FUNC_ADDR, code)

        slot = 0 if case["null_object"] else OBJ_ADDR
        write_u32(uc, GLOBAL_SLOT, slot)
        uc.mem_write(OBJ_ADDR, obj_image(case))
        uc.mem_write(ALT_ADDR, alt_image(case))
        uc.ctl_flush_tb()

    def _set_registers(self, case: dict) -> None:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        junk = case["junk"]
        for index, value in enumerate(junk):
            uc.reg_write(arm.UC_ARM_REG_R0 + index, value)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.case = case

        self._prepare_memory(code, case)
        self._set_registers(case)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        uc = self.uc
        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "obj": bytes(uc.mem_read(OBJ_ADDR, SNAPSHOT_SIZE)),
            "alt": bytes(uc.mem_read(ALT_ADDR, SNAPSHOT_SIZE)),
            "data": bytes(uc.mem_read(GLOBAL_SLOT, 0x40)),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key, base in (("obj", OBJ_ADDR), ("alt", ALT_ADDR), ("data", GLOBAL_SLOT)):
        if orig[key] != cand[key]:
            diff = next(
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            )
            problems.append(
                f"{key} differs first at 0x{base + diff:08x}: "
                f"orig={orig[key][diff]:02x} cand={cand[key][diff]:02x}"
            )
    return problems


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "gate": 0,
        "event": 0xFF,
        "value6": 1,
        "value8": 0,
        "flag": 1,
        "half": 0x1234,
        "byte44": 0x02,
        "state": 0,
        "tail_ret": 0x00C0FFEE,
        "selected_ret": 0x11112222,
        "swap_object_on_selected": False,
        "null_object": False,
        "junk": (0x11111111, 0x22222222, 0x33333333),
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- gate ---------------------------------------------------------------
    for gate in (1, 2, 0x7FFFFFFF, -1, -0x80000000):
        cases.append(
            base_case(
                f"gate 0x{gate & 0xFFFFFFFF:08x} returns immediately (null object)",
                gate=gate, null_object=True,
            )
        )

    # --- every group id against the three register/flag inputs ---------------
    combos = (
        (0, -1, 0),
        (0, -1, 1),
        (0, 0, 0),
        (0, 0, 1),
        (0, 1, 0),
        (0, 1, 1),
        (1, -1, 0),
        (1, 0, 0),
        (-1, -1, 0),
        (-1, 1, 1),
    )
    unique_ids = sorted({ident for ids in GROUP_IDS.values() for ident in ids})
    for ident in unique_ids:
        for value6, value8, flag in combos:
            cases.append(
                base_case(
                    f"id 0x{ident:02x} v6={value6} v8={value8} flag={flag}",
                    event=ident, value6=value6, value8=value8, flag=flag,
                )
            )

    # --- non-members: flagged can never be set ------------------------------
    for ident in (0x00, 0x01, 0x02, 0x05, 0x1A, 0x20, 0x27, 0xB4, 0xB9, 0xBD,
                  0xC4, 0xFF):
        cases.append(
            base_case(
                f"non-member id 0x{ident:02x} never invokes the callback",
                event=ident, value6=0, value8=-1, flag=0,
            )
        )

    # --- explicit multi-group accumulation / group-6 flagged term -----------
    cases.append(
        base_case("0xcc sets flagged through groups 1/3/5 then calls",
                  event=0xCC, value6=0, value8=1, flag=0)
    )
    cases.append(
        base_case("0xe3 group 6 consumes the flagged term",
                  event=0xE3, value6=0, value8=-1, flag=0)
    )
    cases.append(
        base_case("0xe3 group 6 without the flagged term stays quiet",
                  event=0xE3, value6=0, value8=-1, flag=1)
    )

    # --- comparison of object+0x3a with value8 ------------------------------
    for half in (-0x8000, -1, 0, 1, 0x7FFF, 0x1234):
        for value8 in (half, half - 1, half + 1):
            cases.append(
                base_case(
                    f"half {half} vs value8 {value8}",
                    event=0xFF, value6=1, value8=value8, half=half,
                )
            )
    for value8 in (-0x8001, 0x8000, 0x7FFFFFFF, -0x80000000):
        cases.append(
            base_case(
                f"half 0 vs out-of-range value8 {value8}",
                value8=value8, half=0,
            )
        )

    # --- comparison of object+0x44 with value6 (only after the half matches) -
    for byte44 in (-128, -1, 0, 1, 127):
        for value6 in (byte44, byte44 - 1, byte44 + 1):
            cases.append(
                base_case(
                    f"byte44 {byte44} vs value6 {value6} (half matches)",
                    value6=value6, byte44=byte44, half=0x2222, value8=0x2222,
                )
            )
    cases.append(
        base_case("byte44 mismatch with half mismatch still returns state",
                  byte44=-5, value6=-5, half=1, value8=2, state=0x33)
    )

    # --- state dispatch ------------------------------------------------------
    for state in (0, 1, 2, 3, 4, 5, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10,
                  0x11, 0x80, 0xFF):
        cases.append(
            base_case(
                f"state 0x{state:02x}",
                event=0xFF, value6=0, value8=0, flag=0,
                half=0, byte44=0, state=state,
            )
        )

    # --- cached object pointer: the selected-actor stub swaps the global -----
    for alt_state, alt_half, alt_flag in (
        (2, 0x3333, 0x5A),
        (0xFF, 0x1234, 0x00),
        (0x0C, 0x0000, 0xFF),
    ):
        cases.append(
            base_case(
                "selected stub swaps the object pointer",
                swap_object_on_selected=True, event=0xB8, value6=0, value8=-1,
                flag=0, state=0x07, half=0x1111, byte44=0x11,
                alt_state=alt_state, alt_half=alt_half, alt_flag=alt_flag,
                alt_byte44=0x22,
            )
        )

    # --- probe-driven field mutations prove the fields are read afterwards ---
    cases.append(
        base_case("event stub clears the flag before the group tests",
                  event=0xB8, value6=1, value8=0, flag=1,
                  event_mutates={"flag": 0})
    )
    cases.append(
        base_case("event stub sets the flag before the group tests",
                  event=0xB8, value6=1, value8=0, flag=0,
                  event_mutates={"flag": 1})
    )
    cases.append(
        base_case("value6 stub rewrites the comparison halfword",
                  event=0xFF, value6=5, value8=5, half=0,
                  value6_mutates={"half": 5})
    )
    cases.append(
        base_case("value8 stub rewrites the comparison halfword",
                  event=0xFF, value6=0, value8=7, half=0,
                  value8_mutates={"half": 7})
    )
    cases.append(
        base_case("value6 stub rewrites byte44",
                  event=0xFF, value6=-3, value8=0x2222, half=0x2222,
                  byte44=0, value6_mutates={"byte44": -3})
    )
    cases.append(
        base_case("value8 stub rewrites the state byte into a tail state",
                  event=0xFF, value6=0, value8=0, half=1, byte44=1, state=1,
                  value8_mutates={"state": 0x0F}, tail_ret=0xFEEDFACE)
    )
    cases.append(
        base_case("junk r1-r3 and tail return forwarding",
                  event=0x25, value6=0, value8=-1, flag=0, state=0x10,
                  tail_ret=0xDEADBEEF,
                  junk=(0xDEADBEEF, 0x80000000, 0xFFFFFFFF))
    )
    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases) -> int:
    runner = Machine()
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
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, ret=0x{orig['ret']:08x})"
        )
    return passed


def main() -> None:
    print("Testing script_vm_func_0026d1b8 (0x0026d1b8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(7 call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("gate_polarity", "if (gate != 0) {", "if (gate == 0) {"),
        ("group1_first_id", "return id == 0x1C || id == 0x1E",
         "return id == 0x1D || id == 0x1E"),
        ("group1_flag_polarity",
         "    if (in_group_1(event)) {\n"
         "        if (value6 == 0 || flag_byte(object) == 0) {",
         "    if (in_group_1(event)) {\n"
         "        if (value6 == 0 || flag_byte(object) != 0) {"),
        ("group2_first_id", "return id == 0x1B || id == 0x1D",
         "return id == 0x1A || id == 0x1D"),
        ("group2_flag_polarity",
         "    if (in_group_2(event)) {\n"
         "        if (value6 == 0 || flag_byte(object) != 0) {",
         "    if (in_group_2(event)) {\n"
         "        if (value6 == 0 || flag_byte(object) == 0) {"),
        ("group3_signed_bound",
         "    if (in_group_3(event)) {\n"
         "        if (value6 != 0 || value8 < 0 || flag_byte(object) == 0) {",
         "    if (in_group_3(event)) {\n"
         "        if (value6 != 0 || value8 <= 0 || flag_byte(object) == 0) {"),
        ("group4_first_id", "return id == 0x21 || id == 0x23",
         "return id == 0x20 || id == 0x23"),
        ("group4_flag_polarity",
         "    if (in_group_4(event)) {\n"
         "        if (value6 != 0 || value8 < 0 || flag_byte(object) != 0) {",
         "    if (in_group_4(event)) {\n"
         "        if (value6 != 0 || value8 < 0 || flag_byte(object) == 0) {"),
        ("group5_signed_bound",
         "    if (in_group_5(event)) {\n"
         "        if (value6 != 0 || value8 >= 0 || flag_byte(object) == 0) {",
         "    if (in_group_5(event)) {\n"
         "        if (value6 != 0 || value8 > 0 || flag_byte(object) == 0) {"),
        ("group5_first_id", "return id == 0x26 || id == 0x04",
         "return id == 0x27 || id == 0x04"),
        ("group6_first_id", "return id == 0x25 || id == 0x03",
         "return id == 0x24 || id == 0x03"),
        ("tail_state", "state == 0x0F || state == 0x10", "state == 0x0F || state == 0x11"),
        ("half_compare", "kCompareHalfwordOffset) == value8", "kCompareHalfwordOffset) != value8"),
        ("byte_compare", "if (compare_byte == value6) {", "if (compare_byte != value6) {"),
        ("final_return", "    return state;\n}", "    return 0;\n}"),
        ("object_slot", "kObjectSlot = 0x0043DCF0", "kObjectSlot = 0x0043DCF4"),
        ("drop_probe", "(void)Status_GetSelectedActorPtr();", "(void)0;"),
        ("event_ignored", "const u32 event = camp_func_002b8ccc();",
         "const u32 event = 0x1C;"),
        ("value6_ignored", "const s32 value6 = camp_func_002830e0();",
         "const s32 value6 = 0;"),
        ("value8_ignored", "const s32 value8 = camp_func_00282f3c();",
         "const s32 value8 = 0;"),
        ("probe_order",
         "    const u32 event = camp_func_002b8ccc();\n"
         "    const s32 value6 = camp_func_002830e0();",
         "    const s32 value6 = camp_func_002830e0();\n"
         "    const u32 event = camp_func_002b8ccc();"),
        ("late_object_read",
         "    const u8* const object = global_object();\n\n"
         "    (void)Status_GetSelectedActorPtr();",
         "    (void)Status_GetSelectedActorPtr();\n"
         "    const u8* const object = global_object();"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        runner = Machine()
        for case in cases:
            orig = runner.run(orig_code, case)
            try:
                bad = runner.run(mutant_code, case)
            except RuntimeError:
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")
    print(f"{len(mutants)}/{len(mutants)} negative controls detected.")


if __name__ == "__main__":
    main()
