#!/usr/bin/env python3
"""Differential test for ui_func_002bdeb8 (0x002bdeb8) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002bdeb8"

FUNC_ADDR = 0x002BDEB8
FUNC_SIZE = 692

STUBS = {
    0x002BE4DC: "func_002be4dc",
    0x002C615C: "ui_func_002c615c",
    0x002BF6D0: "camp_func_002bf6d0",
    0x002BF460: "ui_func_002bf460",
    0x002BEF14: "script_vm_func_002bef14",
}

LAYOUT_BASE = 0x20000000
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
            if name == "ui_func_002bdeb8":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("ui_func_002bdeb8 not found in object")

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
    val: int,
    x: int,
    y: int,
    show_sign: int,
) -> tuple[list[tuple[str, tuple[int, ...]]], dict[str, int]]:
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

    for idx in range(0x80):
        mu.mem_write(LAYOUT_BASE + idx * 0x10 + 8, struct.pack("<hh", idx * 2 - 10, idx + 3))

    calls: list[tuple[str, tuple[int, ...]]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = STUBS[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        if sname == "func_002be4dc":
            calls.append((sname, (r0,)))
        elif sname == "ui_func_002c615c":
            calls.append((sname, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, (r0 // r1) & 0xFFFFFFFF)
        elif sname == "camp_func_002bf6d0":
            calls.append((sname, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, LAYOUT_BASE + (r1 & 0x7F) * 0x10)
        elif sname == "ui_func_002bf460":
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            s4, s5 = struct.unpack("<ii", uc.mem_read(sp, 8))
            calls.append((sname, (r0, r1, r2, r3, s4, s5)))
        elif sname == "script_vm_func_002bef14":
            calls.append((sname, ()))

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)
    mu.reg_write(arm.UC_ARM_REG_R1, x & 0xFFFFFFFF)
    mu.reg_write(arm.UC_ARM_REG_R2, y & 0xFFFFFFFF)
    mu.reg_write(arm.UC_ARM_REG_R3, show_sign & 0xFFFFFFFF)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return calls, regs


CASES = [
    dict(name="pos_large_with_sign", val=123456789, x=100, y=50, show_sign=1),
    dict(name="neg_large_with_sign", val=-9876543, x=20, y=30, show_sign=1),
    dict(name="zero_with_sign", val=0, x=10, y=15, show_sign=1),
    dict(name="neg_no_sign", val=-42, x=5, y=8, show_sign=0),
    dict(name="zero_no_sign", val=0, x=5, y=8, show_sign=0),
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
            return False, f"{c['name']}: regs mismatch orig={o_regs} cand={c_regs}"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip show_sign == 0 branch beq -> bne
    m1 = bytearray(b)
    off1 = 0x002BDEEC - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x0
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x10000000)

    # 2. Flip zero-digit glyph id mov r1, #0x5c -> #0x5d
    m2 = bytearray(b)
    off2 = 0x002BDFC8 - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0xE3A0105C
    struct.pack_into("<I", m2, off2, 0xE3A0105D)

    # 3. Flip pos == 2 comma check cmp r5, #2 -> #3
    m3 = bytearray(b)
    off3 = 0x002BDFAC - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xE3550002
    struct.pack_into("<I", m3, off3, 0xE3550003)

    # 4. Flip pos == 5 comma check cmp r5, #5 -> #4
    m4 = bytearray(b)
    off4 = 0x002BDFBC - FUNC_ADDR
    assert struct.unpack_from("<I", m4, off4)[0] == 0xE3550005
    struct.pack_into("<I", m4, off4, 0xE3550004)

    # 5. Flip '-' glyph id mov r2, #0xb -> #0xa
    m5 = bytearray(b)
    off5 = 0x002BE0E0 - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE3A0200B
    struct.pack_into("<I", m5, off5, 0xE3A0200A)

    return [
        ("show_sign_bne", bytes(m1)),
        ("zero_glyph_5d", bytes(m2)),
        ("comma_pos2_3", bytes(m3)),
        ("comma_pos5_4", bytes(m4)),
        ("minus_glyph_a", bytes(m5)),
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
        f"PASS: ui_func_002bdeb8 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
