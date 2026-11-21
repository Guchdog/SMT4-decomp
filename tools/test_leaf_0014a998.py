#!/usr/bin/env python3
"""Differential test for func_0014a998 (0x0014a998) with Unicorn ARM."""

from __future__ import annotations

import math
import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "engine" / "leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_0014a998"

FUNC_ADDR = 0x0014A998
FUNC_SIZE = 672
EXPF_ADDR = 0x002AC0C4

CTX0_ADDR = 0x20000000
OUT_DESC_ADDR = 0x20001000
OUT_BUF_ADDR = 0x20002010  # OUT_DESC_ADDR + 0x10 + 0x1000
PARAMS_ADDR = 0x20004000
PROJ_ADDR = 0x20005000

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


def f2u(x: float) -> int:
    return struct.unpack("<I", struct.pack("<f", x))[0]


def u2f(u: int) -> float:
    return struct.unpack("<f", struct.pack("<I", u & 0xFFFFFFFF))[0]


def make_stub_bx_lr() -> bytes:
    return struct.pack("<I", 0xE12FFF1E)


def compile_candidate() -> tuple[bytes, list[tuple[str, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}")

    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    shdrs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = shdrs[e_shstrndx][4]

    def sh_name(idx: int) -> str:
        off = shstr_off + shdrs[idx][0]
        return data[off : data.index(b"\x00", off)].decode("ascii", errors="replace")

    tidx = next(i for i in range(e_shnum) if sh_name(i) == ".text")
    text_data = data[shdrs[tidx][4] : shdrs[tidx][4] + shdrs[tidx][5]]
    symtab = next(s for s in shdrs if s[1] == 2)
    strtab_off = shdrs[symtab[6]][4]

    fn_off = fn_size = None
    for i in range(symtab[5] // 16):
        st_name, st_value, st_size, st_info, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "func_0014a998":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("func_0014a998 not found in object")

    relocs: list[tuple[str, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size and r_type in (28, 29):
                    st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    relocs.append((sname, r_off - fn_off))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def run_case(
    code_bytes: bytes,
    relocs: list[tuple[str, int]],
    *,
    is_orig: bool,
    ctx0_160: float,
    ctx0_158: float,
    ctx0_15c: float,
    mode: int,
    p1: float,
    p2: float,
    p3: float,
    proj_28: float,
    proj_2c: float,
    proj_38: float,
    proj_3c: float,
) -> tuple[bytes, dict[str, int]]:
    mu = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    cpacr = mu.reg_read(arm.UC_ARM_REG_C1_C0_2)
    mu.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    mu.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    mu.mem_map(0x00100000, 0x00400000)
    mu.mem_map(0x20000000, 0x00100000)
    mu.mem_map(STACK_BASE, STACK_SIZE)
    mu.mem_map(LR_SENTINEL, 0x1000)

    buf = bytearray(code_bytes)
    entry = FUNC_ADDR if is_orig else 0x00400000
    if not is_orig:
        for sname, off in relocs:
            if sname == "func_002ac0c4":
                patch_bl(buf, off, entry + off, EXPF_ADDR)
            else:
                raise RuntimeError(f"Unexpected reloc target: {sname}")

    mu.mem_write(entry, bytes(buf))
    mu.mem_write(EXPF_ADDR, make_stub_bx_lr())

    def hook_expf(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        x = u2f(uc.reg_read(arm.UC_ARM_REG_S0))
        try:
            y = math.exp(x)
        except OverflowError:
            y = float("inf")
        uc.reg_write(arm.UC_ARM_REG_S0, f2u(y))

    mu.hook_add(unicorn.UC_HOOK_CODE, hook_expf, begin=EXPF_ADDR, end=EXPF_ADDR)

    mu.mem_write(CTX0_ADDR + 0x158, struct.pack("<fff", ctx0_158, ctx0_15c, ctx0_160))
    mu.mem_write(OUT_DESC_ADDR + 0x10, struct.pack("<I", 0x1000))
    mu.mem_write(OUT_BUF_ADDR, b"\xAA" * (131 * 4))
    mu.mem_write(PARAMS_ADDR, struct.pack("<Ifff", mode, p1, p2, p3))
    mu.mem_write(PROJ_ADDR + 0x28, struct.pack("<ff", proj_28, proj_2c))
    mu.mem_write(PROJ_ADDR + 0x38, struct.pack("<ff", proj_38, proj_3c))

    mu.reg_write(arm.UC_ARM_REG_R0, CTX0_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, OUT_DESC_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R2, PARAMS_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R3, PROJ_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, val in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), val)

    mu.emu_start(entry, LR_SENTINEL, count=300000)

    out_mem = bytes(mu.mem_read(OUT_BUF_ADDR, 131 * 4))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return out_mem, regs


CASES = [
    dict(
        name="proj_mode1_linear",
        ctx0_160=0.0,
        ctx0_158=0.0,
        ctx0_15c=0.0,
        mode=1,
        p1=10.0,
        p2=100.0,
        p3=1.0,
        proj_28=1.0,
        proj_2c=-1.0,
        proj_38=0.01,
        proj_3c=0.02,
    ),
    dict(
        name="lerp_mode2_exp",
        ctx0_160=1.0,
        ctx0_158=0.0,
        ctx0_15c=150.0,
        mode=2,
        p1=20.0,
        p2=120.0,
        p3=2.5,
        proj_28=0.0,
        proj_2c=0.0,
        proj_38=0.0,
        proj_3c=1.0,
    ),
    dict(
        name="lerp_mode3_gauss",
        ctx0_160=1.0,
        ctx0_158=-10.0,
        ctx0_15c=110.0,
        mode=3,
        p1=5.0,
        p2=95.0,
        p3=3.0,
        proj_28=0.0,
        proj_2c=0.0,
        proj_38=0.0,
        proj_3c=1.0,
    ),
    dict(
        name="lerp_mode0_clamp_delta",
        ctx0_160=1.0,
        ctx0_158=0.0,
        ctx0_15c=10.0,
        mode=0,
        p1=1.0,
        p2=8.0,
        p3=1.0,
        proj_28=0.0,
        proj_2c=0.0,
        proj_38=0.0,
        proj_3c=1.0,
    ),
    dict(
        name="lerp_mode1_inf_prev",
        ctx0_160=1.0,
        ctx0_158=0.5,
        ctx0_15c=float("inf"),
        mode=1,
        p1=0.0,
        p2=10.0,
        p3=1.0,
        proj_28=0.0,
        proj_2c=0.0,
        proj_38=0.0,
        proj_3c=1.0,
    ),
]


def check_pair(
    orig_bytes: bytes,
    cand_bytes: bytes,
    relocs: list[tuple[str, int]],
    *,
    cand_is_orig: bool = False,
) -> tuple[bool, str]:
    for c in CASES:
        kw = {k: v for k, v in c.items() if k != "name"}
        o_mem, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_mem, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_mem != c_mem:
            for w in range(0, len(o_mem), 4):
                ov = struct.unpack_from("<I", o_mem, w)[0]
                cv = struct.unpack_from("<I", c_mem, w)[0]
                if ov != cv:
                    return False, f"{c['name']}: word[{w // 4}] orig=0x{ov:08x} cand=0x{cv:08x}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: register mismatch orig={o_regs} cand={c_regs}"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Corrupt literal 0x000F00E6 -> 0x000F00E7
    m1 = bytearray(b)
    off = m1.index(struct.pack("<I", 0x000F00E6))
    struct.pack_into("<I", m1, off, 0x000F00E7)

    # 2. Flip loop bound cmp r4, #0x80 -> cmp r4, #0x7F
    m2 = bytearray(b)
    off2 = 0x0014ABFC - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0xE3540080
    struct.pack_into("<I", m2, off2, 0xE354007F)

    # 3. Flip ctx0+0x160 branch bne -> beq
    m3 = bytearray(b)
    off3 = 0x0014AA48 - FUNC_ADDR
    insn3 = struct.unpack_from("<I", m3, off3)[0]
    assert (insn3 >> 28) == 0x1
    struct.pack_into("<I", m3, off3, (insn3 & 0x0FFFFFFF) | 0x00000000)

    # 4. Flip mode == 2 vnmul.f32 -> vmul.f32
    m4 = bytearray(b)
    off4 = 0x0014AB08 - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    struct.pack_into("<I", m4, off4, insn4 ^ 0x00000040)

    # 5. Flip pack shift lsl #13 -> lsl #12
    m5 = bytearray(b)
    off5 = 0x0014ABD0 - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE1812680
    struct.pack_into("<I", m5, off5, 0xE1812600)

    return [
        ("header_000f00e7", bytes(m1)),
        ("loop_bound_7f", bytes(m2)),
        ("ctx160_beq", bytes(m3)),
        ("mode2_sign", bytes(m4)),
        ("pack_shift_12", bytes(m5)),
    ]


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    start = FUNC_ADDR - 0x00100000
    orig_bytes = orig_all[start : start + FUNC_SIZE]

    cand_bytes, relocs = compile_candidate()
    ok, msg = check_pair(orig_bytes, cand_bytes, relocs)
    if not ok:
        print(f"FAIL: {msg}")
        return 1

    detected = 0
    for mname, mbytes in mutate_bytes(orig_bytes):
        mok, _ = check_pair(orig_bytes, mbytes, [], cand_is_orig=True)
        if not mok:
            detected += 1
        else:
            print(f"FAIL: mutant {mname} was not detected")
            return 1

    print(
        f"PASS: func_0014a998 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
