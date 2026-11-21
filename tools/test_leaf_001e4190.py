#!/usr/bin/env python3
"""Differential test for func_001e4190 (0x001e4190) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_001e4190"

FUNC_ADDR = 0x001E4190
FUNC_SIZE = 700

STUBS = {
    0x002AEB2C: "script_vm_func_002aeb2c",
    0x002C5AB8: "engine_func_002c5ab8",
    0x002C1DE4: "script_vm_func_002c1de4",
    0x001A94FC: "ui_func_001a94fc",
    0x001E38F8: "func_001e38f8",
    0x0025B98C: "func_0025b98c",
}

G_448C58 = 0x00448C58
G_49F91C = 0x0049F91C
G_49F8F8 = 0x0049F8F8

ENTRIES_ADDR = 0x20000000
TABLE_ADDR = 0x20010000

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
            if name == "script_vm_func_001e4190":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("script_vm_func_001e4190 not found in object")

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


def build_entry(
    *,
    s0: int,
    s2: int,
    s4: int,
    s6: int,
    b8: int,
    b9: int,
    b10: int,
    b11: int,
    sc: int,
    se: int,
    f10: float,
    s1a: int,
    f1c: float,
    s24: int,
    s26: int,
    s2a: int,
) -> bytes:
    buf = bytearray(0x30)
    struct.pack_into("<hhhh", buf, 0x00, s0, s2, s4, s6)
    struct.pack_into("<BBBB", buf, 0x08, b8, b9, b10, b11)
    struct.pack_into("<hhf", buf, 0x0C, sc, se, f10)
    struct.pack_into("<BBBBBBh", buf, 0x14, 1, 2, 3, 4, 5, 6, s1a)
    struct.pack_into("<f", buf, 0x1C, f1c)
    struct.pack_into("<BBBBhh", buf, 0x20, 7, 8, 9, 10, s24, s26)
    struct.pack_into("<BBbBBBBB", buf, 0x28, 11, 12, s2a, 13, 14, 15, 16, 17)
    return bytes(buf)


def run_case(
    code_bytes: bytes,
    relocs: list[tuple[str, int]],
    *,
    is_orig: bool,
    a0: int,
    a1: int,
    g_228: int,
    init_30: int,
    entry_kwargs: dict[str, object],
) -> tuple[bytes, bytes, bytes, list[tuple[str, tuple[object, ...]]], dict[str, int]]:
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

    calls: list[tuple[str, tuple[object, ...]]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = STUBS[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        if sname in ("script_vm_func_002aeb2c", "engine_func_002c5ab8"):
            calls.append((sname, (r0, r1)))
        elif sname == "script_vm_func_002c1de4":
            calls.append((sname, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x77)
        elif sname == "ui_func_001a94fc":
            floats = tuple(round(u2f(uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))), 5) for i in range(6))
            calls.append((sname, (r0, *floats)))
        elif sname == "func_001e38f8":
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            stack_args = struct.unpack("<9i", uc.mem_read(sp, 36))
            s0 = round(u2f(uc.reg_read(arm.UC_ARM_REG_S0)), 5)
            s1 = round(u2f(uc.reg_read(arm.UC_ARM_REG_S1)), 5)
            calls.append((sname, (r0, r1, r2, r3, s0, s1, stack_args)))
        elif sname == "func_0025b98c":
            calls.append((sname, ()))

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G_448C58, b"\x00" * 0x40)
    mu.mem_write(G_448C58 + 0x00, struct.pack("<II", ENTRIES_ADDR, TABLE_ADDR))
    mu.mem_write(G_448C58 + 0x18, struct.pack("<I", 0x1111))
    mu.mem_write(G_448C58 + 0x30, struct.pack("<II", init_30, 0x2222))

    mu.mem_write(G_49F91C, b"\x00" * 0x400)
    mu.mem_write(G_49F91C + 0x228, struct.pack("<B", g_228))
    mu.mem_write(G_49F8F8, b"\x00" * 0x10)

    ent_bytes = build_entry(**entry_kwargs)
    for idx in range(4):
        mu.mem_write(ENTRIES_ADDR + idx * 0x30, ent_bytes)

    mu.reg_write(arm.UC_ARM_REG_R0, a0 & 0xFFFFFFFF)
    mu.reg_write(arm.UC_ARM_REG_R1, a1 & 0xFFFFFFFF)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=100000)

    g7_mem = bytes(mu.mem_read(G_448C58, 0x40))
    g6_mem = bytes(mu.mem_read(G_49F91C + 0x390, 0x40)) + bytes(mu.mem_read(G_49F8F8, 8))
    tbl_s0 = entry_kwargs["s0"]
    tbl_mem = bytes(mu.mem_read(TABLE_ADDR + tbl_s0 * 73 * 4, 4))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return g7_mem, g6_mem, tbl_mem, calls, regs


CASES = [
    dict(
        name="a1_gt1_wrap_ang",
        a0=1,
        a1=20,
        g_228=0,
        init_30=1,
        entry_kwargs=dict(
            s0=5,
            s2=10,
            s4=15,
            s6=20,
            b8=3,
            b9=100,
            b10=150,
            b11=200,
            sc=2,
            se=-3,
            f10=1.25,
            s1a=200,
            f1c=0.75,
            s24=-10,
            s26=25,
            s2a=-15,
        ),
    ),
    dict(
        name="a1_1_clamp_r5_gt_31",
        a0=2,
        a1=1,
        g_228=0,
        init_30=0,
        entry_kwargs=dict(
            s0=49,
            s2=1,
            s4=2,
            s6=3,
            b8=1,
            b9=0,
            b10=255,
            b11=128,
            sc=0,
            se=1,
            f10=2.0,
            s1a=90,
            f1c=1.0,
            s24=5,
            s26=6,
            s2a=25,
        ),
    ),
    dict(
        name="a1_0_g228_nonzero",
        a0=3,
        a1=0,
        g_228=1,
        init_30=0,
        entry_kwargs=dict(
            s0=2,
            s2=4,
            s4=6,
            s6=8,
            b8=0,
            b9=10,
            b10=20,
            b11=30,
            sc=1,
            se=2,
            f10=0.5,
            s1a=180,
            f1c=0.5,
            s24=1,
            s26=2,
            s2a=10,
        ),
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
        o_g7, o_g6, o_tbl, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_g7, c_g6, c_tbl, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_g7 != c_g7 or o_g6 != c_g6 or o_tbl != c_tbl:
            return False, f"{c['name']}: memory mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip a1 == 0 branch beq -> bne
    m1 = bytearray(b)
    off1 = 0x001E41A4 - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x0
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x10000000)

    # 2. Flip cmp r5, #0x31 -> #0x30
    m2 = bytearray(b)
    off2 = 0x001E4264 - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0xE3550031
    struct.pack_into("<I", m2, off2, 0xE3550030)

    # 3. Flip g7+0x30 == 0 branch beq -> bne
    m3 = bytearray(b)
    off3 = 0x001E4250 - FUNC_ADDR
    insn3 = struct.unpack_from("<I", m3, off3)[0]
    assert (insn3 >> 28) == 0x0
    struct.pack_into("<I", m3, off3, (insn3 & 0x0FFFFFFF) | 0x10000000)

    # 4. Flip ang > 360 branch ble -> bgt
    m4 = bytearray(b)
    off4 = 0x001E43EC - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    assert (insn4 >> 28) == 0xD
    struct.pack_into("<I", m4, off4, (insn4 & 0x0FFFFFFF) | 0xC0000000)

    # 5. Flip g6+0x3c8 store offset #0x3c8 -> #0x3c4
    m5 = bytearray(b)
    off5 = 0x001E43CC - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE58613C8
    struct.pack_into("<I", m5, off5, 0xE58613C4)

    return [
        ("a1_zero_bne", bytes(m1)),
        ("r5_clamp_30", bytes(m2)),
        ("g30_bne", bytes(m3)),
        ("ang_wrap_bgt", bytes(m4)),
        ("g3c8_off_3c4", bytes(m5)),
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
        f"PASS: func_001e4190 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
