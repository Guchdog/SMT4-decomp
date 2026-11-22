#!/usr/bin/env python3
"""Differential test for script_vm_func_00266e88 (0x00266e88) with Unicorn ARM."""

from __future__ import annotations

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
OUT_DIR = ROOT / "build" / "test_leaf_00266e88"

FUNC_ADDR = 0x00266E88
FUNC_SIZE = 724

STUBS = {
    0x0024BD60: "func_0024bd60",
}

G_SL = 0x00446FE8
G_PASS0_ARR = 0x00493C5C

P0_ADDR = 0x20000000
P1_ADDR = 0x20000100
OUT_ADDR = 0x20000200
PASS1_ARR = 0x20010000
PASS2_ARR = 0x20020000

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
            if name == "script_vm_func_00266e88":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("script_vm_func_00266e88 not found in object")

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


def build_plane(b4: int, b5: int, b8: int, b9: int, nx: float, ny: float, nz: float, d: float) -> bytes:
    buf = bytearray(0xA8)
    struct.pack_into("<bbxxBB", buf, 4, b4, b5, b8, b9)
    struct.pack_into("<4f", buf, 0xC, nx, ny, nz, d)
    return bytes(buf)


def run_case(
    code_bytes: bytes,
    relocs: list[tuple[str, int]],
    *,
    is_orig: bool,
    p0: tuple[float, float, float],
    p1: tuple[float, float, float],
    planes0: list[bytes],
    planes1: list[bytes],
    planes2: list[bytes],
    ret_24bd60: float,
) -> tuple[int, bytes, list[tuple[object, ...]], dict[str, int]]:
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
    name_to_addr = {v: k for k, v in STUBS.items()}
    if not is_orig:
        for sname, off in relocs:
            if sname not in name_to_addr:
                raise RuntimeError(f"Unexpected reloc target: {sname}")
            patch_bl(buf, off, entry + off, name_to_addr[sname])

    mu.mem_write(entry, bytes(buf))
    for addr in STUBS:
        mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[object, ...]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        s0 = round(u2f(uc.reg_read(arm.UC_ARM_REG_S0)), 4)
        s1 = round(u2f(uc.reg_read(arm.UC_ARM_REG_S1)), 4)
        s2 = round(u2f(uc.reg_read(arm.UC_ARM_REG_S2)), 4)
        s3 = round(u2f(uc.reg_read(arm.UC_ARM_REG_S3)), 4)
        calls.append((r0, r1, r2, s0, s1, s2, s3))
        uc.reg_write(arm.UC_ARM_REG_S0, f2u(ret_24bd60))

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(P0_ADDR, struct.pack("<3f", *p0))
    mu.mem_write(P1_ADDR, struct.pack("<3f", *p1))
    mu.mem_write(OUT_ADDR, b"\x00" * 12)

    mu.mem_write(G_SL, b"\x00" * 0x30)
    mu.mem_write(G_SL + 0x0C, struct.pack("<iii", len(planes1), len(planes2), len(planes0)))
    mu.mem_write(G_SL + 0x20, struct.pack("<II", PASS1_ARR, PASS2_ARR))

    for i, pl in enumerate(planes0):
        mu.mem_write(G_PASS0_ARR + i * 0xA8, pl)
    for i, pl in enumerate(planes1):
        mu.mem_write(PASS1_ARR + i * 0xA8, pl)
    for i, pl in enumerate(planes2):
        mu.mem_write(PASS2_ARR + i * 0xA8, pl)

    mu.reg_write(arm.UC_ARM_REG_R0, P0_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, P1_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R2, OUT_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    ret = mu.reg_read(arm.UC_ARM_REG_R0)
    if ret & 0x80000000:
        ret -= 0x100000000
    out_mem = bytes(mu.mem_read(OUT_ADDR, 12))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return ret, out_mem, calls, regs


CASES = [
    dict(
        name="no_hit_all_empty",
        p0=(0.0, 0.0, 100.0),
        p1=(0.0, 0.0, 0.0),
        planes0=[],
        planes1=[],
        planes2=[],
        ret_24bd60=1.0,
    ),
    dict(
        name="pass0_hit_t_lt_1",
        p0=(0.0, 0.0, 50.0),
        p1=(0.0, 0.0, -50.0),
        planes0=[
            build_plane(1, -2, 0, 3, 0.0, 0.0, 1.0, 0.0),
            build_plane(1, -2, 1, 2, 0.0, 0.0, 1.0, 0.0),
            build_plane(1, -2, 1, 3, 0.0, 0.0, 1.0, 0.0),
        ],
        planes1=[],
        planes2=[],
        ret_24bd60=2.0,
    ),
    dict(
        name="pass1_hit_and_pass2_hit_t_ge_1",
        p0=(0.0, 0.0, 40.0),
        p1=(0.0, 0.0, -40.0),
        planes0=[],
        planes1=[build_plane(2, 3, 1, 0, 0.0, 0.0, 1.0, 10.0)],
        planes2=[build_plane(4, 5, 1, 0, 0.0, 0.0, 1.0, 5.0)],
        ret_24bd60=200.0,
    ),
    dict(
        name="miss_negative_24bd60",
        p0=(0.0, 0.0, 50.0),
        p1=(0.0, 0.0, -50.0),
        planes0=[build_plane(1, 1, 1, 3, 0.0, 0.0, 1.0, 0.0)],
        planes1=[],
        planes2=[],
        ret_24bd60=-1.0,
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
        o_ret, o_out, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_ret, c_out, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_ret != c_ret:
            return False, f"{c['name']}: ret mismatch orig={o_ret} cand={c_ret}"
        if o_out != c_out:
            return False, f"{c['name']}: out mismatch orig={o_out.hex()} cand={c_out.hex()}"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch orig={o_calls} cand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip arr[8] == 0 check beq -> bne (at 0x00266eec)
    m1 = bytearray(b)
    off1 = 0x00266EEC - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x0
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x10000000)

    # 2. Flip arr[9] == 3 check cmp r0, #3 -> #2 (at 0x00266fd8)
    m2 = bytearray(b)
    off2 = 0x00266FD8 - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0xE3500003
    struct.pack_into("<I", m2, off2, 0xE3500002)

    # 3. Flip pass loop bound cmp r7, #3 -> #2 (at 0x00267114)
    m3 = bytearray(b)
    off3 = 0x00267114 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xE3570003
    struct.pack_into("<I", m3, off3, 0xE3570002)

    # 4. Flip t2 >= 1.0f branch bge -> blt (at 0x002670b4)
    m4 = bytearray(b)
    off4 = 0x002670B4 - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    assert (insn4 >> 28) == 0xA
    struct.pack_into("<I", m4, off4, (insn4 & 0x0FFFFFFF) | 0xB0000000)

    # 5. Flip res < 0.0f branch bhi -> bls (at 0x002670a0)
    m5 = bytearray(b)
    off5 = 0x002670A0 - FUNC_ADDR
    insn5 = struct.unpack_from("<I", m5, off5)[0]
    assert (insn5 >> 28) == 0x8
    struct.pack_into("<I", m5, off5, (insn5 & 0x0FFFFFFF) | 0x90000000)

    return [
        ("arr8_bne", bytes(m1)),
        ("arr9_cmp_2", bytes(m2)),
        ("pass_bound_2", bytes(m3)),
        ("t2_blt", bytes(m4)),
        ("res_bls", bytes(m5)),
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
        f"PASS: script_vm_func_00266e88 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
