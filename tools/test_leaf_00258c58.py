#!/usr/bin/env python3
"""Differential test for ui_func_00258c58 (0x00258c58) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_00258c58 body,
resolves every direct call to a deterministic stub placed at the original
call-target address, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:

  * continuation PC and final SP, callee-saved r4-r11, and r0 (the final
    helper stub forces a deterministic r0 because the function is void)
  * ordered call log with every meaningful argument, including the fifth
    (stack) argument of script_vm_func_0026ac34 and the eight-id buffer that
    StatusDown_SetSubIdsA consumes
  * full status-work image, the 0x44E140 manager image, and the demon-info image

The function has no indirect calls: every edge is a direct BL to one of the
stubs below. Covered paths include both panels (+0x1300 / +0x18B0), the
negative/zero/positive selected-id split, the two mode lookups, main-menu ids
2/3/6/other, null and non-null demon results with both +0x4B values, the
sub_menu_state == 6 reset block, the signed display-state downgrade at 0/1/2
and a negative word, and the GetActiveMode == 2 refresh.
"""

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
FUNC_ADDR = 0x00258C58
FUNC_SIZE = 480

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00020000
INFO_ADDR = 0x00700000
INFO_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
GMGR_ADDR = 0x0044E000
GMGR_SIZE = 0x00001000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; the stubs live at the same addresses.
STUB_215A60 = 0x00215A60
STUB_2E2F3C = 0x002E2F3C
STUB_29AD98 = 0x0029AD98
STUB_29CB94 = 0x0029CB94
STUB_2B0824 = 0x002B0824
STUB_26AC34 = 0x0026AC34
STUB_26ABE0 = 0x0026ABE0
STUB_293E4C = 0x00293E4C
STUB_215990 = 0x00215990
STUB_2CF4E0 = 0x002CF4E0
STUB_1EE5A4 = 0x001EE5A4
STUB_1EE7C8 = 0x001EE7C8
STUB_293D50 = 0x00293D50
STUB_26B0CC = 0x0026B0CC

# Substring -> stub address, matched against the relocation symbol name.
RELOC_TARGETS = {
    "00215a60": STUB_215A60,
    "002e2f3c": STUB_2E2F3C,
    "0029ad98": STUB_29AD98,
    "0029cb94": STUB_29CB94,
    "002b0824": STUB_2B0824,
    "0026ac34": STUB_26AC34,
    "0026b0cc": STUB_26B0CC,
    "SetSubIdsA": STUB_26ABE0,
    "UpdateAffinityTable": STUB_293E4C,
    "SetPartyPrompt": STUB_215990,
    "UpdateHelpMessage": STUB_2CF4E0,
    "PopulateSkillList": STUB_1EE5A4,
    "PopulateItemList": STUB_1EE7C8,
    "GetActiveMode": STUB_293D50,
}

STUB_NAMES = {
    STUB_215A60: "script_vm_func_00215a60",
    STUB_2E2F3C: "func_002e2f3c",
    STUB_29AD98: "ui_func_0029ad98",
    STUB_29CB94: "script_vm_func_0029cb94",
    STUB_2B0824: "camp_func_002b0824",
    STUB_26AC34: "script_vm_func_0026ac34",
    STUB_26ABE0: "StatusDown_SetSubIdsA",
    STUB_293E4C: "Status_UpdateAffinityTable",
    STUB_215990: "StatusDown_SetPartyPrompt",
    STUB_2CF4E0: "StatusDown_UpdateHelpMessage",
    STUB_1EE5A4: "StatusDown_PopulateSkillList",
    STUB_1EE7C8: "StatusDown_PopulateItemList",
    STUB_293D50: "StatusDown_GetActiveMode",
    STUB_26B0CC: "func_0026b0cc",
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
CALLEE_SAVED_REGS = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def compile_candidate() -> bytes:
    out_dir = ROOT / "build/test_leaf_00258c58"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch41_c.o"
    src_file = ROOT / "src/engine/leaf_batch41_c.cpp"
    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00258c58" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"ui_func_00258c58 not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29, 10):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for token, address in RELOC_TARGETS.items():
            if token in rel.symbol_name:
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


def build_work(case: dict) -> bytes:
    buf = bytearray(((i * 37 + 0x5B) & 0xFF) for i in range(WORK_SIZE))
    struct.pack_into("<h", buf, 0x1300, case.get("selected", 0))
    struct.pack_into("<h", buf, 0x18B0, case.get("panel_b", 0))
    for base in (0x1300, 0x18B0):
        struct.pack_into("<H", buf, base + 0x02, case.get("threshold", 0x1234))
        ids = case.get("exclude", (0, 0, 0, 0, 0, 0, 0, 0))
        for i, value in enumerate(ids):
            struct.pack_into("<H", buf, base + 0x48 + i * 2, value & 0xFFFF)
        for i in range(16):
            buf[base + 0x3A + i] = (0xC0 + i) & 0xFF
        buf[base + 0x58] = 0x58
        buf[base + 0x98] = 0x98
    struct.pack_into("<I", buf, 0x12E4, case.get("display_state", 0) & 0xFFFFFFFF)
    buf[0x1E66] = case.get("main_menu", 0) & 0xFF
    buf[0x1E67] = case.get("sub_menu", 0) & 0xFF
    buf[0x1E63] = case.get("flag_1e63", 0) & 0xFF
    return bytes(buf)


def build_manager(work_ptr: int) -> bytes:
    buf = bytearray(((i * 11 + 0x40) & 0xFF) for i in range(GMGR_SIZE))
    buf[0x140] = 3  # ref_count (StatusManager at 0x0044E140)
    struct.pack_into("<I", buf, 0x144, work_ptr)
    return bytes(buf)


def build_info(case: dict) -> bytes:
    buf = bytearray(((i * 13 + 0x21) & 0xFF) for i in range(INFO_SIZE))
    buf[0x4B] = case.get("demon_flag", 0) & 0xFF
    return bytes(buf)


class Runner:
    """One Unicorn machine with stubs at the original call-target addresses."""

    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GMGR_ADDR, GMGR_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(INFO_ADDR, INFO_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address)

        self.call_log = []
        self.fixture = {}

    @staticmethod
    def _read_u16_array(uc, address, count=8):
        if address == 0:
            return None
        return struct.unpack(f"<{count}H", bytes(uc.mem_read(address, count * 2)))

    def _log(self, address, *args):
        self.call_log.append((STUB_NAMES[address], args))

    def _on_stub(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_215A60:
            self._log(address, r0 - WORK_ADDR, r1)
        elif address == STUB_2E2F3C:
            self._log(address, r0 - WORK_ADDR, r1)
        elif address == STUB_29AD98:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["ad98"])
        elif address == STUB_29CB94:
            self._log(address, r0)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["cb94"])
        elif address == STUB_2B0824:
            self._log(address, r0 & 0xFFFF)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["demon_ptr"])
        elif address == STUB_26AC34:
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            stack_arg = struct.unpack("<I", bytes(uc.mem_read(sp, 4)))[0]
            self._log(address, r0, r1, self._read_u16_array(uc, r2), stack_arg)
            count = self.fixture["count"]
            writable = count if 0 <= count <= 8 else 0
            for i in range(writable):
                uc.mem_write(r3 + i * 2, struct.pack("<H", (r0 * 3 + 0x1000 + i) & 0xFFFF))
            uc.reg_write(arm.UC_ARM_REG_R0, count)
        elif address == STUB_26ABE0:
            self._log(address, self._read_u16_array(uc, r0), r1)
        elif address == STUB_293E4C:
            self._log(address)
            # Real body sets StatusWork::flag_1e63 = 1 through the manager.
            work = struct.unpack(
                "<I", bytes(uc.mem_read(GMGR_ADDR + 0x144, 4))
            )[0]
            if work:
                uc.mem_write(work + 0x1E63, b"\x01")
        elif address == STUB_215990:
            self._log(address, r0 - WORK_ADDR, self._read_u16_array(uc, r0))
        elif address == STUB_2CF4E0:
            self._log(address, struct.unpack("<i", struct.pack("<I", r0))[0])
        elif address == STUB_1EE5A4:
            self._log(address, r0 - WORK_ADDR)
        elif address == STUB_1EE7C8:
            self._log(address, r0 - WORK_ADDR)
        elif address == STUB_293D50:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.fixture["active_mode"])
        elif address == STUB_26B0CC:
            self._log(address)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x6B0CC)
        else:
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict):
        self.call_log = []
        self.fixture = {
            "ad98": case.get("ad98", 8),
            "cb94": case.get("cb94", 8),
            "demon_ptr": INFO_ADDR if case.get("demon_ptr", 0) else 0,
            "count": case.get("count", 0),
            "active_mode": case.get("active_mode", 0),
        }

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(GMGR_ADDR, build_manager(WORK_ADDR))
        self.uc.mem_write(INFO_ADDR, build_info(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("next_panel", 0))
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED_REGS[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED_REGS.items()
            },
            "call_log": list(self.call_log),
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "manager": bytes(self.uc.mem_read(GMGR_ADDR, GMGR_SIZE)),
            "info": bytes(self.uc.mem_read(INFO_ADDR, INFO_SIZE)),
        }


def compare(orig: dict, cand: dict):
    problems = []
    for key in ("r0", "pc", "sp", "callee_saved", "call_log", "work", "manager", "info"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    return problems


def make_cases():
    cases = [
        {
            # Panel base +0x1300; selected id 0 keeps the default mode 8 and
            # neither the sub-id build nor either panel-state block runs.
            "name": "selected 0, default mode 8, no panel block",
            "next_panel": 0,
            "selected": 0,
            "main_menu": 0,
            "sub_menu": 0,
            "display_state": 5,
        },
        {
            # Positive id runs the sub-id build; main menu 0 skips the demon test.
            "name": "selected 1, menu 0, count 2, active 0",
            "next_panel": 0,
            "selected": 1,
            "threshold": 0x2222,
            "exclude": (1, 2, 3, 4, 5, 6, 7, 8),
            "main_menu": 0,
            "display_state": 0,
            "count": 2,
            "active_mode": 0,
        },
        {
            # Max positive id, menu 2 with a null demon, count 0, active 2.
            "name": "selected 32767, menu 2, null demon, count 0, active 2",
            "next_panel": 0,
            "selected": 0x7FFF,
            "main_menu": 2,
            "display_state": 0,
            "demon_ptr": 0,
            "count": 0,
            "active_mode": 2,
        },
        {
            # Negative id: lookup returns 16, display state 2 is downgraded.
            "name": "selected -1, ad98 mode 16, display 2 -> 1 + update",
            "next_panel": 0,
            "selected": -1,
            "ad98": 16,
            "main_menu": 0,
            "display_state": 2,
        },
        {
            # Display state exactly 1 must not be downgraded (strict > 1).
            "name": "selected -32768, display 1 unchanged",
            "next_panel": 0,
            "selected": -32768,
            "ad98": 16,
            "main_menu": 0,
            "display_state": 1,
        },
        {
            # Signed compare: 0x80000000 is negative, so no downgrade/store.
            "name": "selected -1, display 0x80000000 signed boundary",
            "next_panel": 0,
            "selected": -1,
            "ad98": 0x10,
            "main_menu": 0,
            "display_state": 0x80000000,
        },
        {
            # Panel B selected, but its own value is 0: only the 0x18F8
            # trampoline and the null SetSubIdsA path run.  Main menu 6 keeps
            # the default mode.
            "name": "panel B value 0, menu 6, default mode 8",
            "next_panel": 1,
            "panel_b": 0,
            "selected": 0x1234,
            "main_menu": 6,
            "display_state": 0,
        },
        {
            # Panel B positive with menu 3 and a non-null demon flag: full
            # eight-id buffer and the +0x58/+0x98 list refreshes on panel B.
            "name": "panel B value 5, menu 3, demon flag 1, count 8",
            "next_panel": 1,
            "panel_b": 5,
            "selected": 0x10,
            "threshold": 0x00FF,
            "exclude": (9, 8, 7, 6, 5, 4, 3, 2),
            "main_menu": 3,
            "display_state": 0,
            "demon_ptr": 1,
            "demon_flag": 1,
            "count": 8,
            "active_mode": 0,
        },
        {
            # Panel B negative and sub_menu_state 6: reset block runs, then
            # the party prompt; display state is already 0 so no second update.
            "name": "panel B -3, sub_menu 6, display 3, menu 6",
            "next_panel": 1,
            "panel_b": -3,
            "selected": 0,
            "main_menu": 6,
            "sub_menu": 6,
            "display_state": 3,
        },
        {
            # Ordering: sub_menu reset to 0 while display state was 9, then the
            # positive-panel block sets it to 1 because active mode is 2.
            "name": "selected 1, sub_menu 6, display 9, active 2",
            "next_panel": 0,
            "selected": 1,
            "main_menu": 0,
            "sub_menu": 6,
            "display_state": 9,
            "count": 1,
            "active_mode": 2,
        },
        {
            # Positive id with main menu 6: the sub-id build is skipped but the
            # panel-positive block still runs (active 0 so no update).
            "name": "selected 5, menu 6, panel positive, active 0",
            "next_panel": 0,
            "selected": 5,
            "main_menu": 6,
            "display_state": 4,
            "active_mode": 0,
        },
        {
            # Mode returned as 0x1FF -> only the low byte (0xFF) is forwarded;
            # count 0x1FF sign-extends its low byte to -1 for SetSubIdsA.
            "name": "cb94 0x1FF masked to 0xFF, count 0x1FF -> -1",
            "next_panel": 0,
            "selected": 1,
            "main_menu": 0,
            "cb94": 0x1FF,
            "display_state": 0,
            "count": 0x1FF,
        },
        {
            # Mode lookup returns 0 and the demon exists but +0x4B is 0.
            "name": "selected 2, menu 3, demon flag 0, cb94 mode 0",
            "next_panel": 0,
            "selected": 2,
            "main_menu": 3,
            "cb94": 0,
            "display_state": 1,
            "demon_ptr": 1,
            "demon_flag": 0,
            "count": 4,
            "active_mode": 5,
        },
        {
            # Negative selected id, display state 2, but sub_menu_state 6 too:
            # reset block then the downgrade block both call the update helper.
            "name": "selected -2, sub_menu 6, display 2",
            "next_panel": 0,
            "selected": -2,
            "ad98": 0xFF00,
            "main_menu": 4,
            "sub_menu": 6,
            "display_state": 2,
        },
    ]
    return cases


def patch_word(code: bytes, offset: int, new_word: int) -> bytes:
    mutated = bytearray(code)
    struct.pack_into("<I", mutated, offset, new_word)
    return bytes(mutated)


def main():
    print("Testing ui_func_00258c58 (0x00258c58)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B (relocations resolved).")

    cases = make_cases()
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

    # Negative controls: mutate known instructions of the pinned original at
    # fixed offsets and require the same comparison to detect each change.
    print("\nNegative controls:")
    controls = [
        (
            "default mode 8 changed to 9",
            0x0C,  # mov r6, #8
            0xE3A06009,
            "selected 0, default mode 8, no panel block",
        ),
        (
            "main-menu == 6 test changed to == 5",
            0xB4,  # cmp r0, #6 (sub-id gate at 0x258D0C)
            0xE3500005,
            "selected 5, menu 6, panel positive, active 0",
        ),
        (
            "conditional display-state store made unconditional",
            0x16C,  # strgt r6, [r0, #0x2E4] at 0x258DC4
            0xE58062E4,
            "selected -1, display 0x80000000 signed boundary",
        ),
    ]
    by_name = {case["name"]: case for case in cases}
    for label, offset, word, case_name in controls:
        mutant = patch_word(orig_code, offset, word)
        case = by_name[case_name]
        baseline = Runner().run(orig_code, case)
        altered = Runner().run(mutant, case)
        assert compare(baseline, altered), f"negative control not detected: {label}"
        print(f"  [PASS] {label} is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED; "
          f"{len(controls)}/{len(controls)} negative controls detected.")


if __name__ == "__main__":
    main()
