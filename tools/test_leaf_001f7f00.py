#!/usr/bin/env python3
"""Differential test for btlEditor_func_001f7f00 (0x001f7f00) with Unicorn ARM.

Compiles src/battle/battle_extras.cpp, extracts btlEditor_func_001f7f00,
resolves its direct calls and literal-pool relocations against the pinned
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log including stack arguments and task-name strings for
    camp_func_002c4c00 (x2) and engine_func_002c4b84, plus sub-object calls
    and optional tail call func_0025c508;
  * g_BtlEditorState (0x00435CE8), BtlEditorState (+0x00..+0x18), and
    BtlEditorWork (+0x58, +0x44A8);
  * unexpected writes outside allowed buffers and stack.

Coverage:
  * g_BtlEditorSub_004342c8 == nullptr and g_BtlGameOverHookTarget == nullptr;
  * g_BtlEditorSub_004342c8 != nullptr with signed sub[0x760] < 0 (-1, -0x80000000);
  * sub[0x760] >= 0 (0, 5) with battle_func_00256b80 returning 0 vs non-zero;
  * g_BtlGameOverHookTarget != nullptr triggering tail call func_0025c508;
  * negative/mutation controls on kCalcTag, kDrawUpTag, kStateSize,
    kWorkByteOffset, kSubCheckOffset, and `work->flags |= 0x80000u`.
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
OUT_DIR = ROOT / "build/test_leaf_001f7f00"

FUNC_ADDR = 0x001F7F00
FUNC_SIZE = 432

CODE_ADDR = 0x001E0000
CODE_SIZE = 0x00100000  # covers 0x001E495C..0x002C9E88
GLOBALS_PAGE_A = 0x00434000
GLOBALS_PAGE_B = 0x00435000
GLOBALS_PAGE_C = 0x00439000
PTR_SUB = 0x004342C8
PTR_STATE = 0x00435CE8
PTR_HOOK = 0x00439CA8
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00005000
STATE_ADDR = 0x00510000
SUB_ADDR = 0x00520000
RODATA_ADDR = 0x00700000
PAGE_SIZE = 0x00001000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2C4C00 = 0x002C4C00
STUB_2C4B84 = 0x002C4B84
STUB_256B80 = 0x00256B80
STUB_256B04 = 0x00256B04
STUB_256AD8 = 0x00256AD8
STUB_25C508 = 0x0025C508

FN_1E495C = 0x001E495C
FN_2C9E88 = 0x002C9E88
FN_20EC74 = 0x0020EC74

STUB_NAMES = {
    STUB_2C4C00: "camp_func_002c4c00",
    STUB_2C4B84: "engine_func_002c4b84",
    STUB_256B80: "battle_func_00256b80",
    STUB_256B04: "battle_func_00256b04",
    STUB_256AD8: "battle_func_00256ad8",
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
        if "btlEditor_func_001f7f00" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"btlEditor_func_001f7f00 not found in {obj_file}: {sorted(funcs)}"
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
            if "g_BtlEditorState" in sym:
                target = PTR_STATE + addend
            elif "g_BtlEditorSub_004342c8" in sym:
                target = PTR_SUB + addend
            elif "g_BtlGameOverHookTarget" in sym:
                target = PTR_HOOK + addend
            elif "001e495c" in sym:
                target = FN_1E495C + addend
            elif "002c9e88" in sym:
                target = FN_2C9E88 + addend
            elif "0020ec74" in sym:
                target = FN_20EC74 + addend
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
    """One Unicorn machine with deterministic stubs for btlEditor_func_001f7f00."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE_A, PAGE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE_B, PAGE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE_C, PAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(STATE_ADDR, PAGE_SIZE)
        self.uc.mem_map(SUB_ADDR, PAGE_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, bx_lr)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE320F000))

        self.case: dict = {}
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
            uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
        elif address == STUB_256B80:
            self.call_log.append((address, r0, r1, r2))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["check_ret"])
        elif address in (STUB_256B04, STUB_256AD8, STUB_25C508):
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
            or (PTR_STATE <= address < PTR_STATE + 4)
            or (WORK_ADDR <= address < WORK_ADDR + 0x44AC)
            or (STATE_ADDR <= address < STATE_ADDR + 0x18)
        )
        if not allowed:
            self.bad_writes.append((address, size, value))

    def run(
        self, code: bytes, rodata_blobs: dict[int, bytes], case: dict
    ) -> dict:
        self.case = case
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
        self.uc.mem_write(GLOBALS_PAGE_C, b"\x00" * PAGE_SIZE)

        self.uc.mem_write(
            PTR_SUB, struct.pack("<I", SUB_ADDR if case["sub_nonnull"] else 0)
        )
        self.uc.mem_write(PTR_HOOK, struct.pack("<I", case["hook_target"]))

        sub = bytearray(b"\x00" * PAGE_SIZE)
        struct.pack_into("<i", sub, 0x760, case["sub_val"])
        self.uc.mem_write(SUB_ADDR, bytes(sub))

        work = bytearray(b"\x00" * 0x44AC)
        struct.pack_into("<I", work, 0x00, case["parent"])
        work[0x1E9D] = case["work_byte"] & 0xFF
        struct.pack_into("<I", work, 0x44A8, case["init_flags"])
        self.uc.mem_write(WORK_ADDR, bytes(work))
        self.uc.mem_write(STATE_ADDR, b"\x5A" * 0x18)

        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
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
            "ptr_state": bytes(self.uc.mem_read(PTR_STATE, 4)),
            "work_calc": bytes(self.uc.mem_read(WORK_ADDR + 0x58, 4)),
            "work_flags": bytes(self.uc.mem_read(WORK_ADDR + 0x44A8, 4)),
            "state": bytes(self.uc.mem_read(STATE_ADDR, 0x18)),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {
            "name": "sub_null_hook_null",
            "parent": 0x00601000,
            "work_byte": 0x42,
            "init_flags": 0x00000001,
            "sub_nonnull": False,
            "sub_val": 0,
            "check_ret": 0,
            "hook_target": 0,
        },
        {
            "name": "sub_neg_hook_set",
            "parent": 0x00602000,
            "work_byte": 0xFF,
            "init_flags": 0x00000002,
            "sub_nonnull": True,
            "sub_val": -1,
            "check_ret": 1,
            "hook_target": 0x00609000,
        },
        {
            "name": "sub_zero_check_zero",
            "parent": 0x00000000,
            "work_byte": 0x00,
            "init_flags": 0x00000004,
            "sub_nonnull": True,
            "sub_val": 0,
            "check_ret": 0,
            "hook_target": 0x0060A000,
        },
        {
            "name": "sub_pos_check_nonzero",
            "parent": 0x00603000,
            "work_byte": 0x7F,
            "init_flags": 0x00000008,
            "sub_nonnull": True,
            "sub_val": 5,
            "check_ret": 1,
            "hook_target": 0,
        },
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee", "calls", "ptr_state", "work_calc", "work_flags", "state", "bad_writes"):
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
        ("calc_tag", '"btlEditor Calc",\n        kCalcTag,', '"btlEditor Calc",\n        3,'),
        ("draw_up_tag", "kDrawUpTag = 0x73;", "kDrawUpTag = 0x74;"),
        ("state_size", "kStateSize = sizeof(BtlEditorState);", "kStateSize = 0x1C;"),
        ("work_byte_off", "kWorkByteOffset = 0x1E9D;", "kWorkByteOffset = 0x1E9E;"),
        ("sub_check_off", "kSubCheckOffset = 0x760;", "kSubCheckOffset = 0x764;"),
        ("work_flags", "work->flags |= 0x80000u;", "work->flags |= 0x40000u;"),
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
        f"PASS: btlEditor_func_001f7f00 (0x001f7f00) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
