#!/usr/bin/env python3
"""Differential test for engine_func_0015b8f8 (0x0015b8f8) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0015b8f8"

FUNC_ADDR = 0x0015B8F8
FUNC_SIZE = 680

STUBS = {
    0x0015D888: "func_0015d888",
    0x002BC300: "engine_func_002bc300",
}

G422204 = 0x00422204
G42221C = 0x0042221C

SELF_ADDR = 0x20000000
MAT_ADDR = 0x20001000
SUB_ADDR = 0x20002000
SRC_ADDR = 0x20003000
TEXOBJ_ADDR = 0x20004000
TEXDATA_ADDR = 0x20005000

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
            if name == "engine_func_0015b8f8":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_0015b8f8 not found in object")

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
    tex_handle_18: int,
    g0_val: int,
    g1_val: int,
    src_34: int,
    src_18: int,
    src_1c: int,
    src_3c: int,
    src_40: float,
) -> tuple[bytes, bytes, list[tuple[str, int]], dict[str, int]]:
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

    calls: list[tuple[str, int]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = STUBS[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        if sname == "func_0015d888":
            mat_ptr = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            calls.append((sname, mat_ptr))
        elif sname == "engine_func_002bc300":
            calls.append((sname, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x12345678)

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G422204 + 4, struct.pack("<I", g0_val))
    mu.mem_write(G42221C + 4, struct.pack("<I", g1_val))

    # self
    mu.mem_write(SELF_ADDR, b"\x00" * 0x60)
    mu.mem_write(SELF_ADDR + 0x0C, struct.pack("<I", MAT_ADDR - (SELF_ADDR + 0x0C)))
    mu.mem_write(SELF_ADDR + 0x10, struct.pack("<8I", 0xFFFFFFFF, 0x11111111, 0x22222222, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF))

    # mat -> sub
    mu.mem_write(MAT_ADDR, b"\x00" * 0x20)
    mu.mem_write(MAT_ADDR + 0x00, struct.pack("<I", 0x80000001))
    mu.mem_write(MAT_ADDR + 0x04, struct.pack("<I", SUB_ADDR - (MAT_ADDR + 0x04)))
    mu.mem_write(SUB_ADDR, b"\x00" * 0x40)
    mu.mem_write(SUB_ADDR + 0x24, struct.pack("<I", 0xAABB7704))

    # src -> tex_obj -> tex_data
    mu.mem_write(SRC_ADDR, b"\x00" * 0x50)
    mu.mem_write(SRC_ADDR + 0x18, struct.pack("<I", src_18))
    mu.mem_write(SRC_ADDR + 0x1C, struct.pack("<I", src_1c))
    mu.mem_write(SRC_ADDR + 0x34, struct.pack("<I", src_34))
    mu.mem_write(SRC_ADDR + 0x38, struct.pack("<I", TEXOBJ_ADDR - (SRC_ADDR + 0x38)))
    mu.mem_write(SRC_ADDR + 0x3C, struct.pack("<B", src_3c))
    mu.mem_write(SRC_ADDR + 0x40, struct.pack("<f", src_40))

    mu.mem_write(TEXOBJ_ADDR, b"\x00" * 0x20)
    mu.mem_write(TEXOBJ_ADDR + 0x0C, struct.pack("<I", TEXDATA_ADDR - (TEXOBJ_ADDR + 0x0C)))
    mu.mem_write(TEXOBJ_ADDR + 0x18, struct.pack("<I", tex_handle_18))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, SRC_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, val in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), val)

    mu.emu_start(entry, LR_SENTINEL, count=100000)

    self_mem = bytes(mu.mem_read(SELF_ADDR, 0x50))
    sub_mem = bytes(mu.mem_read(MAT_ADDR, 0x10)) + bytes(mu.mem_read(SUB_ADDR, 0x30))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return self_mem, sub_mem, calls, regs


CASES = [
    dict(
        name="direct_handle_zero_f40",
        tex_handle_18=0x20009000,
        g0_val=1,
        g1_val=1,
        src_34=0xAB,
        src_18=0x1234,
        src_1c=0xABCD,
        src_3c=0,
        src_40=0.0,
    ),
    dict(
        name="fallback_texdata_frac_f40",
        tex_handle_18=0,
        g0_val=0,
        g1_val=1,
        src_34=0x05,
        src_18=0x03FF,
        src_1c=0x07FF,
        src_3c=1,
        src_40=0.25,
    ),
    dict(
        name="clamp_high_f40",
        tex_handle_18=0x2000A000,
        g0_val=1,
        g1_val=0,
        src_34=0x02,
        src_18=0x0010,
        src_1c=0x0020,
        src_3c=0,
        src_40=2.5,
    ),
    dict(
        name="nan_f40",
        tex_handle_18=0,
        g0_val=0,
        g1_val=0,
        src_34=0x0F,
        src_18=0xFFFF,
        src_1c=0xFFFF,
        src_3c=2,
        src_40=float("nan"),
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
        o_self, o_sub, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_self, c_sub, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_self != c_self:
            return False, f"{c['name']}: self_mem mismatch"
        if o_sub != c_sub:
            return False, f"{c['name']}: sub_mem mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch orig={o_calls} cand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip self+0x48 constant mov r3, #0x38 -> #0x34
    m1 = bytearray(b)
    off1 = 0x0015B900 - FUNC_ADDR
    assert struct.unpack_from("<I", m1, off1)[0] == 0xE3A03038
    struct.pack_into("<I", m1, off1, 0xE3A03034)

    # 2. Flip tex_handle == 0 check beq -> bne
    m2 = bytearray(b)
    off2 = 0x0015B984 - FUNC_ADDR
    insn2 = struct.unpack_from("<I", m2, off2)[0]
    assert (insn2 >> 28) == 0x0
    struct.pack_into("<I", m2, off2, (insn2 & 0x0FFFFFFF) | 0x10000000)

    # 3. Flip sub+0x24 orr r1, r1, #2 -> #4
    m3 = bytearray(b)
    off3 = 0x0015BA90 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xE3811002
    struct.pack_into("<I", m3, off3, 0xE3811004)

    # 4. Flip src_3c == 0 moveq r0, #1 -> #0
    m4 = bytearray(b)
    off4 = 0x0015BB04 - FUNC_ADDR
    assert struct.unpack_from("<I", m4, off4)[0] == 0x03A00001
    struct.pack_into("<I", m4, off4, 0x03A00000)

    # 5. Flip gpu_addr shift lsr #4 -> lsr #5
    m5 = bytearray(b)
    off5 = 0x0015BAF0 - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE1811222
    struct.pack_into("<I", m5, off5, 0xE18112A2)

    return [
        ("self48_34", bytes(m1)),
        ("tex_handle_bne", bytes(m2)),
        ("sub24_bit4", bytes(m3)),
        ("src3c_zero", bytes(m4)),
        ("gpu_shift_5", bytes(m5)),
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
        f"PASS: engine_func_0015b8f8 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
