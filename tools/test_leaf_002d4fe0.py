#!/usr/bin/env python3
"""Differential test for engine_func_002d4fe0 (0x002d4fe0) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002d4fe0"

FUNC_ADDR = 0x002D4FE0
FUNC_SIZE = 744

STUBS = {
    0x002C2B1C: "engine_func_002c2b1c",
    0x00256780: "func_00256780",
    0x0027FBC8: "script_vm_func_0027fbc8",
    0x00264368: "script_vm_func_00264368",
    0x002820A4: "ui_func_002820a4",
    0x0028277C: "script_vm_func_0028277c",
    0x00282600: "script_vm_func_00282600",
    0x002ED03C: "func_002ed03c",
}

G_9FC1C = 0x0049FC1C
G_447E88 = 0x00447E88

SELF_ADDR = 0x20000000
PLAYER_ADDR = 0x20001000

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
            if name == "engine_func_002d4fe0":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_002d4fe0 not found in object")

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
    flag_48: int,
    flag_m2e8: int,
    flag_cc: int,
    dash_val: int,
    stick: tuple[float, float],
    init_spd: float,
    self_50: float,
    col_ret: int,
) -> tuple[bytes, bytes, list[tuple[str, tuple[object, ...]]], dict[str, int]]:
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
        if sname == "engine_func_002c2b1c":
            calls.append((sname, ()))
        elif sname == "func_00256780":
            calls.append((sname, ()))
            uc.reg_write(arm.UC_ARM_REG_R0, dash_val & 0xFFFFFFFF)
        elif sname == "script_vm_func_0027fbc8":
            calls.append((sname, (r2,)))
            uc.mem_write(r0, struct.pack("<f", stick[0]))
            uc.mem_write(r1, struct.pack("<f", stick[1]))
        elif sname == "script_vm_func_00264368":
            calls.append((sname, ()))
        elif sname == "ui_func_002820a4":
            s0 = u2f(uc.reg_read(arm.UC_ARM_REG_S0))
            s1 = u2f(uc.reg_read(arm.UC_ARM_REG_S1))
            calls.append((sname, (round(s0, 4), round(s1, 4))))
            uc.reg_write(arm.UC_ARM_REG_S0, f2u(math.atan2(s1, s0)))
        elif sname == "script_vm_func_0028277c":
            s0 = u2f(uc.reg_read(arm.UC_ARM_REG_S0))
            calls.append((sname, (round(s0, 5),)))
            uc.reg_write(arm.UC_ARM_REG_S0, f2u(math.sin(s0)))
        elif sname == "script_vm_func_00282600":
            s0 = u2f(uc.reg_read(arm.UC_ARM_REG_S0))
            calls.append((sname, (round(s0, 5),)))
            uc.reg_write(arm.UC_ARM_REG_S0, f2u(math.cos(s0)))
        elif sname == "func_002ed03c":
            prev = struct.unpack("<3f", uc.mem_read(r1, 12))
            calls.append((sname, (r0, tuple(round(x, 3) for x in prev))))
            uc.reg_write(arm.UC_ARM_REG_R0, col_ret)

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G_9FC1C - 0x300, b"\x00" * 0x400)
    mu.mem_write(G_9FC1C + 0x48, struct.pack("<B", flag_48))
    mu.mem_write(G_9FC1C - 0x300 + 0x18, struct.pack("<B", flag_m2e8))
    mu.mem_write(G_9FC1C + 0xCC, struct.pack("<B", flag_cc))

    mu.mem_write(G_447E88, struct.pack("<I", PLAYER_ADDR))
    mu.mem_write(PLAYER_ADDR, b"\x00" * 0x60)
    mu.mem_write(PLAYER_ADDR + 0x1C, struct.pack("<3f", 10.0, 20.0, 30.0))
    mu.mem_write(PLAYER_ADDR + 0x50, struct.pack("<f", 45.0))

    mu.mem_write(SELF_ADDR, b"\x00" * 0xE00)
    mu.mem_write(SELF_ADDR + 0x3C, struct.pack("<f", init_spd))
    mu.mem_write(SELF_ADDR + 0x50, struct.pack("<f", self_50))
    mu.mem_write(SELF_ADDR + 0xD94, struct.pack("<I", 0x9999))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    self_mem = (
        bytes(mu.mem_read(SELF_ADDR + 0x3C, 4))
        + bytes(mu.mem_read(SELF_ADDR + 0xC0, 4))
        + bytes(mu.mem_read(SELF_ADDR + 0xD94, 4))
    )
    player_mem = bytes(mu.mem_read(PLAYER_ADDR + 0x1C, 0x38))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return self_mem, player_mem, calls, regs


CASES = [
    dict(
        name="blocked_by_flag48",
        flag_48=1,
        flag_m2e8=0,
        flag_cc=0,
        dash_val=100,
        stick=(0.8, 0.0),
        init_spd=10.0,
        self_50=90.0,
        col_ret=0,
    ),
    dict(
        name="active_stick_2_steps_with_collision_break",
        flag_48=0,
        flag_m2e8=0,
        flag_cc=0,
        dash_val=250,
        stick=(0.8, -0.6),
        init_spd=30.0,
        self_50=350.0,
        col_ret=1,
    ),
    dict(
        name="deadzone_decay_1_step_no_col_check",
        flag_48=0,
        flag_m2e8=0,
        flag_cc=1,
        dash_val=150,
        stick=(0.1, -0.2),
        init_spd=0.0012,
        self_50=0.0,
        col_ret=0,
    ),
    dict(
        name="active_stick_2_steps_no_collision",
        flag_48=0,
        flag_m2e8=0,
        flag_cc=0,
        dash_val=150,
        stick=(-0.7, 0.7),
        init_spd=50.0,
        self_50=10.0,
        col_ret=0,
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
        o_self, o_pl, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_self, c_pl, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_self != c_self or o_pl != c_pl:
            return False, f"{c['name']}: memory mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip flag_48 != 0 branch bne -> beq (at 0x002d5014)
    m1 = bytearray(b)
    off1 = 0x002D5014 - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x1
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x00000000)

    # 2. Flip deadzone decay threshold to zero (0x002d50e8 cmp r0, r1 -> bge skip)
    m2 = bytearray(b)
    off2 = 0x002D50EC - FUNC_ADDR
    insn2 = struct.unpack_from("<I", m2, off2)[0]
    assert (insn2 >> 28) == 0xB
    struct.pack_into("<I", m2, off2, (insn2 & 0x0FFFFFFF) | 0xA0000000)

    # 3. Flip steps movgt r5, #2 -> #1 (at 0x002d5188)
    m3 = bytearray(b)
    off3 = 0x002D5188 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xC3A05002
    struct.pack_into("<I", m3, off3, 0xC3A05001)

    # 4. Flip flag_cc != 0 branch bne -> beq (at 0x002d5204)
    m4 = bytearray(b)
    off4 = 0x002D5204 - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    assert (insn4 >> 28) == 0x1
    struct.pack_into("<I", m4, off4, (insn4 & 0x0FFFFFFF) | 0x00000000)

    # 5. Flip col_res != 0 break branch bne -> beq (at 0x002d5248)
    m5 = bytearray(b)
    off5 = 0x002D5248 - FUNC_ADDR
    insn5 = struct.unpack_from("<I", m5, off5)[0]
    assert (insn5 >> 28) == 0x1
    struct.pack_into("<I", m5, off5, (insn5 & 0x0FFFFFFF) | 0x00000000)

    return [
        ("flag48_beq", bytes(m1)),
        ("decay_ge", bytes(m2)),
        ("steps_1", bytes(m3)),
        ("flagcc_beq", bytes(m4)),
        ("col_break_beq", bytes(m5)),
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
        f"PASS: engine_func_002d4fe0 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
