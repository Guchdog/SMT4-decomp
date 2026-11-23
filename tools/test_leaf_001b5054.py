#!/usr/bin/env python3
"""Differential test for script_vm_func_001b5054 (0x001b5054) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the
script_vm_func_001b5054 body, resolves its direct ARM BL targets to
deterministic stubs, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with each helper's architected register arguments;
  * the complete scene, global-slot, VM-context, action-owner and manager
    pages, which must be identical after the call;
  * every memory write outside the private stack (address, size and value).

Coverage: all four +0x44A0 selector flags, the +0x44A8 lookup mask (each bit
separately and together), the +0x7C entry bit, every +0x64 state value, the
0x0027EB98 chain (null context, null +0x28 owner, signed +0x14C selector 7/9/
13, negative and non-matching selectors), signed 0x00345164 counts around
zero (including 0x80000000 / 0x7FFFFFFF), the 0x00439CA8 null gate and both
of its helper results, the +0x40/+0x100 precedence chain and the 0x002C1830
results that gate every tail path. Negative controls mutate the lookup mask,
the +0x100000 gate, the 0x16 state, the selector for 13, one dispatch key and
the (7, 1) camp request; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001b5054"

FUNC_ADDR = 0x001B5054
FUNC_SIZE = 836

# Covers the function and every stub target (0x002C0AC8 .. 0x003C0564).
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000
DATA_ADDR = 0x00430000
DATA_SIZE = 0x00010000
SCENE_ADDR = 0x00710000
SCENE_SIZE = 0x00010000
CTX_ADDR = 0x00720000
CTX_SIZE = 0x00010000
OWNER_ADDR = 0x00730000
OWNER_SIZE = 0x00010000
MANAGER_ADDR = 0x00740000
MANAGER_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SLOT_VM_CONTEXT = 0x0043427C
SLOT_ACTION_MANAGER = 0x00434290
SLOT_GAME_OVER = 0x00439CA8

STUB_2C0AC8 = 0x002C0AC8
STUB_295E74 = 0x00295E74
STUB_295E48 = 0x00295E48
STUB_2BF41C = 0x002BF41C
STUB_27EB98 = 0x0027EB98
STUB_345164 = 0x00345164
STUB_3ADCD8 = 0x003ADCD8
STUB_33851C = 0x0033851C
STUB_2C1830 = 0x002C1830
STUB_27EAE4 = 0x0027EAE4
STUB_2BC200 = 0x002BC200
STUB_3C0564 = 0x003C0564
STUB_337558 = 0x00337558

STUB_NAMES = {
    STUB_2C0AC8: "ui_func_002c0ac8",
    STUB_295E74: "script_vm_func_00295e74",
    STUB_295E48: "script_vm_func_00295e48",
    STUB_2BF41C: "battle_func_002bf41c",
    STUB_27EB98: "script_vm_func_0027eb98",
    STUB_345164: "func_00345164",
    STUB_3ADCD8: "script_vm_func_003adcd8",
    STUB_33851C: "script_vm_func_0033851c",
    STUB_2C1830: "camp_func_002c1830",
    STUB_27EAE4: "script_vm_func_0027eae4",
    STUB_2BC200: "camp_func_002bc200",
    STUB_3C0564: "battle_func_003c0564",
    STUB_337558: "func_00337558",
}

# Architected integer arguments per recovered prototype.
STUB_ARGS = {
    STUB_2C0AC8: 1,
    STUB_295E74: 0,
    STUB_295E48: 1,
    STUB_2BF41C: 1,
    STUB_27EB98: 1,
    STUB_345164: 2,
    STUB_3ADCD8: 1,
    STUB_33851C: 1,
    STUB_2C1830: 2,
    STUB_27EAE4: 0,
    STUB_2BC200: 1,
    STUB_3C0564: 2,
    STUB_337558: 1,
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

PAGES = {
    "scene": (SCENE_ADDR, SCENE_SIZE),
    "data": (DATA_ADDR, DATA_SIZE),
    "ctx": (CTX_ADDR, CTX_SIZE),
    "owner": (OWNER_ADDR, OWNER_SIZE),
    "manager": (MANAGER_ADDR, MANAGER_SIZE),
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001b5054" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_001b5054 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name == rel.symbol_name:
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
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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
def build_scene(case: dict) -> bytes:
    page = bytearray(SCENE_SIZE)
    struct.pack_into("<I", page, 0x00, 0xC0DE0000)
    struct.pack_into("<I", page, 0x20, case.get("task", 0x00112233) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x64, case.get("state", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x7C, case.get("flags_7C", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x44A0, case.get("flags_44A0", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x44A8, case.get("flags_44A8", 0) & 0xFFFFFFFF)
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    struct.pack_into("<I", page, SLOT_VM_CONTEXT - DATA_ADDR,
                     case.get("vm_global", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, SLOT_ACTION_MANAGER - DATA_ADDR,
                     MANAGER_ADDR)
    struct.pack_into("<I", page, SLOT_GAME_OVER - DATA_ADDR,
                     case.get("game_over_global", 0x00BEEF00) & 0xFFFFFFFF)
    return bytes(page)


def build_ctx(case: dict) -> bytes:
    page = bytearray(CTX_SIZE)
    struct.pack_into("<I", page, 0x00, 0xC7C70000)
    struct.pack_into("<I", page, 0x28,
                     case.get("owner_ptr", OWNER_ADDR) & 0xFFFFFFFF)
    return bytes(page)


def build_owner(case: dict) -> bytes:
    page = bytearray(OWNER_SIZE)
    struct.pack_into("<I", page, 0x00, 0x00000A11)
    struct.pack_into("<H", page, 0x14C, case.get("owner_action", 0) & 0xFFFF)
    return bytes(page)


def build_manager(case: dict) -> bytes:
    page = bytearray(MANAGER_SIZE)
    struct.pack_into("<I", page, 0x00, 0x00000A22)
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(SCENE_ADDR, SCENE_SIZE)
        self.uc.mem_map(CTX_ADDR, CTX_SIZE)
        self.uc.mem_map(OWNER_ADDR, OWNER_SIZE)
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

    @staticmethod
    def _u32(value: int) -> int:
        return value & 0xFFFFFFFF

    def _log(self, address: int, *args) -> None:
        self.call_log.append((STUB_NAMES[address], tuple(args)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (size * 8)) - 1)))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = self._u32(uc.reg_read(arm.UC_ARM_REG_R0))
        r1 = self._u32(uc.reg_read(arm.UC_ARM_REG_R1))
        count = STUB_ARGS[address]
        raw = (r0, r1)[:count]
        self._log(address, *raw)

        if address == STUB_2C0AC8:
            uc.reg_write(arm.UC_ARM_REG_R0, SCENE_ADDR)
        elif address == STUB_295E74:
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("selection", 0) & 0xFFFFFFFF)
        elif address == STUB_295E48:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2BF41C:
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("task_result", 0) & 0xFFFFFFFF)
        elif address == STUB_27EB98:
            result = CTX_ADDR if self.case.get("vm_nonnull", False) else 0
            uc.reg_write(arm.UC_ARM_REG_R0, result)
        elif address == STUB_345164:
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("action_count", 0) & 0xFFFFFFFF)
        elif address == STUB_3ADCD8:
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("game_over_result", 1) & 0xFFFFFFFF)
        elif address == STUB_33851C:
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("script_ready", 1) & 0xFFFFFFFF)
        elif address == STUB_2C1830:
            key = f"camp_{r0}"
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get(key, 0) & 0xFFFFFFFF)
        elif address == STUB_27EAE4:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2BC200:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_3C0564:
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_337558:
            uc.reg_write(arm.UC_ARM_REG_R0,
                         self.case.get("probe", 1) & 0xFFFFFFFF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SCENE_ADDR, build_scene(case))
        self.uc.mem_write(DATA_ADDR, build_data(case))
        self.uc.mem_write(CTX_ADDR, build_ctx(case))
        self.uc.mem_write(OWNER_ADDR, build_owner(case))
        self.uc.mem_write(MANAGER_ADDR, build_manager(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("handle", 0x12345678))
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
            in_scene = SCENE_ADDR <= address < SCENE_ADDR + SCENE_SIZE
            if not in_stack and not in_scene:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": [
                (address, size)
                for address, size, _value in self.writes
                if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            ],
            "fixtures": {
                name: bytes(self.uc.mem_read(address, size))
                for name, (address, size) in PAGES.items()
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
    if orig["writes"] != cand["writes"]:
        problems.append(
            "write log:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
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
        "handle": 0x12345678,
        "task": 0x00112233,
        "state": 0,
        "flags_7C": 0,
        "flags_44A0": 0,
        "flags_44A8": 0,
        "selection": 0,
        "task_result": 0,
        "vm_global": 0,
        "vm_nonnull": False,
        "owner_ptr": OWNER_ADDR,
        "owner_action": 0,
        "action_count": 0,
        "game_over_global": 0x00BEEF00,
        "game_over_result": 1,
        "script_ready": 1,
        "camp_1": 1,
        "camp_7": 0,
        "camp_8": 1,
        "probe": 1,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- +0x44A8 lookup mask: each bit, both, unrelated bits, and clear effect
    for mask in (0x00080001, 0x00080000, 0x00000001, 0x00080003, 0x00000002,
                 0x00100000, 0x00080001 | 0x140):
        for selection in (0, 1):
            cases.append(
                base_case(
                    f"lookup mask 0x{mask:08x} selection {selection}",
                    flags_44A8=mask,
                    flags_44A0=0x140,
                    selection=selection,
                )
            )

    # --- +0x44A0 bit 20 gate
    for selection in (0, 1):
        cases.append(
            base_case(
                f"task gate bit20 selection {selection}",
                flags_44A0=0x100000 | 0x140,
                selection=selection,
            )
        )

    # --- +0x44A0 bit 9 early out (selection must not be consulted for output)
    for selection in (0, 1):
        cases.append(
            base_case(
                f"early out bit9 selection {selection}",
                flags_44A0=0x200 | 0x140,
                selection=selection,
            )
        )
    cases.append(base_case("early out bit9 other bits",
                           flags_44A0=0xFFFFFFFF))

    # --- 0x002BF41C task presence
    for result in (0, 1, 0xFFFFFFFF):
        for selection in (0, 1):
            cases.append(
                base_case(
                    f"task_present {result:#x} selection {selection}",
                    task_result=result,
                    selection=selection,
                )
            )

    # --- scene +0x7C bit 0
    for flags in (0, 1, 2, 0xFFFFFFFF):
        for selection in (0, 1):
            cases.append(
                base_case(
                    f"flags_7C 0x{flags:08x} selection {selection}",
                    flags_7C=flags,
                    selection=selection,
                )
            )

    # --- scene +0x64 state selector
    for state in (0x14, 0x15, 0x16, 0x13, 0x17, 0x10016, 0xFFFFFFFF):
        for selection in (0, 1):
            cases.append(
                base_case(
                    f"state 0x{state:08x} selection {selection}",
                    state=state,
                    selection=selection,
                )
            )

    # --- 0x0027EB98 chain: null global, null result, null owner
    cases.append(base_case("vm global null"))
    cases.append(base_case("vm global non-null, lookup null", vm_global=CTX_ADDR))
    cases.append(
        base_case("vm global non-null, owner null", vm_global=CTX_ADDR,
                  vm_nonnull=True, owner_ptr=0)
    )
    cases.append(
        base_case("vm global non-null, owner non-null selector 0",
                  vm_global=CTX_ADDR, vm_nonnull=True, owner_action=0)
    )

    # --- signed owner selector: 7/9/13, neighbours, sign boundary
    for action in (6, 7, 8, 9, 12, 13, 14, 0, -1, 0x7FFF, 0x8000,
                   0x8007, 0x800D):
        for selection in (0, 1):
            cases.append(
                base_case(
                    f"owner action 0x{action & 0xFFFF:04x} selection {selection}",
                    vm_global=CTX_ADDR,
                    vm_nonnull=True,
                    owner_action=action,
                    selection=selection,
                )
            )

    # --- signed 0x00345164 action-node count around zero
    for count in (0, 1, 2, 0x7FFFFFFF, 0xFFFFFFFF, 0x80000000, 0x80000001):
        cases.append(
            base_case(
                f"action count 0x{count:08x}",
                action_count=count,
            )
        )
    cases.append(
        base_case("action count positive with vm path",
                  vm_global=CTX_ADDR, vm_nonnull=True, owner_action=8,
                  action_count=3)
    )

    # --- 0x00439CA8 gate and both helper results
    cases.append(base_case("game over global null", game_over_global=0))
    cases.append(base_case("game over helper zero", game_over_result=0))
    cases.append(base_case("script ready zero", script_ready=0))
    cases.append(base_case("both gates pass"))

    # --- +0x44A0 bit 6 / bit 8 dispatch chain
    for flags in (0x40, 0x100, 0x140, 0x40 | 0x800, 0x100 | 0x800,
                  0xFFFFFFFF, 0x800):
        for camp1 in (0, 1):
            cases.append(
                base_case(
                    f"dispatch flags 0x{flags:08x} camp1 {camp1}",
                    flags_44A0=flags,
                    camp_1=camp1,
                )
            )

    # --- neither selector bit: (7, 1) then (8, 1) chain
    for camp7 in (0, 1, 0xFFFFFFFF):
        for camp8 in (0, 1):
            for probe in (0, 1):
                cases.append(
                    base_case(
                        f"camp7 {camp7:#x} camp8 {camp8} probe {probe}",
                        camp_7=camp7,
                        camp_8=camp8,
                        probe=probe,
                    )
                )
    cases.append(base_case("camp7 path preserves other flags",
                           flags_44A0=0x80070, camp_7=1))
    cases.append(base_case("camp8 path preserves other flags",
                           flags_44A0=0x80100, camp_7=0, camp_8=1,
                           probe=1))

    # --- handle forwarding
    for handle in (0, 1, 0xFFFFFFFF, 0xDEADBEEF):
        cases.append(base_case(f"handle 0x{handle:08x}", handle=handle))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, case)
        cand = LeafRunner().run(cand_code, case)
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
    print("Testing script_vm_func_001b5054 (0x001b5054)...")
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
        ("lookup_mask_bit20", "constexpr u32 kLookupMask = 0x00080001u;",
         "constexpr u32 kLookupMask = 0x00000001u;"),
        ("task_gate", "constexpr u32 kTaskGateBit = 0x100000u;",
         "constexpr u32 kTaskGateBit = 0x200000u;"),
        ("message_state", "constexpr u32 kStateMessage = 0x16u;",
         "constexpr u32 kStateMessage = 0x15u;"),
        ("owner_action_c", "constexpr s16 kOwnerActionC = 13;",
         "constexpr s16 kOwnerActionC = 14;"),
        ("dispatch_key_a", "constexpr u32 kDispatchKeyA = 0x0100016Eu;",
         "constexpr u32 kDispatchKeyA = 0x0100016Fu;"),
        ("camp_request_7", "if (camp_request(7u, 1u) != 0u) {",
         "if (camp_request(8u, 1u) != 0u) {"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, case)
            bad = LeafRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
