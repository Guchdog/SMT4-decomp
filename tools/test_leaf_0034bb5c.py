#!/usr/bin/env python3
"""Differential test for ui_func_0034bb5c (0x0034bb5c) with Unicorn ARM."""

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
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0034bb5c"

FUNC_ADDR = 0x0034BB5C
FUNC_SIZE = 444

STUB_VCALL = 0x00200100
STUB_297004 = 0x00297004
STUB_2C0BCC = 0x002C0BCC
STUB_2B73A4 = 0x002B73A4
STUB_2B740C = 0x002B740C

STUB_NAMES = {
    STUB_297004: "ui_func_00297004",
    STUB_2C0BCC: "engine_func_002c0bcc",
    STUB_2B73A4: "ui_func_002b73a4",
    STUB_2B740C: "ui_func_002b740c",
}

PTR_SELF = 0x20000000
PTR_DST = 0x20001000
PTR_P14 = 0x20002000
PTR_VTBL = 0x20003000
PTR_ARR = 0x20004000
PTR_CFG = 0x20005000
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
    candidate = next((val for name, val in funcs.items() if "ui_func_0034bb5c" in name), None)
    if candidate is None:
        raise RuntimeError(f"ui_func_0034bb5c not found in {obj_file}")

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
    obj = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    fs = text.index("extern \"C\" void ui_func_0034bb5c(")
    fe = text.index("\n}\n", fs) + 3
    body = text[fs:fe]
    if body.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"leaf_batch45_b_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"leaf_batch45_b_mutant_{name}.o"
    mutant_src.write_text(text[:fs] + body.replace(old, new, 1) + text[fe:], encoding="utf-8")
    res = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed:\n{res.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_SELF, 0x00010000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, *, count: int, rand_s: int, rand_a: int) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(PTR_SELF, b"\x00" * 0x40)
        struct.pack_into("<I", sbuf := bytearray(0x20), 0x04, PTR_DST)
        struct.pack_into("<I", sbuf, 0x14, PTR_P14)
        struct.pack_into("<I", sbuf, 0x18, PTR_ARR)
        struct.pack_into("<I", sbuf, 0x1C, PTR_CFG)
        uc.mem_write(PTR_SELF, bytes(sbuf))

        uc.mem_write(PTR_DST, b"\x00" * 0x60)
        uc.mem_write(PTR_P14, struct.pack("<I", PTR_VTBL))
        uc.mem_write(PTR_VTBL + 0x0C, struct.pack("<I", STUB_VCALL))
        uc.mem_write(PTR_ARR, b"\x00" * 0x200)

        cbuf = bytearray(0x40)
        struct.pack_into("<IIII", cbuf, 0x00, 0x11111111, 0x22222222, 0x33333333, 0x44444444)
        struct.pack_into("<ff", cbuf, 0x24, 1.5, 5.5)
        struct.pack_into("<iI", cbuf, 0x2C, count, 7)
        uc.mem_write(PTR_CFG, bytes(cbuf))

        calls: list[tuple[str, tuple[object, ...]]] = []

        def ret_arm(val: int | None = None) -> None:
            if val is not None:
                uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, address: int, _size: int, _user: object) -> None:
            r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
            if address == STUB_VCALL:
                calls.append(("vcall", (r0,)))
                ret_arm(None)
            elif address == STUB_297004:
                calls.append(("297004", (r0, r1)))
                ret_arm(rand_s)
            elif address == STUB_2C0BCC:
                calls.append(("2c0bcc", (r0,)))
                ret_arm(rand_a)
            elif address == STUB_2B73A4:
                s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_S0)))[0]
                calls.append(("2b73a4", (round(s0, 5),)))
                uc_inst.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 0.5))[0])
                ret_arm(None)
            elif address == STUB_2B740C:
                s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_S0)))[0]
                calls.append(("2b740c", (round(s0, 5),)))
                uc_inst.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", -0.25))[0])
                ret_arm(None)

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_VCALL, end=STUB_VCALL),
            *[uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=a, end=a) for a in STUB_NAMES],
        ]
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_R0, PTR_SELF)
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
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "dst": bytes(uc.mem_read(PTR_DST, 0x54)),
            "arr": bytes(uc.mem_read(PTR_ARR, max(0, count) * 0x50 + 0x50)),
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "dst", "arr", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    cases = [
        ("count_0", {"count": 0, "rand_s": 0, "rand_a": 0}),
        ("count_2", {"count": 2, "rand_s": 16384, "rand_a": 32768}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_vcall", "(*reinterpret_cast<void (**)(void*)>(vtbl + 0x0C))(p14);", ""),
        ("wrong_corner_off", "dst[0x4C / 4] = cfg[3];", "dst[0x4C / 4] = cfg[2];"),
        ("wrong_stride", "static_cast<u32>(i) * 0x50u", "static_cast<u32>(i) * 0x40u"),
        ("wrong_scale_const", "3.0517578125e-05f", "1.52587890625e-05f"),
        ("drop_vec_scale", "vec2[0] = vec2[0] * scale;", ""),
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
        f"PASS: ui_func_0034bb5c (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
