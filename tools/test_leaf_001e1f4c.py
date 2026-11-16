#!/usr/bin/env python3
"""Differential test for btlDebug_func_001e1f4c (0x001e1f4c) with Unicorn ARM.

Compiles src/battle/battle_extras.cpp, extracts btlDebug_func_001e1f4c,
resolves its direct calls and literal-pool relocations against the pinned
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log including stack arguments and task-name strings for
    camp_func_002c4c00 (x3) and engine_func_002c4b84, plus both arg!=null
    (list creation/setup) and arg==null (battle_func_003c5378) branches and
    optional tail call func_0025c508;
  * BtlDebugWork (+0x5C, +0x44A8), g_BtlDebugState (0x00434388..+0x0C), and
    allocated 0x20-byte debug block;
  * unexpected writes outside allowed buffers and stack.

Coverage:
  * arg == nullptr with g_BtlGameOverHookTarget == nullptr;
  * arg == nullptr with g_BtlGameOverHookTarget != nullptr;
  * arg != nullptr with g_BtlGameOverHookTarget == nullptr;
  * arg != nullptr with g_BtlGameOverHookTarget != nullptr;
  * negative/mutation controls on kDrawUpTag, kDrawDownTag, kDebugBlockSize,
    kListCount, `work->flags |= 1u`, and `if (arg != nullptr)`.
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
SOURCE = ROOT / "src/battle/battle_extras.cpp"
OUT_DIR = ROOT / "build/test_leaf_001e1f4c"

FUNC_ADDR = 0x001E1F4C
FUNC_SIZE = 504

CODE_ADDR = 0x001D0000
CODE_SIZE = 0x00200000  # covers 0x001D3CA4..0x003C5378
GLOBALS_PAGE_A = 0x00434000
GLOBALS_PAGE_B = 0x00439000
PTR_DBG_STATE = 0x00434388
ADDR_ITEMS = 0x00434588
ADDR_TITLE = 0x00400534
PTR_HOOK = 0x00439CA8
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00005000
DBG_BLOCK_ADDR = 0x00510000
LIST_ADDR = 0x00520000
RODATA_ADDR = 0x00700000
PAGE_SIZE = 0x00001000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2C4C00 = 0x002C4C00
STUB_2C4B84 = 0x002C4B84
STUB_25C7C4 = 0x0025C7C4
STUB_25C550 = 0x0025C550
STUB_25C524 = 0x0025C524
STUB_262B40 = 0x00262B40
STUB_3C5378 = 0x003C5378
STUB_25C508 = 0x0025C508

FN_21EB38 = 0x0021EB38
FN_1D3CA4 = 0x001D3CA4
FN_1FC51C = 0x001FC51C
FN_21EBE0 = 0x0021EBE0

STUB_NAMES = {
    STUB_2C4C00: "camp_func_002c4c00",
    STUB_2C4B84: "engine_func_002c4b84",
    STUB_25C7C4: "battle_func_0025c7c4",
    STUB_25C550: "AsdListBox_func_0025c550",
    STUB_25C524: "battle_func_0025c524",
    STUB_262B40: "battle_func_00262b40",
    STUB_3C5378: "battle_func_003c5378",
    STUB_25C508: "func_0025c508",
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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def elf_rodata(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + index * e_shentsize)
        for index in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        if name.startswith(".rodata"):
            result[name] = data[section[4] : section[4] + section[5]]
    return result


def _stub_address(symbol_name: str) -> int | None:
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "btlDebug_func_001e1f4c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"btlDebug_func_001e1f4c not found in {obj_file}: {sorted(funcs)}"
        )

    rodata_sections = elf_rodata(obj_file)
    rodata_blobs: dict[int, bytes] = {}
    rodata_bases: dict[str, int] = {}
    cursor = RODATA_ADDR
    for sec_name, blob in sorted(rodata_sections.items()):
        if blob:
            rodata_bases[sec_name] = cursor
            rodata_blobs[cursor] = blob
            cursor += (len(blob) + 0xFF) & ~0xFF

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = _stub_address(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            sym = rel.symbol_name
            if "g_BtlDebugState" in sym:
                target = PTR_DBG_STATE + addend
            elif "g_DebugMenuItems_00434588" in sym:
                target = ADDR_ITEMS + addend
            elif "g_DebugMenuTitle_00400534" in sym:
                target = ADDR_TITLE + addend
            elif "g_BtlGameOverHookTarget" in sym:
                target = PTR_HOOK + addend
            elif "0021eb38" in sym:
                target = FN_21EB38 + addend
            elif "001d3ca4" in sym:
                target = FN_1D3CA4 + addend
            elif "001fc51c" in sym:
                target = FN_1FC51C + addend
            elif "0021ebe0" in sym:
                target = FN_21EBE0 + addend
            elif sym in rodata_bases:
                target = rodata_bases[sym] + addend
            elif ".rodata" in sym or sym == "":
                base = rodata_bases.get(".rodata.str1.1") or next(iter(rodata_bases.values()))
                target = base + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {sym!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code), rodata_blobs


def compile_candidate() -> tuple[bytes, dict[int, bytes]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "battle_extras.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(
    name: str, old: str, new: str
) -> tuple[bytes, dict[int, bytes]]:
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


class Runner:
    """One Unicorn machine with deterministic stubs for btlDebug_func_001e1f4c."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE_A, PAGE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE_B, PAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(DBG_BLOCK_ADDR, PAGE_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, bx_lr)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE320F000))

        self.task_seq = 0
        self.call_log: list[tuple] = []
        self.bad_writes: list[tuple[int, int, int]] = []

        for addr in STUB_NAMES:
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, None, addr, addr)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _read_cstr(self, addr: int) -> bytes:
        raw = self.uc.mem_read(addr, 64)
        end = raw.find(b"\x00")
        return bytes(raw[:end] if end != -1 else raw)

    def _on_stub(
        self, uc: unicorn.Uc, address: int, size: int, user_data: object
    ) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)

        if address == STUB_2C4C00:
            stack_args = struct.unpack("<4I", self.uc.mem_read(sp, 16))
            self.call_log.append(
                (address, self._read_cstr(r0), r1, r2, r3, stack_args)
            )
            self.task_seq += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x00600000 + self.task_seq * 0x100)
        elif address == STUB_2C4B84:
            stack_args = struct.unpack("<1I", self.uc.mem_read(sp, 4))
            self.call_log.append((address, r0, r1, r2, r3, stack_args))
            uc.reg_write(arm.UC_ARM_REG_R0, DBG_BLOCK_ADDR)
        elif address == STUB_25C7C4:
            self.call_log.append((address, r0, r1, r2, r3))
            uc.reg_write(arm.UC_ARM_REG_R0, LIST_ADDR)
        elif address == STUB_25C550:
            self.call_log.append((address, r0, r1, r2))
        elif address in (STUB_25C524, STUB_262B40, STUB_3C5378, STUB_25C508):
            self.call_log.append((address, r0, r1))

    def _on_write(
        self,
        uc: unicorn.Uc,
        access: int,
        address: int,
        size: int,
        value: int,
        user_data: object,
    ) -> None:
        allowed = (
            (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            or (PTR_DBG_STATE <= address < PTR_DBG_STATE + 0x0C)
            or (WORK_ADDR <= address < WORK_ADDR + 0x44AC)
            or (DBG_BLOCK_ADDR <= address < DBG_BLOCK_ADDR + 0x20)
        )
        if not allowed:
            self.bad_writes.append((address, size, value))

    def run(
        self, code: bytes, rodata_blobs: dict[int, bytes], case: dict
    ) -> dict:
        self.task_seq = 0
        self.call_log = []
        self.bad_writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * max(FUNC_SIZE, len(code) + 16))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(RODATA_ADDR, b"\x00" * RODATA_SIZE)
        for base, blob in rodata_blobs.items():
            self.uc.mem_write(base, blob)

        self.uc.mem_write(STACK_ADDR, b"\xCD" * STACK_SIZE)
        self.uc.mem_write(GLOBALS_PAGE_A, b"\x00" * PAGE_SIZE)
        self.uc.mem_write(GLOBALS_PAGE_B, b"\x00" * PAGE_SIZE)
        self.uc.mem_write(PTR_DBG_STATE, b"\x5A" * 0x0C)
        self.uc.mem_write(PTR_HOOK, struct.pack("<I", case["hook_target"]))

        work = bytearray(b"\x00" * 0x44AC)
        struct.pack_into("<I", work, 0x00, case["parent"])
        struct.pack_into("<I", work, 0x44A8, case["init_flags"])
        self.uc.mem_write(WORK_ADDR, bytes(work))
        self.uc.mem_write(DBG_BLOCK_ADDR, b"\x77" * 0x20)

        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["arg"])
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000, count=200_000)

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "calls": list(self.call_log),
            "dbg_state": bytes(self.uc.mem_read(PTR_DBG_STATE, 0x0C)),
            "work_calc": bytes(self.uc.mem_read(WORK_ADDR + 0x5C, 4)),
            "work_flags": bytes(self.uc.mem_read(WORK_ADDR + 0x44A8, 4)),
            "dbg_block": bytes(self.uc.mem_read(DBG_BLOCK_ADDR, 0x20)),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {
            "name": "arg_null_hook_null",
            "parent": 0x00601000,
            "init_flags": 0x00000010,
            "arg": 0,
            "hook_target": 0,
        },
        {
            "name": "arg_null_hook_set",
            "parent": 0x00602000,
            "init_flags": 0x00000020,
            "arg": 0,
            "hook_target": 0x00609000,
        },
        {
            "name": "arg_nonnull_hook_null",
            "parent": 0x00000000,
            "init_flags": 0x00000000,
            "arg": 0x00604000,
            "hook_target": 0,
        },
        {
            "name": "arg_nonnull_hook_set",
            "parent": 0x00603000,
            "init_flags": 0x00000040,
            "arg": 0x00605000,
            "hook_target": 0x0060A000,
        },
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee", "calls", "dbg_state", "work_calc", "work_flags", "dbg_block", "bad_writes"):
        if orig[key] != cand[key]:
            diffs.append(f"{name}: {key} orig={orig[key]!r} cand={cand[key]!r}")
    if cand["sp"] != ENTRY_SP:
        diffs.append(f"{name}: sp not restored: {cand['sp']:#x}")
    if cand["callee"] != CALLEE_SAVED_START:
        diffs.append(f"{name}: callee-saved clobbered: {cand['callee']!r}")
    if cand["bad_writes"]:
        diffs.append(f"{name}: unexpected writes: {cand['bad_writes']!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    orig_runner = Runner()
    cand_runner = Runner()
    cases = build_cases()

    for case in cases:
        orig_res = orig_runner.run(orig_bytes, {}, case)
        cand_res = cand_runner.run(cand_bytes, cand_rodata, case)
        diffs = compare_outputs(case["name"], orig_res, cand_res)
        if diffs:
            for d in diffs:
                print("FAIL:", d)
            return 1

    mutants = [
        ("draw_up_tag", '"btlDebug DrawUp",\n        kDrawUpTag,', '"btlDebug DrawUp",\n        0x74,'),
        ("draw_down_tag", "kDrawDownTag = 0xE6;", "kDrawDownTag = 0xE7;"),
        ("dbg_block_size", "kDebugBlockSize = 0x20;", "kDebugBlockSize = 0x24;"),
        ("list_count", "kListCount = 0xB;", "kListCount = 0xC;"),
        ("work_flags", "work->flags |= 1u;", "work->flags |= 2u;"),
        ("arg_branch", "if (arg != nullptr)", "if (arg == nullptr)"),
    ]
    for m_name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(m_name, old, new)
        mut_runner = Runner()
        detected = False
        for case in cases:
            orig_res = orig_runner.run(orig_bytes, {}, case)
            mut_res = mut_runner.run(mut_bytes, mut_rodata, case)
            if compare_outputs(case["name"], orig_res, mut_res):
                detected = True
                break
        if not detected:
            print(f"FAIL: mutant {m_name} was not detected")
            return 1

    print(
        f"PASS: btlDebug_func_001e1f4c (0x001e1f4c) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
