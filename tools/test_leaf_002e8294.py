#!/usr/bin/env python3
"""Differential test for btlTargetSelect_Init (0x002e8294) with Unicorn ARM.

Compiles src/battle/btl_target_select.cpp, extracts btlTargetSelect_Init,
resolves its direct calls and literal-pool relocations against the pinned
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log across all 10+ call sites (including stack-passed
    arguments for engine_func_002c54f0, camp_func_002c4c00, engine_func_002c32f8,
    and engine_func_002bdb2c + VFP s0=1.0f);
  * parent_work (+0x00..+0x20), g_pBtlTargetSelectWork (0x00439C60),
    BtlTargetSelectWork (+0x00..+0xB8), and cursor_anim (+0x00..+0x60);
  * unexpected writes outside allowed buffers and stack.

Coverage:
  * both reticle and cursor allocations succeed (full init path);
  * reticle allocation returns nullptr, cursor allocation succeeds;
  * both reticle and cursor allocations return nullptr;
  * negative/mutation controls on kReticleSize, kCursorSize, kCursorInitY,
    kCalcTag, kListType, and kListTag.
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
SOURCE = ROOT / "src/battle/btl_target_select.cpp"
OUT_DIR = ROOT / "build/test_leaf_002e8294"

FUNC_ADDR = 0x002E8294
FUNC_SIZE = 604

CODE_ADDR = 0x002B0000
CODE_SIZE = 0x000A0000  # covers 0x002BDB2C..0x00349468
PTR_WORK = 0x00439C60
GLOBALS_PAGE = 0x00439000
PARENT_ADDR = 0x00500000
WORK_ADDR = 0x00510000
RETICLE_ADDR = 0x00520000
CURSOR_ADDR = 0x00530000
RODATA_ADDR = 0x00700000
PAGE_SIZE = 0x00001000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2C54F0 = 0x002C54F0
STUB_2C23F8 = 0x002C23F8
STUB_3431F4 = 0x003431F4
STUB_2C5F58 = 0x002C5F58
STUB_2C4C00 = 0x002C4C00
STUB_2C3344 = 0x002C3344
STUB_2C32F8 = 0x002C32F8
STUB_2BDB2C = 0x002BDB2C
STUB_2EB72C = 0x002EB72C

FN_CALC = 0x002E06BC
FN_DRAW_UP = 0x002F4AA4
FN_DTOR = 0x003093E8
FN_ELEM_CTOR = 0x00349468
ADDR_VTABLE = 0x00420504
ADDR_DESC = 0x00401844

STUB_NAMES = {
    STUB_2C54F0: "engine_func_002c54f0",
    STUB_2C23F8: "engine_func_002c23f8",
    STUB_3431F4: "ui_func_003431f4",
    STUB_2C5F58: "__aeabi_vec_ctor_nocookie_nodtor",
    STUB_2C4C00: "camp_func_002c4c00",
    STUB_2C3344: "engine_func_002c3344",
    STUB_2C32F8: "engine_func_002c32f8",
    STUB_2BDB2C: "engine_func_002bdb2c",
    STUB_2EB72C: "engine_func_002eb72c",
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
    if "__aeabi_vec_ctor_nocookie_nodtor" in symbol_name:
        return STUB_2C5F58
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "btlTargetSelect_Init" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"btlTargetSelect_Init not found in {obj_file}: {sorted(funcs)}"
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
            if "g_pBtlTargetSelectWork" in sym:
                target = PTR_WORK + addend
            elif "g_CursorAnimVtable_00420504" in sym:
                target = ADDR_VTABLE + addend
            elif "g_TargetSelectDesc_00401844" in sym:
                target = ADDR_DESC + addend
            elif "btlTargetSelect_Calc" in sym:
                target = FN_CALC + addend
            elif "btlTargetSelect_DrawUp" in sym:
                target = FN_DRAW_UP + addend
            elif "003093e8" in sym:
                target = FN_DTOR + addend
            elif "00349468" in sym:
                target = FN_ELEM_CTOR + addend
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
    obj_file = OUT_DIR / "btl_target_select.o"
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
    """One Unicorn machine with deterministic stubs for btlTargetSelect_Init."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(
            arm.UC_ARM_REG_C1_C0_2,
            self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2) | 0x00F00000,
        )
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE, PAGE_SIZE)
        self.uc.mem_map(PARENT_ADDR, PAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, PAGE_SIZE)
        self.uc.mem_map(RETICLE_ADDR, PAGE_SIZE)
        self.uc.mem_map(CURSOR_ADDR, PAGE_SIZE)
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

        if address == STUB_2C54F0:
            stack_args = struct.unpack("<1I", self.uc.mem_read(sp, 4))
            self.call_log.append((address, r0, r1, r2, r3, stack_args))
            uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        elif address == STUB_2C23F8:
            self.call_log.append((address, r0, r1))
            if r0 == 0x12C:
                uc.reg_write(arm.UC_ARM_REG_R0, RETICLE_ADDR if self.case["reticle_ok"] else 0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, CURSOR_ADDR if self.case["cursor_ok"] else 0)
        elif address == STUB_3431F4:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
        elif address == STUB_2C5F58:
            self.call_log.append((address, r0, r1, r2, r3))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)
            # Return cleanly from both ARM bl and Thumb blx
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            cpsr = uc.reg_read(arm.UC_ARM_REG_CPSR)
            if lr & 1:
                uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr | 0x20)
            else:
                uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr & ~0x20)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)
        elif address == STUB_2C4C00:
            stack_args = struct.unpack("<4I", self.uc.mem_read(sp, 16))
            self.call_log.append(
                (address, self._read_cstr(r0), r1, r2, r3, stack_args)
            )
            self.task_seq += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x00600000 + self.task_seq * 0x100)
        elif address == STUB_2C3344:
            self.call_log.append((address, r0))
        elif address == STUB_2C32F8:
            stack_args = struct.unpack("<7I", self.uc.mem_read(sp, 28))
            self.call_log.append((address, r0, r1, r2, r3, stack_args))
        elif address == STUB_2BDB2C:
            stack_args = struct.unpack("<1I", self.uc.mem_read(sp, 4))
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append((address, r0, r1, r2, r3, stack_args, s0))
        elif address == STUB_2EB72C:
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
            or (PARENT_ADDR <= address < PARENT_ADDR + 0x20)
            or (WORK_ADDR <= address < WORK_ADDR + 0xB8)
            or (CURSOR_ADDR <= address < CURSOR_ADDR + 0x60)
            or (PTR_WORK <= address < PTR_WORK + 4)
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
        self.uc.mem_write(GLOBALS_PAGE, b"\x00" * PAGE_SIZE)
        self.uc.mem_write(WORK_ADDR, b"\xEE" * 0xB8)
        self.uc.mem_write(CURSOR_ADDR, b"\xAA" * 0x60)

        parent = bytearray(b"\x11" * 0x20)
        struct.pack_into("<I", parent, 0x00, case["root_parent"])
        self.uc.mem_write(PARENT_ADDR, bytes(parent))

        self.uc.reg_write(arm.UC_ARM_REG_R0, PARENT_ADDR)
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
            "parent": bytes(self.uc.mem_read(PARENT_ADDR, 0x20)),
            "work": bytes(self.uc.mem_read(WORK_ADDR, 0xB8)),
            "cursor": bytes(self.uc.mem_read(CURSOR_ADDR, 0x60)),
            "ptr_work": bytes(self.uc.mem_read(PTR_WORK, 4)),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {
            "name": "full_init",
            "root_parent": 0x00601000,
            "reticle_ok": True,
            "cursor_ok": True,
        },
        {
            "name": "reticle_null_cursor_ok",
            "root_parent": 0x00602000,
            "reticle_ok": False,
            "cursor_ok": True,
        },
        {
            "name": "both_null",
            "root_parent": 0x00000000,
            "reticle_ok": False,
            "cursor_ok": False,
        },
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee", "calls", "parent", "work", "cursor", "ptr_work", "bad_writes"):
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
        ("reticle_size", "kReticleSize = 0x12C;", "kReticleSize = 0x130;"),
        ("cursor_size", "kCursorSize = 0x60;", "kCursorSize = 0x64;"),
        ("cursor_y", "kCursorInitY = 40.0f;", "kCursorInitY = 42.0f;"),
        ("calc_tag", "kCalcTag = 2;", "kCalcTag = 3;"),
        ("list_type", "kListType = 0x14;", "kListType = 0x15;"),
        ("list_tag", "kListTag = 0x71;", "kListTag = 0x72;"),
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
        f"PASS: btlTargetSelect_Init (0x002e8294) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
