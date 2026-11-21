#!/usr/bin/env python3
"""Differential test for ui_func_0033ceb8 (0x0033ceb8) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0033ceb8"

FUNC_ADDR = 0x0033CEB8
FUNC_SIZE = 684

STUBS = {
    0x002C1D3C: "ui_func_002c1d3c",
    0x002B7978: "ui_func_002b7978",
    0x002BC2C4: "ui_func_002bc2c4",
    0x002BF710: "ui_func_002bf710",
    0x002BF460: "ui_func_002bf460",
    0x0024807C: "ui_func_0024807c",
    0x0033C960: "ui_func_0033c960",
}

G44EA00 = 0x0044EA00
SELF_ADDR = 0x20000000

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
            if name == "ui_func_0033ceb8":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("ui_func_0033ceb8 not found in object")

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
    state_390: int,
    f394: float,
    f398: float,
    f39c: float,
    f3a0: float,
    count_2f4: int,
    n_2f8: int,
    n_2fc: int,
    y_388: float,
    y_38c: float,
    items: list[tuple[int, int, int]],
) -> tuple[list[tuple[str, tuple[object, ...]]], dict[str, int]]:
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
        if sname == "ui_func_002c1d3c":
            calls.append((sname, (r0, r1)))
        elif sname == "ui_func_002b7978":
            rect0 = struct.unpack("<4f", uc.mem_read(r0, 16))
            s0 = u2f(uc.reg_read(arm.UC_ARM_REG_S0))
            s1 = u2f(uc.reg_read(arm.UC_ARM_REG_S1))
            s2 = u2f(uc.reg_read(arm.UC_ARM_REG_S2))
            s3 = u2f(uc.reg_read(arm.UC_ARM_REG_S3))
            s4 = u2f(uc.reg_read(arm.UC_ARM_REG_S4))
            calls.append((sname, (rect0, round(s0, 4), round(s1, 4), round(s2, 4), round(s3, 4), round(s4, 4))))
        elif sname == "ui_func_002bc2c4":
            calls.append((sname, ()))
        elif sname == "ui_func_002bf710":
            s0 = u2f(uc.reg_read(arm.UC_ARM_REG_S0))
            calls.append((sname, (round(s0, 5),)))
        elif sname == "ui_func_002bf460":
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            s4, s5 = struct.unpack("<ii", uc.mem_read(sp, 8))
            calls.append((sname, (r0, r1, r2, r3, s4, s5)))
        elif sname == "ui_func_0024807c":
            s0 = u2f(uc.reg_read(arm.UC_ARM_REG_S0))
            s1 = u2f(uc.reg_read(arm.UC_ARM_REG_S1))
            s2 = u2f(uc.reg_read(arm.UC_ARM_REG_S2))
            s3 = u2f(uc.reg_read(arm.UC_ARM_REG_S3))
            calls.append((sname, (round(s0, 4), round(s1, 4), round(s2, 4), round(s3, 4))))
            uc.reg_write(arm.UC_ARM_REG_S0, f2u(s0 - s3 * 2.0))
        elif sname == "ui_func_0033c960":
            s0 = u2f(uc.reg_read(arm.UC_ARM_REG_S0))
            s1 = u2f(uc.reg_read(arm.UC_ARM_REG_S1))
            s2 = u2f(uc.reg_read(arm.UC_ARM_REG_S2))
            calls.append((sname, (r0, r1, round(s0, 4), round(s1, 4), round(s2, 4))))

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G44EA00, struct.pack("<I", 0x20050000))
    mu.mem_write(SELF_ADDR, b"\x00" * 0x400)
    mu.mem_write(SELF_ADDR + 0x2F4, struct.pack("<iii", count_2f4, n_2f8, n_2fc))
    mu.mem_write(SELF_ADDR + 0x368, struct.pack("<4f", 12.0, 34.0, 56.0, 78.0))
    mu.mem_write(SELF_ADDR + 0x388, struct.pack("<ff", y_388, y_38c))
    mu.mem_write(SELF_ADDR + 0x390, struct.pack("<i4f", state_390, f394, f398, f39c, f3a0))

    for i, (b40, m44, idx48) in enumerate(items):
        base = SELF_ADDR + i * 0x54
        mu.mem_write(base + 0x40, struct.pack("<B", b40))
        mu.mem_write(base + 0x44, struct.pack("<ii", m44, idx48))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, val in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), val)

    mu.emu_start(entry, LR_SENTINEL, count=100000)

    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return calls, regs


CASES = [
    dict(
        name="state_4_early_exit",
        state_390=4,
        f394=1.0,
        f398=2.0,
        f39c=1.0,
        f3a0=4.0,
        count_2f4=2,
        n_2f8=2,
        n_2fc=2,
        y_388=100.0,
        y_38c=150.0,
        items=[(0, 0, 0), (1, 1, 0)],
    ),
    dict(
        name="both_nonzero_mixed_items",
        state_390=1,
        f394=2.0,
        f398=3.0,
        f39c=1.5,
        f3a0=4.0,
        count_2f4=3,
        n_2f8=2,
        n_2fc=3,
        y_388=100.0,
        y_38c=150.0,
        items=[(0, 0, 1), (1, 1, 0), (1, 2, 2)],
    ),
    dict(
        name="zero_2f8_fallback_avg_y",
        state_390=2,
        f394=0.0,
        f398=1.0,
        f39c=2.0,
        f3a0=2.0,
        count_2f4=2,
        n_2f8=0,
        n_2fc=4,
        y_388=80.0,
        y_38c=120.0,
        items=[(1, 1, 1), (1, 0, 2)],
    ),
    dict(
        name="zero_count",
        state_390=0,
        f394=1.0,
        f398=1.0,
        f39c=3.0,
        f3a0=0.0,
        count_2f4=0,
        n_2f8=1,
        n_2fc=1,
        y_388=50.0,
        y_38c=60.0,
        items=[],
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
        o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip state == 4 check cmp r0, #4 -> #5
    m1 = bytearray(b)
    off1 = 0x0033CECC - FUNC_ADDR
    assert struct.unpack_from("<I", m1, off1)[0] == 0xE3500004
    struct.pack_into("<I", m1, off1, 0xE3500005)

    # 2. Flip ui_func_002bf460 arg r2=#0x54 -> #0x53
    m2 = bytearray(b)
    off2 = 0x0033CF70 - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0xE3A02054
    struct.pack_into("<I", m2, off2, 0xE3A02053)

    # 3. Flip item[0x40] == 0 branch beq -> bne
    m3 = bytearray(b)
    off3 = 0x0033D000 - FUNC_ADDR
    insn3 = struct.unpack_from("<I", m3, off3)[0]
    assert (insn3 >> 28) == 0x0
    struct.pack_into("<I", m3, off3, (insn3 & 0x0FFFFFFF) | 0x10000000)

    # 4. Flip mode44 == 1 branch beq -> bne (at 0x0033d020)
    m4 = bytearray(b)
    off4 = 0x0033D020 - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    assert (insn4 >> 28) == 0x0
    struct.pack_into("<I", m4, off4, (insn4 & 0x0FFFFFFF) | 0x10000000)

    # 5. Flip loop bound bgt -> blt (at 0x0033d068)
    m5 = bytearray(b)
    off5 = 0x0033D068 - FUNC_ADDR
    insn5 = struct.unpack_from("<I", m5, off5)[0]
    assert (insn5 >> 28) == 0xC
    struct.pack_into("<I", m5, off5, (insn5 & 0x0FFFFFFF) | 0xB0000000)

    return [
        ("state_cmp_5", bytes(m1)),
        ("bf460_arg_53", bytes(m2)),
        ("item40_bne", bytes(m3)),
        ("mode44_bne", bytes(m4)),
        ("loop_blt", bytes(m5)),
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
        f"PASS: ui_func_0033ceb8 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
