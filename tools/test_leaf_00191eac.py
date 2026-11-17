#!/usr/bin/env python3
"""Differential test for saveLoadUI_Init (0x00191eac) with Unicorn ARM.

Compiles src/ui/save_load.cpp, extracts saveLoadUI_Init, resolves its calls,
globals, and string literal against the pinned target addresses, and runs the
pinned original (extracted/exefs/code.bin) against the candidate in Unicorn.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log (stub address, args, stack args, task name string);
  * g_SaveLoadUIManager.work and allocated SaveLoadUIWork (+0x00..+0x388);
  * unexpected writes outside g_SaveLoadUIManager, work, and stack.
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

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "ui" / "save_load.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00191eac"

FUNC_ADDR = 0x00191EAC
FUNC_SIZE = 208

G_SAVE_LOAD_MGR_ADDR = 0x0044DE28
FUNC_001C8D28 = 0x001C8D28
FUNC_00214960 = 0x00214960

STUB_ALLOC = 0x002C4B84
STUB_CREATE_CALC = 0x002C5978

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_CREATE_CALC: "AsdTask_CreateCalc",
}

PTR_WORK = 0x20000000
WORK_SIZE = 0x388
PTR_TASK = 0x20010000
PTR_RODATA = 0x00500000
STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
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


def _stub_address(symbol_name: str) -> int | None:
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def _extract_rodata_str(obj_file: Path) -> bytes:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr_off, shstr_size = sections[e_shstrndx][4], sections[e_shstrndx][5]
    shstr = data[shstr_off : shstr_off + shstr_size]
    for sh in sections:
        end = shstr.find(b"\x00", sh[0])
        name = shstr[sh[0] : end].decode("utf-8", errors="replace")
        if name == ".rodata.str1.1":
            return data[sh[4] : sh[4] + sh[5]]
    return b""


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "saveLoadUI_Init" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"saveLoadUI_Init not found in {obj_file}")

    rodata = _extract_rodata_str(obj_file)
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
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_SaveLoadUIManager" in rel.symbol_name:
                target = G_SAVE_LOAD_MGR_ADDR + addend
            elif "func_001c8d28" in rel.symbol_name:
                target = FUNC_001C8D28 + addend
            elif "func_00214960" in rel.symbol_name:
                target = FUNC_00214960 + addend
            elif rel.symbol_name == "" or rel.symbol_name.startswith(".L.str") or rel.symbol_name == ".rodata.str1.1":
                target = PTR_RODATA + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {rel.symbol_name!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name!r}"
            )
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "save_load.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"save_load_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"save_load_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed: {result.stderr}")
    return relocate_candidate(mutant_obj)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    raw = bytes(uc.mem_read(addr, 32))
    end = raw.find(b"\x00")
    return raw[:end].decode("ascii", errors="replace") if end >= 0 else raw.decode("ascii", errors="replace")


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_RODATA, 0x10000)
        self.uc.mem_map(PTR_WORK, 0x20000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, rodata: bytes, prefill: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)
        if rodata:
            uc.mem_write(PTR_RODATA, rodata)

        uc.mem_write(G_SAVE_LOAD_MGR_ADDR, b"\x00" * 0x14)
        uc.mem_write(PTR_WORK, bytes([prefill & 0xFF]) * WORK_SIZE)
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            uc.mem_write(addr, bx_lr)
        uc.mem_write(LR_SENTINEL, bx_lr)

        calls: list[tuple[object, ...]] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            r3 = emu.reg_read(arm.UC_ARM_REG_R3)
            sp = emu.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_ALLOC:
                sp0 = struct.unpack("<I", emu.mem_read(sp, 4))[0]
                calls.append((addr, r0, r1, r2, r3, sp0))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_WORK)
            elif addr == STUB_CREATE_CALC:
                sp0, sp4, sp8 = struct.unpack("<III", emu.mem_read(sp, 12))
                calls.append((addr, read_cstr(emu, r0), r1, r2, r3, sp0, sp4, sp8))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_TASK)

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if G_SAVE_LOAD_MGR_ADDR <= addr < G_SAVE_LOAD_MGR_ADDR + 0x14:
                return
            if PTR_WORK <= addr < PTR_WORK + WORK_SIZE:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=1000)
        for hook in hooks:
            uc.hook_del(hook)

        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {
                name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
                for name in CALLEE_SAVED
            },
            "calls": calls,
            "mgr": bytes(uc.mem_read(G_SAVE_LOAD_MGR_ADDR, 0x14)),
            "work": bytes(uc.mem_read(PTR_WORK, WORK_SIZE)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls: orig={orig['calls']} cand={cand['calls']}")
    if orig["mgr"] != cand["mgr"]:
        diffs.append("g_SaveLoadUIManager mismatch")
    if orig["work"] != cand["work"]:
        diffs.append("work memory mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()
    cases = [("prefill_00", 0x00), ("prefill_aa", 0xAA)]
    for label, prefill in cases:
        orig_res = Runner().run(orig_bytes, b"", prefill)
        cand_res = Runner().run(cand_bytes, cand_rodata, prefill)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_alloc_align", "AsdMem_Alloc(0x10000, 0x100, 0, sizeof(SaveLoadUIWork), 1));\n    g_SaveLoadUIManager.work = work;", "AsdMem_Alloc(0x20000, 0x100, 0, sizeof(SaveLoadUIWork), 1));\n    g_SaveLoadUIManager.work = work;"),
        ("wrong_task_name", '"BOOT C"', '"BOOT X"'),
        ("wrong_task_cb", "func_001c8d28,", "nullptr,"),
        ("wrong_state", "work->state = 0x11;", "work->state = 0x10;"),
        ("wrong_sub_state", "work->sub_state = 0;", "work->sub_state = 1;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, prefill in cases:
            if compare(Runner().run(orig_bytes, b"", prefill), Runner().run(mut_bytes, mut_rodata, prefill)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: saveLoadUI_Init (0x00191eac) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
