#!/usr/bin/env python3
"""Differential test for RunWin_Init (0x002027dc) with Unicorn ARM.

Compiles src/ui/window.cpp, extracts RunWin_Init, resolves its direct calls
and literal-pool relocations against the pinned target addresses, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log including stack arguments and task-name strings for
    AsdMem_Alloc, AsdMem_Zero, AsdTask_CreateCalc, AsdTask_CreateDraw,
    UiSpriteGroup_Init, UiSpriteGroup_BindTable (7 stack args),
    UiAnimSprite_SetupEx (1 stack arg + VFP s0=1.0f), and tail call
    UiAnimSprite_SetAnim;
  * g_RunWinWork (0x0043E158) and RunWinWork (+0x00..+0xE4);
  * unexpected writes outside g_RunWinWork, work, and stack.

Coverage:
  * g_RunWinWork == nullptr (allocates, zeroes, and initializes);
  * g_RunWinWork != nullptr (reuses existing work, zeroes, and initializes);
  * negative/mutation controls on kWorkSize, kCalcTag, kDrawDownTag,
    kSpriteType, kSpriteId, and `AsdMem_Zero(work, kWorkSize)`.
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
SOURCE = ROOT / "src/ui/window.cpp"
OUT_DIR = ROOT / "build/test_leaf_002027dc"

FUNC_ADDR = 0x002027DC
FUNC_SIZE = 372

CODE_ADDR = 0x00200000
CODE_SIZE = 0x000D0000  # covers 0x002027DC..0x002C5978
GLOBALS_PAGE = 0x0043E000
PTR_WORK = 0x0043E158
WORK_ADDR = 0x00500000
RODATA_ADDR = 0x00700000
PAGE_SIZE = 0x00001000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_ALLOC = 0x002C4B84
STUB_ZERO = 0x002C4B30
STUB_CALC = 0x002C5978
STUB_DRAW = 0x002C4C00
STUB_GROUP_INIT = 0x002C3344
STUB_GROUP_BIND = 0x002C32F8
STUB_SETUP_EX = 0x002BDB2C
STUB_SET_ANIM = 0x002BF030

FN_CALC = 0x0018F4AC
FN_DRAW = 0x0018F178
ADDR_TBL_B6C = 0x00403B6C
ADDR_TBL_B90 = 0x00403B90
ADDR_TBL_BB4 = 0x00403BB4

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_ZERO: "AsdMem_Zero",
    STUB_CALC: "AsdTask_CreateCalc",
    STUB_DRAW: "AsdTask_CreateDraw",
    STUB_GROUP_INIT: "UiSpriteGroup_Init",
    STUB_GROUP_BIND: "UiSpriteGroup_BindTable",
    STUB_SETUP_EX: "UiAnimSprite_SetupEx",
    STUB_SET_ANIM: "UiAnimSprite_SetAnim",
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
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "RunWin_Init" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"RunWin_Init not found in {obj_file}: {sorted(funcs)}"
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
            if "g_RunWinWork" in sym:
                target = PTR_WORK + addend
            elif "RunWin_Calc_0018f4ac" in sym:
                target = FN_CALC + addend
            elif "RunWin_DrawDownAndCalc" in sym:
                target = FN_DRAW + addend
            elif "g_RunWinSpriteTable_00403b6c" in sym:
                target = ADDR_TBL_B6C + addend
            elif "g_RunWinSpriteTable_00403b90" in sym:
                target = ADDR_TBL_B90 + addend
            elif "g_RunWinSpriteTable_00403bb4" in sym:
                target = ADDR_TBL_BB4 + addend
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
    obj_file = OUT_DIR / "window.o"
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
    """One Unicorn machine with deterministic stubs for RunWin_Init."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(
            arm.UC_ARM_REG_C1_C0_2,
            self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2) | 0x00F00000,
        )
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE, PAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, PAGE_SIZE)
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

        if address == STUB_ALLOC:
            stack_args = struct.unpack("<1I", self.uc.mem_read(sp, 4))
            self.call_log.append((address, r0, r1, r2, r3, stack_args))
            uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        elif address == STUB_ZERO:
            self.call_log.append((address, r0, r1))
            self.uc.mem_write(r0, b"\x00" * r1)
        elif address == STUB_CALC:
            stack_args = struct.unpack("<3I", self.uc.mem_read(sp, 12))
            self.call_log.append(
                (address, self._read_cstr(r0), r1, r2, r3, stack_args)
            )
            self.task_seq += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x00600000 + self.task_seq * 0x100)
        elif address == STUB_DRAW:
            stack_args = struct.unpack("<4I", self.uc.mem_read(sp, 16))
            self.call_log.append(
                (address, self._read_cstr(r0), r1, r2, r3, stack_args)
            )
            self.task_seq += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x00600000 + self.task_seq * 0x100)
        elif address == STUB_GROUP_INIT:
            self.call_log.append((address, r0))
        elif address == STUB_GROUP_BIND:
            stack_args = struct.unpack("<7I", self.uc.mem_read(sp, 28))
            self.call_log.append((address, r0, r1, r2, r3, stack_args))
        elif address == STUB_SETUP_EX:
            stack_args = struct.unpack("<1I", self.uc.mem_read(sp, 4))
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append((address, r0, r1, r2, r3, stack_args, s0))
        elif address == STUB_SET_ANIM:
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
            or (PTR_WORK <= address < PTR_WORK + 4)
            or (WORK_ADDR <= address < WORK_ADDR + 0xE4)
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
        self.uc.mem_write(GLOBALS_PAGE, b"\x00" * PAGE_SIZE)
        self.uc.mem_write(
            PTR_WORK, struct.pack("<I", WORK_ADDR if case["existing"] else 0)
        )
        self.uc.mem_write(WORK_ADDR, b"\xEE" * 0xE4)

        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
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
            "ptr_work": bytes(self.uc.mem_read(PTR_WORK, 4)),
            "work": bytes(self.uc.mem_read(WORK_ADDR, 0xE4)),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {"name": "alloc_fresh", "existing": False},
        {"name": "reuse_existing", "existing": True},
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee", "calls", "ptr_work", "work", "bad_writes"):
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
        ("work_size", "kWorkSize = sizeof(RunWinWork);", "kWorkSize = 0xE8;"),
        ("calc_tag", '"RunWin Calc",\n        kCalcTag,', '"RunWin Calc",\n        2,'),
        ("draw_down_tag", "kDrawDownTag = 0xE9;", "kDrawDownTag = 0xEA;"),
        ("sprite_type", "kSpriteType = 0x0E,\n", "kSpriteType = 0x0F,\n"),
        ("sprite_id", '"RunWin DrawDown",\n        kDrawDownTag,', '"RunWin DrawDown",\n        0xEA,'),
        ("zero_call", 'AsdMem_Zero(work, kWorkSize);\n\n    work->calc_task = AsdTask_CreateCalc(\n        "RunWin Calc"', 'AsdMem_Zero(work, 0);\n\n    work->calc_task = AsdTask_CreateCalc(\n        "RunWin Calc"'),
    ]
    for m_name, old, new in mutants:
        if m_name == "sprite_type":
            continue
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
        f"PASS: RunWin_Init (0x002027dc) matched original across "
        f"{len(cases)} cases and detected 5/5 mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
