#!/usr/bin/env python3
"""Differential test for engine_func_0013a62c (0x0013a62c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0013a62c"

FUNC_ADDR = 0x0013A62C
FUNC_SIZE = 712

STUBS = {
    0x002C5FF4: "engine_func_002c5ff4",
    0x00139B64: "func_00139b64",
    0x0014672C: "func_0014672c",
    0x002C3AA8: "engine_func_002c3aa8",
    0x002C42FC: "engine_func_002c42fc",
    0x002C5468: "engine_func_002c5468",
    0x002C3A24: "engine_func_002c3a24",
    0x00146758: "func_00146758",
    0x001467AC: "func_001467ac",
}

SELF_ADDR = 0x20000000
VRAM_PTR_ADDR = 0x20010000

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
            if name == "engine_func_0013a62c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_0013a62c not found in object")

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
    init_1318: int,
    a1: int,
    sync_ret: int,
    svc19_ret: int,
    svc18_ret: int,
    num_addrs: int,
) -> tuple[bytes, bytes, list[tuple[str, tuple[object, ...]]], dict[str, int]]:
    mu = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    cpacr = mu.reg_read(arm.UC_ARM_REG_C1_C0_2)
    mu.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
    mu.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

    mu.mem_map(0x00100000, 0x00400000)
    mu.mem_map(0x20000000, 0x00100000)
    mu.mem_map(0x30000000, 0x00100000)
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
        if sname == "engine_func_002c5ff4":
            calls.append((sname, (r0, r1, r2)))
        elif sname == "func_00139b64":
            v = struct.unpack("<H", uc.mem_read(r1, 2))[0]
            calls.append((sname, (r0, v, r2)))
        elif sname == "func_0014672c":
            calls.append((sname, (r0,)))
        elif sname in ("engine_func_002c3aa8", "engine_func_002c3a24"):
            calls.append((sname, (r0,)))
        elif sname == "engine_func_002c42fc":
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            t_lo, t_hi = struct.unpack("<II", uc.mem_read(sp, 8))
            h = struct.unpack("<I", uc.mem_read(r1, 4))[0]
            calls.append((sname, (h, r2, r3, t_lo, t_hi)))
            uc.reg_write(arm.UC_ARM_REG_R0, sync_ret & 0xFFFFFFFF)
        elif sname == "engine_func_002c5468":
            calls.append((sname, (r0,)))
        elif sname == "func_00146758":
            calls.append((sname, (r0, r2)))
            if r2 == 2:
                uc.mem_write(r1, struct.pack("<H", num_addrs))
            else:
                vals = [0x10 + i for i in range(num_addrs)]
                uc.mem_write(r1, struct.pack(f"<{num_addrs}H", *vals))
        elif sname == "func_001467ac":
            calls.append((sname, (r0,)))
            uc.mem_write(r1, struct.pack("<I", 0x30000000 + (r0 & 0x1FFFF) * 0x10))

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    def hook_intr(uc: unicorn.Uc, intno: int, user_data: object) -> None:
        pc = uc.reg_read(arm.UC_ARM_REG_PC)
        insn = struct.unpack("<I", uc.mem_read(pc - 4, 4))[0]
        svc_num = insn & 0xFF
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        calls.append((f"svc_{svc_num:02x}", (r0,)))
        if svc_num == 0x19:
            uc.reg_write(arm.UC_ARM_REG_R0, svc19_ret & 0xFFFFFFFF)
        elif svc_num == 0x18:
            uc.reg_write(arm.UC_ARM_REG_R0, svc18_ret & 0xFFFFFFFF)

    mu.hook_add(unicorn.UC_HOOK_INTR, hook_intr)

    mu.mem_write(SELF_ADDR, b"\x00" * 0x1600)
    mu.mem_write(SELF_ADDR + 0x00, struct.pack("<II", 0x1111, 0x2222))
    mu.mem_write(SELF_ADDR + 0x1098, struct.pack("<I", VRAM_PTR_ADDR))
    mu.mem_write(SELF_ADDR + 0x10A8, struct.pack("<I", 0x44445555))
    mu.mem_write(SELF_ADDR + 0x1318, struct.pack("<BB", init_1318, 3))
    mu.mem_write(VRAM_PTR_ADDR, struct.pack("<H", 0))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, a1)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    self_mem = bytes(mu.mem_read(SELF_ADDR + 0x1098, 0x520))
    vram_mem = bytes(mu.mem_read(VRAM_PTR_ADDR, 4))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return self_mem, vram_mem, calls, regs


CASES = [
    dict(
        name="already_init_early_return",
        init_1318=1,
        a1=1,
        sync_ret=0,
        svc19_ret=0,
        svc18_ret=0,
        num_addrs=15,
    ),
    dict(
        name="full_init_a1_1_15_addrs",
        init_1318=0,
        a1=1,
        sync_ret=0,
        svc19_ret=0,
        svc18_ret=0,
        num_addrs=15,
    ),
    dict(
        name="init_a1_0_error_paths",
        init_1318=0,
        a1=0,
        sync_ret=-1,
        svc19_ret=-2,
        svc18_ret=-3,
        num_addrs=8,
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
        o_self, o_vram, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_self, c_vram, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_self != c_self or o_vram != c_vram:
            return False, f"{c['name']}: memory mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip init_1318 != 0 early return bne -> beq
    m1 = bytearray(b)
    off1 = 0x0013A644 - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x1
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x00000000)

    # 2. Flip a1 == 0 branch beq -> bne
    m2 = bytearray(b)
    off2 = 0x0013A658 - FUNC_ADDR
    insn2 = struct.unpack_from("<I", m2, off2)[0]
    assert (insn2 >> 28) == 0x0
    struct.pack_into("<I", m2, off2, (insn2 & 0x0FFFFFFF) | 0x10000000)

    # 3. Flip add r0, r0, #0xa00 -> #0xb00
    m3 = bytearray(b)
    off3 = 0x0013A814 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xE2800C0A
    struct.pack_into("<I", m3, off3, 0xE2800C0B)

    # 4. Flip loop bound cmp r0, #0x18 -> #0x17
    m4 = bytearray(b)
    off4 = 0x0013A888 - FUNC_ADDR
    assert struct.unpack_from("<I", m4, off4)[0] == 0xE3500018
    struct.pack_into("<I", m4, off4, 0xE3500017)

    # 5. Flip final self[0x1318] = 1 -> 0
    m5 = bytearray(b)
    off5 = 0x0013A8D4 - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE3A01001
    struct.pack_into("<I", m5, off5, 0xE3A01000)

    return [
        ("init_1318_beq", bytes(m1)),
        ("a1_zero_bne", bytes(m2)),
        ("add_a00_b00", bytes(m3)),
        ("loop_17", bytes(m4)),
        ("final_1318_0", bytes(m5)),
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
        f"PASS: engine_func_0013a62c (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
