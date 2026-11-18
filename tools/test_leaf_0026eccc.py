#!/usr/bin/env python3
"""Differential test for engine_func_0026eccc (0x0026eccc) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0026eccc"

FUNC_ADDR = 0x0026ECCC
FUNC_SIZE = 464

PTR_OUT_N = 0x20000000
PTR_OUT_D = 0x20000100
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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = next((val for name, val in funcs.items() if "engine_func_0026eccc" in name), None)
    if candidate is None:
        raise RuntimeError(f"engine_func_0026eccc not found in {obj_file}")
    code_raw, relocs = candidate
    if relocs:
        raise RuntimeError(f"Unexpected relocations: {relocs}")
    return bytes(code_raw)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed:\n{res.stderr}\n{res.stdout}")
    return relocate_candidate(obj)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    fs = text.index("extern \"C\" void engine_func_0026eccc(")
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
        self.uc.mem_map(PTR_OUT_N, 0x00010000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        *,
        axis: int,
        vert_idx: int,
        ref_pt: tuple[float, float, float],
        a: tuple[float, float, float],
        b: tuple[float, float, float],
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(PTR_OUT_N, b"\x00" * 16)
        uc.mem_write(PTR_OUT_D, b"\x00" * 4)

        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_R0, axis)
        uc.reg_write(arm.UC_ARM_REG_R1, vert_idx)
        uc.reg_write(arm.UC_ARM_REG_R2, PTR_OUT_N)
        uc.reg_write(arm.UC_ARM_REG_R3, PTR_OUT_D)
        svals = ref_pt + a + b
        for idx, fv in enumerate(svals):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{idx}"), struct.unpack("<I", struct.pack("<f", fv))[0])

        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)

        nx, ny, nz = struct.unpack("<fff", uc.mem_read(PTR_OUT_N, 12))
        d = struct.unpack("<f", uc.mem_read(PTR_OUT_D, 4))[0]
        return {
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "out": (round(nx, 5), round(ny, 5), round(nz, 5), round(d, 5)),
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("sp", "callee", "out"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    cases = [
        ("axis0_v0_pos", {"axis": 0, "vert_idx": 0, "ref_pt": (5.0, 2.0, 3.0), "a": (1.0, 2.0, 3.0), "b": (4.0, 5.0, 1.0)}),
        ("axis0_v2", {"axis": 0, "vert_idx": 2, "ref_pt": (5.0, 2.0, 3.0), "a": (1.0, 2.0, 3.0), "b": (4.0, 5.0, 1.0)}),
        ("axis1_v1_neg", {"axis": 1, "vert_idx": 1, "ref_pt": (-5.0, -2.0, -3.0), "a": (1.0, 2.0, 3.0), "b": (4.0, 5.0, 2.0)}),
        ("axis1_v2", {"axis": 1, "vert_idx": 2, "ref_pt": (-5.0, -2.0, -3.0), "a": (1.0, 2.0, 3.0), "b": (4.0, 5.0, 2.0)}),
        ("axis2_v2_flip", {"axis": 2, "vert_idx": 2, "ref_pt": (1.0, 2.0, -4.0), "a": (1.0, 2.0, 3.0), "b": (4.0, 6.0, 5.0)}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_axis0_zero", "p0 = { 0.0f, ay, az };", "p0 = { ax, 0.0f, az };"),
        ("wrong_axis1_zero", "p0 = { ax, 0.0f, az };", "p0 = { 0.0f, ay, az };"),
        ("wrong_axis2_zero", "p0 = { ax, ay, 0.0f };", "p0 = { ax, 0.0f, az };"),
        ("drop_flip", "if (dist < 0.0f)", "if (false)"),
        ("wrong_d_sign", "f32 d = nx * pref.x + ny * pref.y + nz * pref.z;", "f32 d = -(nx * pref.x + ny * pref.y + nz * pref.z);"),
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
        f"PASS: engine_func_0026eccc (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
