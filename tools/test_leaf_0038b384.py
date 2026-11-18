#!/usr/bin/env python3
"""Differential test for aocApplication_func_0038b384 (0x0038b384) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "aoc.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0038b384"

FUNC_ADDR = 0x0038B384
FUNC_SIZE = 236

STUB_TEX_DESTROY = 0x0035311C
STUB_RELEASE_GLOBAL = 0x002B2520
STUB_FREE = 0x002C4360
STUB_ALLOC_ALIGN = 0x002C54F0
STUB_WORK_ZERO = 0x002C3B48
STUB_MEM_ALLOC = 0x002C23F8
STUB_TEX_CREATE = 0x003530F8
STUB_NOTIFY_CLOSE = 0x002BCE48

STUB_NAMES = {
    STUB_TEX_DESTROY: "AocTexture_Destroy",
    STUB_RELEASE_GLOBAL: "Aoc_ReleaseGlobal",
    STUB_FREE: "AsdMem_Free",
    STUB_ALLOC_ALIGN: "AsdMem_AllocAlign",
    STUB_WORK_ZERO: "AsdWork_Zero",
    STUB_MEM_ALLOC: "AsdMemory_func_002c23f8",
    STUB_TEX_CREATE: "AocTexture_Create",
    STUB_NOTIFY_CLOSE: "AsdFile_NotifyClose",
}

PTR_APP = 0x20000000
PTR_BUF = 0x20010000
PTR_OBJ = 0x20040000
PTR_NEW_HANDLE = 0x20050000
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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "aocApplication_func_0038b384" in name), None)
    if candidate is None:
        raise RuntimeError(f"aocApplication_func_0038b384 not found in {obj_file}")

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
        else:
            raise RuntimeError(f"Unhandled relocation type {rtype} for {sym_name}")
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "aoc.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"aoc_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"aoc_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_APP, 0x00060000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        *,
        init_handle: int,
        init_buffer: int,
        alloc_align_ok: bool,
        obj_alloc_ok: bool,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_APP, b"\x00" * 0x600)
        uc.mem_write(PTR_APP + 0x80, struct.pack("<I", 0x12345678))
        uc.mem_write(PTR_APP + 0x5A8, struct.pack("<II", init_handle, init_buffer))

        calls: list[tuple[str, tuple[int, ...]]] = []

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
            if address == STUB_TEX_DESTROY:
                calls.append(("destroy", (r0,)))
                ret_arm(None)
            elif address == STUB_RELEASE_GLOBAL:
                calls.append(("release_global", ()))
                ret_arm(None)
            elif address == STUB_FREE:
                calls.append(("free", (r0,)))
                ret_arm(None)
            elif address == STUB_ALLOC_ALIGN:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                flag = struct.unpack("<I", uc_inst.mem_read(sp, 4))[0]
                calls.append(("alloc_align", (r0, r1, r2, r3, flag)))
                ret_arm(PTR_BUF if alloc_align_ok else 0)
            elif address == STUB_WORK_ZERO:
                calls.append(("work_zero", (r0, r1)))
                ret_arm(None)
            elif address == STUB_MEM_ALLOC:
                calls.append(("mem_alloc", (r0,)))
                ret_arm(PTR_OBJ if obj_alloc_ok else 0)
            elif address == STUB_TEX_CREATE:
                calls.append(("tex_create", (r0, r1, r2, r3)))
                ret_arm(PTR_NEW_HANDLE)
            elif address == STUB_NOTIFY_CLOSE:
                calls.append(("notify_close", ()))
                ret_arm(None)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_R0, PTR_APP)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        end_handle, end_buf = struct.unpack("<II", uc.mem_read(PTR_APP + 0x5A8, 8))
        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "end_handle": end_handle,
            "end_buf": end_buf,
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "end_handle", "end_buf", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    cases = [
        ("fresh_ok", {"init_handle": 0, "init_buffer": 0, "alloc_align_ok": True, "obj_alloc_ok": True}),
        ("replace_existing", {"init_handle": 0x20004000, "init_buffer": 0x20005000, "alloc_align_ok": True, "obj_alloc_ok": True}),
        ("alloc_buf_fail", {"init_handle": 0, "init_buffer": 0, "alloc_align_ok": False, "obj_alloc_ok": True}),
        ("alloc_obj_fail", {"init_handle": 0, "init_buffer": 0, "alloc_align_ok": True, "obj_alloc_ok": False}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_destroy", "AocTexture_Destroy(app->texture_handle);", ""),
        ("drop_free", "AsdMem_Free(app->texture_buffer);", ""),
        ("drop_zero", "AsdWork_Zero(app->texture_buffer, 0x20000);", ""),
        ("drop_notify_close", "AsdFile_NotifyClose();\n        return;", "return;"),
        ("wrong_buf_size", "AsdMem_AllocAlign(0x10000, 0x100, 0, 0x20000, 1);", "AsdMem_AllocAlign(0x10000, 0x100, 0, 0x10000, 1);"),
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
        f"PASS: aocApplication_func_0038b384 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
