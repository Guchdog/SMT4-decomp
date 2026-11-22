#!/usr/bin/env python3
"""Differential test for engine_func_002eef44 (0x002eef44) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002eef44"

FUNC_ADDR = 0x002EEF44
FUNC_SIZE = 728
LUT_ADDR = 0x00407FC0

STUBS = {
    0x00296F60: "engine_func_00296f60",
    0x002AD6D8: "battle_func_002ad6d8",
    0x0027FE84: "script_vm_func_0027fe84",
    0x0027FD08: "script_vm_func_0027fd08",
    0x00273AB0: "script_vm_func_00273ab0",
}

G_CAM = 0x0049F91C
G_ST_PTR = 0x004474F4
ST_ADDR = 0x20000000

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


def build_lut() -> bytes:
    out = bytearray()
    for i in range(256):
        a0 = 2.0 * math.pi * i / 256.0
        a1 = 2.0 * math.pi * (i + 1) / 256.0
        s0, c0 = math.sin(a0), math.cos(a0)
        s1, c1 = math.sin(a1), math.cos(a1)
        out.extend(struct.pack("<4f", s0, c0, s1 - s0, c1 - c0))
    return bytes(out)


LUT_BYTES = build_lut()


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
            if name == "engine_func_002eef44":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_002eef44 not found in object")

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
    cam_vals: tuple[int, int, int, int],
    st_mode: int,
) -> tuple[int, bytes, bytes, list[tuple[str, tuple[object, ...]]], dict[str, int]]:
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
    mu.mem_write(LUT_ADDR, LUT_BYTES)
    for addr in STUBS:
        mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[str, tuple[object, ...]]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = STUBS[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        if sname == "engine_func_00296f60":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, cam_vals[r0] & 0xFFFFFFFF)
        elif sname == "battle_func_002ad6d8":
            mtx = struct.unpack("<12f", uc.mem_read(r1, 48))
            vin = struct.unpack("<3f", uc.mem_read(r2, 12))
            vout = (
                mtx[0] * vin[0] + mtx[1] * vin[1] + mtx[2] * vin[2],
                mtx[4] * vin[0] + mtx[5] * vin[1] + mtx[6] * vin[2],
                mtx[8] * vin[0] + mtx[9] * vin[1] + mtx[10] * vin[2],
            )
            uc.mem_write(r0, struct.pack("<3f", *vout))
            calls.append((sname, tuple(round(x, 5) for x in vout)))
        elif sname in ("script_vm_func_0027fe84", "script_vm_func_0027fd08", "script_vm_func_00273ab0"):
            calls.append((sname, (r0,)))

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G_CAM + 0xC4, b"\x00" * 0x20)
    mu.mem_write(G_ST_PTR, struct.pack("<I", ST_ADDR))
    mu.mem_write(ST_ADDR, b"\x00" * 0xB0)
    mu.mem_write(ST_ADDR, struct.pack("<I", st_mode))

    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=100000)

    ret = mu.reg_read(arm.UC_ARM_REG_R0)
    cam_mem = bytes(mu.mem_read(G_CAM + 0xC4, 0x1C))
    st_mem = bytes(mu.mem_read(ST_ADDR + 0xA4, 4))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return ret, cam_mem, st_mem, calls, regs


CASES = [
    dict(name="mode_not_3_pos_yaw", cam_vals=(100, 200, 300, 45), st_mode=1),
    dict(name="mode_3_neg_yaw", cam_vals=(-50, 0, 150, -90), st_mode=3),
    dict(name="mode_0_zero_yaw", cam_vals=(0, 10, -20, 0), st_mode=0),
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
        o_ret, o_cam, o_st, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_ret, c_cam, c_st, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_ret != c_ret or o_cam != c_cam or o_st != c_st:
            return False, f"{c['name']}: ret/memory mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch orig={o_calls} cand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip st_mode == 3 check cmp r1, #3 -> #4
    m1 = bytearray(b)
    off1 = 0x002EF1B8 - FUNC_ADDR
    assert struct.unpack_from("<I", m1, off1)[0] == 0xE3510003
    struct.pack_into("<I", m1, off1, 0xE3510004)

    # 2. Flip st[0xA4] = 1 -> 0
    m2 = bytearray(b)
    off2 = 0x002EF1C0 - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0xE3A01001
    struct.pack_into("<I", m2, off2, 0xE3A01000)

    # 3. Flip return value mov r0, #1 -> #0
    m3 = bytearray(b)
    off3 = 0x002EF1E8 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xE3A00001
    struct.pack_into("<I", m3, off3, 0xE3A00000)

    # 4. Flip script_vm_func_0027fe84 arg mov r0, #3 -> #4
    m4 = bytearray(b)
    off4 = 0x002EF1C8 - FUNC_ADDR
    assert struct.unpack_from("<I", m4, off4)[0] == 0xE3A00003
    struct.pack_into("<I", m4, off4, 0xE3A00004)

    # 5. Flip script_vm_func_00273ab0 arg mov r0, #1 -> #0
    m5 = bytearray(b)
    off5 = 0x002EF1DC - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE3A00001
    struct.pack_into("<I", m5, off5, 0xE3A00000)

    return [
        ("st_mode_4", bytes(m1)),
        ("st_a4_0", bytes(m2)),
        ("ret_0", bytes(m3)),
        ("fe84_arg_4", bytes(m4)),
        ("3ab0_arg_0", bytes(m5)),
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
        f"PASS: engine_func_002eef44 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
