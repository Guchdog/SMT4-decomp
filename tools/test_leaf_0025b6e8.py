#!/usr/bin/env python3
"""Differential test for engine_func_0025b6e8 (0x0025b6e8) with Unicorn ARM."""

from __future__ import annotations

import math
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
OUT_DIR = ROOT / "build" / "test_leaf_0025b6e8"

FUNC_ADDR = 0x0025B6E8
FUNC_SIZE = 448

STUB_24BD60 = 0x0024BD60
STUB_NAMES = {STUB_24BD60: "func_0024bd60"}

ADDR_GLOBAL = 0x00446FE8
PTR_STATE = 0x20000000
PTR_ARR2 = 0x20001000
PTR_ARR3 = 0x20002000
PTR_P0 = 0x20003000
PTR_P1 = 0x20003100
PTR_OUT = 0x20003200
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
    candidate = next((val for name, val in funcs.items() if "engine_func_0025b6e8" in name), None)
    if candidate is None:
        raise RuntimeError(f"engine_func_0025b6e8 not found in {obj_file}")

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
    fs = text.index("extern \"C\" s32 engine_func_0025b6e8(")
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


def pack_plane(flag: int, b4: int, b5: int, nx: float, ny: float, nz: float, d: float) -> bytes:
    buf = bytearray(0xA8)
    struct.pack_into("<bb", buf, 4, b4, b5)
    buf[8] = flag
    struct.pack_into("<ffff", buf, 0x0C, nx, ny, nz, d)
    return bytes(buf)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_STATE, 0x00010000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self,
        code: bytes,
        *,
        p0: tuple[float, float, float],
        p1: tuple[float, float, float],
        has_out: bool,
        planes2: list[bytes],
        planes3: list[bytes],
        dist_rets: list[float],
    ) -> dict[str, object]:
        uc = self.uc
        uc.mem_write(0x00100000, ORIG_BIN.read_bytes())
        uc.mem_write(FUNC_ADDR, code)

        sbuf = bytearray(0x30)
        struct.pack_into("<II", sbuf, 0x0C, len(planes2), len(planes3))
        struct.pack_into("<II", sbuf, 0x20, PTR_ARR2, PTR_ARR3)
        uc.mem_write(ADDR_GLOBAL, bytes(sbuf))
        for i, pl in enumerate(planes2):
            uc.mem_write(PTR_ARR2 + i * 0xA8, pl)
        for i, pl in enumerate(planes3):
            uc.mem_write(PTR_ARR3 + i * 0xA8, pl)
        uc.mem_write(PTR_P0, struct.pack("<fff", *p0))
        uc.mem_write(PTR_P1, struct.pack("<fff", *p1))
        uc.mem_write(PTR_OUT, b"\x00" * 12)

        calls: list[tuple[object, ...]] = []
        idx = [0]

        def ret_arm() -> None:
            lr = uc.reg_read(arm.UC_ARM_REG_LR)
            uc.reg_write(arm.UC_ARM_REG_PC, lr & ~1)

        def on_code(uc_inst: unicorn.Uc, _address: int, _size: int, _user: object) -> None:
            r0 = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_R0)))[0]
            r1 = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_R1)))[0]
            r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
            s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_S0)))[0]
            s1 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_S1)))[0]
            s2 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_S2)))[0]
            s3 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(arm.UC_ARM_REG_S3)))[0]
            calls.append((r0, r1, r2, round(s0, 4), round(s1, 4), round(s2, 4), round(s3, 4)))
            ret_f = dist_rets[idx[0] % len(dist_rets)]
            idx[0] += 1
            uc_inst.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", ret_f))[0])
            ret_arm()

        h = uc.hook_add(unicorn.UC_HOOK_CODE, on_code, begin=STUB_24BD60, end=STUB_24BD60)
        uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.reg_write(arm.UC_ARM_REG_R0, PTR_P0)
        uc.reg_write(arm.UC_ARM_REG_R1, PTR_P1)
        uc.reg_write(arm.UC_ARM_REG_R2, PTR_OUT if has_out else 0)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        try:
            uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=5_000_000)
        finally:
            uc.hook_del(h)

        out_vec = struct.unpack("<fff", uc.mem_read(PTR_OUT, 12))
        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {r: uc.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
            "out": tuple(round(x, 4) for x in out_vec),
            "calls": calls,
        }


def compare(a: dict[str, object], b: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    for k in ("ret", "sp", "callee", "out", "calls"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]!r} != {b[k]!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()

    pl_skip = pack_plane(0, 1, 2, 0.0, 1.0, 0.0, 2.0)
    pl_hit_pos_neg = pack_plane(1, -3, 4, 0.0, 1.0, 0.0, 2.0)
    pl_hit_neg_pos = pack_plane(1, 5, -6, 0.0, 1.0, 0.0, 3.0)

    cases = [
        ("hit_pass2_idx1", {"p0": (1.0, 4.0, 0.0), "p1": (5.0, 0.0, 0.0), "has_out": True, "planes2": [pl_skip, pl_hit_pos_neg], "planes3": [], "dist_rets": [0.5]}),
        ("hit_pass3_neg_then_pos", {"p0": (0.0, 1.0, 2.0), "p1": (0.0, 5.0, 2.0), "has_out": True, "planes2": [pl_skip], "planes3": [pl_hit_neg_pos], "dist_rets": [0.25]}),
        ("miss_dist_neg_no_out", {"p0": (1.0, 4.0, 0.0), "p1": (5.0, 0.0, 0.0), "has_out": False, "planes2": [pl_hit_pos_neg], "planes3": [], "dist_rets": [-1.0]}),
        ("miss_all", {"p0": (0.0, 10.0, 0.0), "p1": (0.0, 20.0, 0.0), "has_out": True, "planes2": [pl_hit_pos_neg], "planes3": [pl_hit_neg_pos], "dist_rets": [0.0]}),
    ]

    for label, kw in cases:
        orig_res = Runner().run(orig_bytes, **kw)
        cand_res = Runner().run(cand_bytes, **kw)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_flag_check", "if (elem[8] == 0) {\n                continue;\n            }", ""),
        ("wrong_stride", "i * 0xA8", "i * 0xA0"),
        ("wrong_dist_check", "if (dist >= 0.0f)", "if (dist > 1.0f)"),
        ("drop_out_write", "if (out != nullptr)", "if (false)"),
        ("wrong_miss_ret", "return -1;", "return 0;"),
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
        f"PASS: engine_func_0025b6e8 (0x{FUNC_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
