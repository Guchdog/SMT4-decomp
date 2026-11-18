#!/usr/bin/env python3
"""Differential test for AsdTMSpr_func_00144fbc (0x00144fbc) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "asd_texture.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00144fbc"

FUNC_ADDR = 0x00144FBC
FUNC_SIZE = 416

STUB_GET_SIZE = 0x0014F3FC
STUB_WORK_ALLOC2 = 0x002BF798
STUB_BIND_10 = 0x0014F070
STUB_BIND_20 = 0x0014F30C
STUB_BIND_30 = 0x0014F1CC
STUB_FREE = 0x002C4360

STUB_NAMES = {
    STUB_GET_SIZE: "UiTMSpr_func_0014f3fc",
    STUB_WORK_ALLOC2: "engine_func_002bf798",
    STUB_BIND_10: "UiTMSpr_func_0014f070",
    STUB_BIND_20: "UiTMSpr_func_0014f30c",
    STUB_BIND_30: "UiTMSpr_func_0014f1cc",
    STUB_FREE: "AsdMem_Free",
}

PTR_SPRITE = 0x20000000
PTR_BUFFER = 0x20010000
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
    candidate = next((val for name, val in funcs.items() if "AsdTMSpr_func_00144fbc" in name), None)
    if candidate is None:
        raise RuntimeError(f"AsdTMSpr_func_00144fbc not found in {obj_file}")

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
    obj = OUT_DIR / "asd_texture.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"asd_texture_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"asd_texture_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_SPRITE, 0x00020000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        *,
        kind_byte: int,
        flags: int,
        arg2: int,
        size_ret: int,
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_SPRITE, bytes([kind_byte]) + b"\x00" * 63)

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
            if address == STUB_GET_SIZE:
                calls.append(("get_size", (r0,)))
                ret_arm(size_ret)
            elif address == STUB_WORK_ALLOC2:
                sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
                a4, a5 = struct.unpack("<II", uc_inst.mem_read(sp, 8))
                calls.append(("work_alloc2", (r0, r1, r2, r3, a4, a5)))
                ret_arm(PTR_BUFFER)
            elif address == STUB_BIND_10:
                calls.append(("bind_10", (r0, r1)))
                ret_arm(None)
            elif address == STUB_BIND_20:
                calls.append(("bind_20", (r0, r1)))
                ret_arm(None)
            elif address == STUB_BIND_30:
                calls.append(("bind_30", (r0, r1)))
                ret_arm(None)
            elif address == STUB_FREE:
                calls.append(("free", (r0,)))
                ret_arm(None)

        hooks = [uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES]
        uc.reg_write(arm.UC_ARM_REG_R0, PTR_SPRITE)
        uc.reg_write(arm.UC_ARM_REG_R1, flags)
        uc.reg_write(arm.UC_ARM_REG_R2, arg2)
        uc.reg_write(arm.UC_ARM_REG_R3, 0xDEADBEEF)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            for h in hooks:
                uc.hook_del(h)

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("ret", "sp", "callee", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    cases = [
        ("invalid_kind", {"kind_byte": 0x45, "flags": 0, "arg2": 0x11, "size_ret": 0x40}),
        ("zero_size", {"kind_byte": 0x12, "flags": 0, "arg2": 0x11, "size_ret": 0}),
        ("kind_10_flags_3", {"kind_byte": 0x15, "flags": 3, "arg2": 0x77, "size_ret": 0x80}),
        ("kind_20_flags_1", {"kind_byte": 0x25, "flags": 1, "arg2": 0x88, "size_ret": 0x40}),
        ("kind_30_flags_2", {"kind_byte": 0x35, "flags": 2, "arg2": 0x99, "size_ret": 0x60}),
        ("kind_10_flags_0", {"kind_byte": 0x10, "flags": 0, "arg2": 0x11, "size_ret": 0x20}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_invalid_ret", "if (kind != 0x10u && kind != 0x20u && kind != 0x30u) {\n        return sprite;\n    }", "if (kind != 0x10u && kind != 0x20u && kind != 0x30u) {\n        return nullptr;\n    }"),
        ("wrong_zero_ret", "if (size == 0) {\n        return sprite;\n    }", "if (size == 0) {\n        return nullptr;\n    }"),
        ("wrong_arena", "const u32 arena = ((flags & 1u) != 0) ? 0x10000u : 0x100u;", "const u32 arena = 0x100u;"),
        ("wrong_alloc_flag", "const u32 alloc_flag = ((flags & 2u) != 0) ? 0u : 1u;", "const u32 alloc_flag = 1u;"),
        ("drop_free", "AsdMem_Free(sprite);", ""),
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
        f"PASS: AsdTMSpr_func_00144fbc (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
