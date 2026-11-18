#!/usr/bin/env python3
"""Differential test for AsdFile_func_0010d070 (0x0010d070) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "asd_file.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0010d070"

FUNC_ADDR = 0x0010D070
FUNC_SIZE = 272

STUB_WORK_ALLOC = 0x002C34A4
STUB_MEM_ALLOC = 0x002C23F8
STUB_HEAP_INIT = 0x002BCF34
STUB_THREAD_CREATE = 0x002BCE50
STUB_ABORT = 0x002C5468

STUB_NAMES = {
    STUB_WORK_ALLOC: "AsdWork_Alloc",
    STUB_MEM_ALLOC: "AsdMemory_func_002c23f8",
    STUB_HEAP_INIT: "AsdHeap_Init",
    STUB_THREAD_CREATE: "AsdThread_Create",
    STUB_ABORT: "AsdKernel_AbortOnFailure",
}

ADDR_GLOBAL = 0x00465000
ADDR_ENTRY = 0x00113D58
PTR_WORK_BUF = 0x20010000
PTR_HEAP_OBJ = 0x20020000
STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
    "r4": 0x00465010,  # Caller (0x0010250c) leaves r4 = &g_AsdFile.mutex
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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "AsdFile_func_0010d070" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdFile_func_0010d070 not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        off = rel.offset
        sym_name = rel.symbol_name
        rtype = rel.relocation_type
        if rtype in (28, 29):
            dst = _stub_address(sym_name)
            if dst is None:
                raise RuntimeError(f"Unhandled call relocation: {sym_name}")
            pc = FUNC_ADDR + off + 8
            disp = ((dst - pc) >> 2) & 0x00FFFFFF
            insn = struct.unpack_from("<I", code, off)[0]
            struct.pack_into("<I", code, off, (insn & 0xFF000000) | disp)
        elif rtype == 2:
            if "g_AsdFile" in sym_name:
                addend = struct.unpack_from("<I", code, off)[0]
                struct.pack_into("<I", code, off, ADDR_GLOBAL + addend)
            elif "AsdFile_func_00113d58" in sym_name:
                struct.pack_into("<I", code, off, ADDR_ENTRY)
            else:
                raise RuntimeError(f"Unhandled ABS32 relocation: {sym_name}")
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "asd_file.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"asd_file_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"asd_file_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_WORK_BUF, 0x00020000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, *, thread_res: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(ADDR_GLOBAL, b"\xFF" + b"\x00" * 0x40)
        uc.mem_write(PTR_HEAP_OBJ, b"\xAA" * 0x18)

        calls: list[tuple[str, tuple[object, ...]]] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
            if address == STUB_WORK_ALLOC:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
                calls.append(("work_alloc", (r0, r1, r2, r3, a4, a5)))
                ret_arm(PTR_WORK_BUF)
            elif address == STUB_MEM_ALLOC:
                calls.append(("mem_alloc", (r0,)))
                ret_arm(PTR_HEAP_OBJ)
            elif address == STUB_HEAP_INIT:
                uc_inst.mem_write(r0 + 8, struct.pack("<II", 0x400, 0x800))
                calls.append(("heap_init", (r0, r1, r2)))
                ret_arm(None)
            elif address == STUB_THREAD_CREATE:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                stack_sz, prio, proc = struct.unpack("<III", uc_inst.mem_read(sp, 12))
                desc = struct.unpack("<IIII", uc_inst.mem_read(r1, 16))
                ctx = struct.unpack("<I", uc_inst.mem_read(r3, 4))[0]
                calls.append(("thread_create", (r0, desc, r2, ctx, stack_sz, prio, proc)))
                ret_arm(thread_res)
            elif address == STUB_ABORT:
                calls.append(("abort", (r0,)))
                ret_arm(None)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        f00 = uc.mem_read(ADDR_GLOBAL, 1)[0]
        work_buf, heap = struct.unpack("<II", uc.mem_read(ADDR_GLOBAL + 0x14, 8))
        heap_head = struct.unpack("<IIIIB", uc.mem_read(PTR_HEAP_OBJ, 17))
        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "f00": f00,
            "work_buf": work_buf,
            "heap": heap,
            "heap_head": heap_head,
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "f00", "work_buf", "heap", "heap_head", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    cases = [
        ("ok_zero", {"thread_res": 0}),
        ("ok_class_00600000", {"thread_res": 0x80600001}),
        ("fail_negative", {"thread_res": 0x80000001}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_flag_clear", "g_AsdFile.field_00 = 0;", ""),
        ("wrong_work_size", "AsdWork_Alloc(0x100, 0x100, 0, 0x1000, 0x1000, 1);", "AsdWork_Alloc(0x100, 0x100, 0, 0x2000, 0x1000, 1);"),
        ("wrong_heap_init_size", "AsdHeap_Init(heap, g_AsdFile.work_buffer, 0x1000);", "AsdHeap_Init(heap, g_AsdFile.work_buffer, 0x2000);"),
        ("wrong_prio", "stack_size, 0x12, -2);", "stack_size, 0x13, -2);"),
        ("drop_status_mask", "if ((result & 0x07E00000) != 0x00600000 && result < 0)", "if (result < 0)"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, kw in cases:
            if compare(Runner().run(orig_bytes, **kw), Runner().run(mut_bytes, **kw)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: AsdFile_func_0010d070 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
