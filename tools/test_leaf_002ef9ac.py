#!/usr/bin/env python3
"""Differential test for SaveLoadProcess_Step (0x002ef9ac) with Unicorn ARM.

Compiles src/ui/save_load.cpp, extracts SaveLoadProcess_Step, resolves its
direct calls against the pinned target addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in Unicorn.
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
OUT_DIR = ROOT / "build" / "test_leaf_002ef9ac"

FUNC_ADDR = 0x002EF9AC
FUNC_SIZE = 420

MGR_ADDR = 0x0043E2F0

STUB_002C0AC8 = 0x002C0AC8
STUB_002C54F0 = 0x002C54F0
STUB_00247C64 = 0x00247C64
STUB_001A1BF8 = 0x001A1BF8
STUB_DISMISS = 0x002CED0C
STUB_0026B844 = 0x0026B844
STUB_002BCF58 = 0x002BCF58
STUB_0026B830 = 0x0026B830
STUB_002ADB40 = 0x002ADB40
STUB_002C0B94 = 0x002C0B94
STUB_0026B734 = 0x0026B734

STUB_NAMES = {
    STUB_002C0AC8: "ui_func_002c0ac8",
    STUB_002C54F0: "engine_func_002c54f0",
    STUB_00247C64: "SaveLoad_Thread_func_00247c64",
    STUB_001A1BF8: "script_vm_func_001a1bf8",
    STUB_DISMISS: "SearchWin_Dismiss",
    STUB_0026B844: "ui_func_0026b844",
    STUB_002BCF58: "ui_func_002bcf58",
    STUB_0026B830: "ui_func_0026b830",
    STUB_002ADB40: "ui_func_002adb40",
    STUB_002C0B94: "ui_func_002c0b94",
    STUB_0026B734: "ui_func_0026b734",
}

PTR_PROC = 0x20000000
PTR_BUF = 0x20010000
PTR_DST1 = 0x20040000
PTR_DST2 = 0x20041000
PTR_DST3 = 0x20042000
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


def _get_symbol_offset(obj_file: Path, sym_substr: str) -> int:
    data = obj_file.read_bytes()
    e_shoff, = struct.unpack_from("<I", data, 0x20)
    e_shentsize, e_shnum = struct.unpack_from("<HH", data, 0x2E)
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    for sh in sections:
        if sh[1] == 2:  # SHT_SYMTAB
            sym_off, sym_size, str_idx, entsize = sh[4], sh[5], sh[6], sh[9]
            str_off, str_size = sections[str_idx][4], sections[str_idx][5]
            strtab = data[str_off : str_off + str_size]
            for pos in range(0, sym_size, entsize):
                st_name, st_value = struct.unpack_from("<II", data, sym_off + pos)
                end = strtab.find(b"\x00", st_name)
                name = strtab[st_name:end].decode("utf-8", errors="replace")
                if sym_substr in name:
                    return st_value
    raise RuntimeError(f"Symbol containing {sym_substr!r} not found in {obj_file}")


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "SaveLoadProcess_Step" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"SaveLoadProcess_Step not found in {obj_file}")

    sym_offset = _get_symbol_offset(obj_file, "SaveLoadProcess_Step")
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
        elif rel.relocation_type == 2 and rel.symbol_name == "":  # switch jump table
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, FUNC_ADDR + (addend - sym_offset))
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "save_load.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
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


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_PROC, 0x50000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self, code: bytes, state: int, vm_ret: int = 0, dismiss_ret: int = 0
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(MGR_ADDR, b"\xAA\xBB\xCC\xDD")
        uc.mem_write(PTR_PROC, struct.pack("<IIIII", 0, state, PTR_BUF, 0, 7))
        uc.mem_write(PTR_DST3, b"\x00" * 0x10)
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
            if addr == STUB_002C0AC8:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_PROC)
            elif addr == STUB_002C54F0:
                sp0 = struct.unpack("<I", emu.mem_read(sp, 4))[0]
                calls.append((addr, r0, r1, r2, r3, sp0))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_BUF)
            elif addr == STUB_00247C64:
                sp0 = struct.unpack("<I", emu.mem_read(sp, 4))[0]
                calls.append((addr, r0, r1, r2, r3, sp0))
            elif addr == STUB_001A1BF8:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, vm_ret)
            elif addr == STUB_DISMISS:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, dismiss_ret)
            elif addr == STUB_0026B844:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_DST1)
            elif addr == STUB_0026B830:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_DST2)
            elif addr == STUB_002C0B94:
                calls.append((addr,))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_DST3)
            elif addr == STUB_002BCF58:
                calls.append((addr, r0, r1, r2))
            elif addr == STUB_002ADB40:
                calls.append((addr, r0, r1))
            elif addr == STUB_0026B734:
                calls.append((addr,))

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if MGR_ADDR <= addr < MGR_ADDR + 4:
                return
            if PTR_PROC <= addr < PTR_PROC + 0x18:
                return
            if PTR_DST3 <= addr < PTR_DST3 + 0x10:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_R0, 0x12345678)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=2000)
        for hook in hooks:
            uc.hook_del(hook)

        return {
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {
                name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
                for name in CALLEE_SAVED
            },
            "calls": calls,
            "proc": bytes(uc.mem_read(PTR_PROC, 0x18)),
            "mgr": bytes(uc.mem_read(MGR_ADDR, 4)),
            "dst3": bytes(uc.mem_read(PTR_DST3, 0x10)),
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["r0"] != cand["r0"]:
        diffs.append(f"r0: orig={orig['r0']:#x} cand={cand['r0']:#x}")
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls: orig={orig['calls']} cand={cand['calls']}")
    if orig["proc"] != cand["proc"]:
        diffs.append("proc memory mismatch")
    if orig["mgr"] != cand["mgr"]:
        diffs.append("mgr memory mismatch")
    if orig["dst3"] != cand["dst3"]:
        diffs.append("dst3 memory mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("state0", 0, 0, 0),
        ("state4", 4, 0, 0),
        ("state5_wait", 5, 0, 0),
        ("state5_dismiss", 5, 1, 1),
        ("state5_commit", 5, 1, 0),
        ("state6", 6, 0, 0),
        ("state7", 7, 0, 0),
    ]
    for label, st, vm_ret, dis_ret in cases:
        orig_res = Runner().run(orig_bytes, st, vm_ret, dis_ret)
        cand_res = Runner().run(cand_bytes, st, vm_ret, dis_ret)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_buf_size", "kBufferSize = 0x24DB0;", "kBufferSize = 0x24DB4;"),
        ("wrong_payload_size", "kPayloadSize = 0x24D28;", "kPayloadSize = 0x24D20;"),
        ("drop_dismiss_check", "if (SearchWin_Dismiss())", "if (false)"),
        ("wrong_mgr3_case6", "mgr[3] = 1;\n        mgr[0] = 1;", "mgr[3] = 0;\n        mgr[0] = 1;"),
        ("wrong_ret_case7", "mgr[3] = 0;\n        mgr[0] = 1;\n        return -1;", "mgr[3] = 0;\n        mgr[0] = 1;\n        return 0;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, st, vm_ret, dis_ret in cases:
            if compare(Runner().run(orig_bytes, st, vm_ret, dis_ret), Runner().run(mut_bytes, st, vm_ret, dis_ret)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: SaveLoadProcess_Step (0x002ef9ac) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
