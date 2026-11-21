#!/usr/bin/env python3
"""Differential test for script_vm_func_00240158 (0x00240158) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00240158"

FUNC_ADDR = 0x00240158
FUNC_SIZE = 712

STUBS = {
    0x002BCF58: "ui_func_002bcf58",
    0x0033A250: "func_0033a250",
    0x0033A06C: "func_0033a06c",
    0x003D7228: "func_003d7228",
    0x0027DCA0: "ui_func_0027dca0",
    0x002406F8: "func_002406f8",
    0x00250800: "battle_func_00250800",
    0x00270298: "script_vm_func_00270298",
    0x002C2BD0: "script_vm_func_002c2bd0",
    0x002C2BA4: "script_vm_func_002c2ba4",
    0x00289924: "script_vm_func_00289924",
    0x0023FD38: "battle_func_0023fd38",
}

G42C8_PTR = 0x004342C8
SELF_ADDR = 0x20000000
HDR_ADDR = 0x20001000
CTX_ADDR = 0x20002000
ARR_ADDR = 0x20008000
DST1FBC_ADDR = 0x2000C000
UNIT_ADDR = 0x2000D000

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
            if name == "script_vm_func_00240158":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("script_vm_func_00240158 not found in object")

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
    hdr_null: bool,
    f44a0: int,
    hdr_a: int,
    ver_digits: tuple[int, int, int, int],
    total_sz: int,
    cap_1e9d: int,
    f44b7: int,
    fe0: int,
    ch0: int,
    ch1: int,
    ret_289924: int,
    ret_2406f8: int,
) -> tuple[bytes, bytes, bytes, list[tuple[str, tuple[int, ...]]], dict[str, int]]:
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

    calls: list[tuple[str, tuple[int, ...]]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = STUBS[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        if sname == "ui_func_002bcf58":
            calls.append((sname, (r0, r1, r2)))
        elif sname in ("func_0033a250", "func_0033a06c", "func_003d7228", "script_vm_func_00270298"):
            calls.append((sname, (r0,)))
        elif sname == "ui_func_0027dca0":
            calls.append((sname, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, UNIT_ADDR)
        elif sname == "func_002406f8":
            calls.append((sname, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_2406f8)
        elif sname == "battle_func_00250800":
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            s4, s5, s6 = struct.unpack("<III", uc.mem_read(sp, 12))
            calls.append((sname, (r0, r1, r2, uc.reg_read(arm.UC_ARM_REG_R3), s4, s5, s6)))
        elif sname == "script_vm_func_002c2bd0":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, ch0 if r0 == 0 else ch1)
        elif sname == "script_vm_func_002c2ba4":
            calls.append((sname, (r0, r1, r2)))
        elif sname == "script_vm_func_00289924":
            calls.append((sname, ()))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_289924)
        elif sname == "battle_func_0023fd38":
            calls.append((sname, (r0, r1)))

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G42C8_PTR, struct.pack("<I", 0x20050000))
    mu.mem_write(SELF_ADDR, struct.pack("<IIII", 0, 0 if hdr_null else HDR_ADDR, 0, 0x999))
    mu.mem_write(HDR_ADDR, b"\x00" * 0x20)
    mu.mem_write(HDR_ADDR + 4, struct.pack("<4bHBxI", *ver_digits, 0x20, hdr_a, total_sz))

    mu.mem_write(CTX_ADDR, b"\x00" * 0x5000)
    mu.mem_write(CTX_ADDR + 0xE0, struct.pack("<I", fe0))
    mu.mem_write(CTX_ADDR + 0x1E98, struct.pack("<I", ARR_ADDR))
    mu.mem_write(CTX_ADDR + 0x1E9D, struct.pack("<B", cap_1e9d))
    mu.mem_write(CTX_ADDR + 0x1EA4, struct.pack("<7I", *([0xAAAAAAAA] * 7)))
    mu.mem_write(CTX_ADDR + 0x1FBC, struct.pack("<I", DST1FBC_ADDR))
    mu.mem_write(CTX_ADDR + 0x44A0, struct.pack("<I", f44a0))
    mu.mem_write(CTX_ADDR + 0x44B7, struct.pack("<B", f44b7))

    mu.mem_write(ARR_ADDR, b"\x00" * (0x36 * 0x114))
    for i in (4, 10, 0x35):
        e = ARR_ADDR + i * 0x114
        mu.mem_write(e + 0x50, struct.pack("<II", 3, 8))
        mu.mem_write(e + 0x58, struct.pack("<H", 0))
        mu.mem_write(e + 0x62, struct.pack("<h", i))
    mu.mem_write(UNIT_ADDR + 2, struct.pack("<H", 0x123))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, CTX_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    self_mem = bytes(mu.mem_read(SELF_ADDR, 0x10))
    ctx_mem = bytes(mu.mem_read(CTX_ADDR + 0x1EA4, 0x20)) + bytes(mu.mem_read(CTX_ADDR + 0x44A0, 4))
    arr_mem = bytes(mu.mem_read(ARR_ADDR, 0x36 * 0x114))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return self_mem, ctx_mem, arr_mem, calls, regs


CASES = [
    dict(
        name="hdr_null_early_ret",
        hdr_null=True,
        f44a0=0,
        hdr_a=1,
        ver_digits=(54, 4, 2, 8),
        total_sz=0x118 + 48,
        cap_1e9d=5,
        f44b7=0,
        fe0=0,
        ch0=0,
        ch1=0,
        ret_289924=0,
        ret_2406f8=0,
    ),
    dict(
        name="ver_1100_copy_and_full_loop",
        hdr_null=False,
        f44a0=0,
        hdr_a=1,
        ver_digits=(54, 4, 2, 8),  # 54*1000+400+20+8 - 53328 = 1100 (0x44c)
        total_sz=0x118 + 72,
        cap_1e9d=2,
        f44b7=0,
        fe0=0x02000000,
        ch0=3,
        ch1=3,
        ret_289924=1,
        ret_2406f8=0,
    ),
    dict(
        name="ver_other_skip_loop_already_flagged",
        hdr_null=False,
        f44a0=0x40000202,
        hdr_a=1,
        ver_digits=(54, 4, 2, 9),
        total_sz=0x118 + 24,
        cap_1e9d=5,
        f44b7=1,
        fe0=0,
        ch0=1,
        ch1=3,
        ret_289924=0,
        ret_2406f8=1,
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
        o_self, o_ctx, o_arr, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_self, c_ctx, c_arr, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_self != c_self or o_ctx != c_ctx or o_arr != c_arr:
            return False, f"{c['name']}: memory mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip hdr[0xA] == 1 check cmp r1, #1 -> #2
    m1 = bytearray(b)
    off1 = 0x00240190 - FUNC_ADDR
    assert struct.unpack_from("<I", m1, off1)[0] == 0xE3510001
    struct.pack_into("<I", m1, off1, 0xE3510002)

    # 2. Flip ver == 0x44C branch bne -> beq
    m2 = bytearray(b)
    off2 = 0x0024021C - FUNC_ADDR
    insn2 = struct.unpack_from("<I", m2, off2)[0]
    assert (insn2 >> 28) == 0x1
    struct.pack_into("<I", m2, off2, (insn2 & 0x0FFFFFFF) | 0x00000000)

    # 3. Flip loop bound cmp r4, #0x36 -> #0x35
    m3 = bytearray(b)
    off3 = 0x00240330 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xE3540036
    struct.pack_into("<I", m3, off3, 0xE3540035)

    # 4. Flip self[0] = 0xd -> 0xc
    m4 = bytearray(b)
    off4 = 0x00240358 - FUNC_ADDR
    assert struct.unpack_from("<I", m4, off4)[0] == 0xE3A0000D
    struct.pack_into("<I", m4, off4, 0xE3A0000C)

    # 5. Flip ch0 == 3 check cmp r0, #3 -> #4
    m5 = bytearray(b)
    off5 = 0x00240388 - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE3500003
    struct.pack_into("<I", m5, off5, 0xE3500004)

    return [
        ("hdr_null_bne", bytes(m1)),
        ("ver_44c_beq", bytes(m2)),
        ("loop_35", bytes(m3)),
        ("self0_c", bytes(m4)),
        ("ch0_cmp_4", bytes(m5)),
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
        f"PASS: script_vm_func_00240158 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
