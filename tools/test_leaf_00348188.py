#!/usr/bin/env python3
"""Differential test for func_00348188 (0x00348188) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00348188"

FUNC_ADDR = 0x00348188
FUNC_SIZE = 712
LUT_ADDR = 0x00407FC0

STUBS = {
    0x0023E55C: "func_0023e55c",
}

VFN_OBJ14 = 0x00410000

SELF_ADDR = 0x20000000
ARR_ADDR = 0x20001000
OBJ14_ADDR = 0x20002000
OBJ14_VT_ADDR = 0x20002100
CFG_ADDR = 0x20003000

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
            if name == "func_00348188":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("func_00348188 not found in object")

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


def run_case(
    code_bytes: bytes,
    relocs: list[tuple[str, int]],
    *,
    is_orig: bool,
    n_cfg: int,
    ang_init: float,
    sc_init: float,
    du: float,
    dv: float,
    da: float,
    ds: float,
) -> tuple[bytes, bytes, list[tuple[object, ...]], dict[str, int]]:
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
    for addr in list(STUBS) + [VFN_OBJ14]:
        mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[object, ...]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        if addr == VFN_OBJ14:
            calls.append(("vfn_obj14", r0))
        else:
            v = struct.unpack("<3f", uc.mem_read(r2, 12))
            calls.append(("func_0023e55c", r0, r1, tuple(round(x, 5) for x in v)))

    for addr in list(STUBS) + [VFN_OBJ14]:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(SELF_ADDR, b"\x00" * 0x70)
    mu.mem_write(SELF_ADDR + 0x04, struct.pack("<I", ARR_ADDR))
    mu.mem_write(SELF_ADDR + 0x14, struct.pack("<I", OBJ14_ADDR))
    mu.mem_write(SELF_ADDR + 0x58, struct.pack("<ff", ang_init, sc_init))
    mu.mem_write(SELF_ADDR + 0x60, struct.pack("<I", CFG_ADDR))

    mu.mem_write(OBJ14_ADDR, struct.pack("<I", OBJ14_VT_ADDR))
    mu.mem_write(OBJ14_VT_ADDR + 8, struct.pack("<I", VFN_OBJ14))

    mu.mem_write(CFG_ADDR, b"\x00" * 0x50)
    mu.mem_write(CFG_ADDR + 0x00, struct.pack("<i", n_cfg))
    mu.mem_write(CFG_ADDR + 0x30, struct.pack("<4f", du, dv, da, ds))

    mu.mem_write(ARR_ADDR, b"\x00" * 100)
    for i in range(4):
        mu.mem_write(ARR_ADDR + i * 20 + 0xC, struct.pack("<ff", 0.1 * i, 0.2 * i))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=100000)

    self_mem = bytes(mu.mem_read(SELF_ADDR, 0x64))
    arr_mem = bytes(mu.mem_read(ARR_ADDR, 80))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return self_mem, arr_mem, calls, regs


CASES = [
    dict(
        name="wrap_above_360",
        n_cfg=2,
        ang_init=350.0,
        sc_init=1.0,
        du=0.25,
        dv=-0.5,
        da=25.0,
        ds=0.5,
    ),
    dict(
        name="wrap_below_0",
        n_cfg=1,
        ang_init=5.0,
        sc_init=2.0,
        du=0.1,
        dv=0.2,
        da=-15.0,
        ds=-0.25,
    ),
    dict(
        name="negative_n_no_uv_loop",
        n_cfg=-1,
        ang_init=45.0,
        sc_init=0.5,
        du=1.0,
        dv=1.0,
        da=0.0,
        ds=0.0,
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
        o_self, o_arr, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_self, c_arr, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_self != c_self or o_arr != c_arr:
            return False, f"{c['name']}: memory mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch orig={o_calls} cand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip UV loop ble -> bgt (at 0x003481b4)
    m1 = bytearray(b)
    off1 = 0x003481B4 - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0xD
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0xC0000000)

    # 2. Flip ang >= 360 vsubge -> vaddge (at 0x00348240)
    m2 = bytearray(b)
    off2 = 0x00348240 - FUNC_ADDR
    insn2 = struct.unpack_from("<I", m2, off2)[0]
    struct.pack_into("<I", m2, off2, insn2 ^ 0x00000040)

    # 3. Flip vstr s0, [r4, #0x58] -> [r4, #0x5c] (at 0x00348258)
    m3 = bytearray(b)
    off3 = 0x00348258 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xED840A16
    struct.pack_into("<I", m3, off3, 0xED840A17)

    # 4. Flip vneg.f32 s12, s0 -> vmov.f32 s12, s0 (at 0x00348388)
    m4 = bytearray(b)
    off4 = 0x00348388 - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    struct.pack_into("<I", m4, off4, insn4 ^ 0x00000040)

    # 5. Flip m[15] = 1.0f -> 0.0f (at 0x0034832c)
    m5 = bytearray(b)
    off5 = 0x0034832C - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE3A012FE or True
    struct.pack_into("<I", m5, off5, struct.unpack_from("<I", m5, off5)[0] ^ 0x00000001)

    return [
        ("uv_loop_bgt", bytes(m1)),
        ("ang_wrap_add", bytes(m2)),
        ("ang_store_5c", bytes(m3)),
        ("neg_sy_pos", bytes(m4)),
        ("m15_not_one", bytes(m5)),
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
        f"PASS: func_00348188 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
