#!/usr/bin/env python3
"""Differential test for engine_func_00352d98 (0x00352d98) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00352d98"

FUNC_ADDR = 0x00352D98
FUNC_SIZE = 740

STUBS = {
    0x003538D4: "func_003538d4",
    0x003538B8: "func_003538b8",
    0x003538C4: "func_003538c4",
    0x0035334C: "func_0035334c",
    0x0023A3A4: "func_0023a3a4",
    0x003532A8: "func_003532a8",
    0x0035FAD8: "func_0035fad8",
    0x002B45F8: "engine_func_002b45f8",
    0x002C607C: "script_vm_func_002c607c",
    0x0035382C: "func_0035382c",
}

G_471A50 = 0x00471A50
G_471A54 = 0x00471A54

SELF_ADDR = 0x20000000
HDR_ADDR = 0x20001000
ITEMS_ADDR = 0x20002000
PAIRS_ADDR = 0x20003000
STR_KEY_ADDR = 0x20004000
STR_VAL_ADDR = 0x20004100
A3_ADDR = 0x20005000
RODATA_BASE = 0x00450000

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


def compile_candidate() -> tuple[bytes, list[tuple[str, int]], bytes, list[tuple[int, int, int]]]:
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
            if name == "engine_func_00352d98":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_00352d98 not found in object")

    # Gather .rodata* sections sequentially into a single blob
    ro_blob = bytearray()
    sec_to_ro_off: dict[int, int] = {}
    for idx, s in enumerate(shdrs):
        nm = sh_name(idx)
        if nm.startswith(".rodata"):
            sec_to_ro_off[idx] = len(ro_blob)
            ro_blob.extend(data[s[4] : s[4] + s[5]])
            while len(ro_blob) % 4:
                ro_blob.append(0)

    relocs: list[tuple[str, int]] = []
    abs_relocs: list[tuple[int, int, int]] = []
    for s in shdrs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if fn_off <= r_off < fn_off + fn_size:
                    st_name, st_value, _, _, _, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + sym_idx * 16)
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    if r_type in (28, 29):
                        relocs.append((sname, r_off - fn_off))
                    elif r_type == 2 and st_shndx in sec_to_ro_off:  # R_ARM_ABS32
                        abs_relocs.append((r_off - fn_off, sec_to_ro_off[st_shndx] + st_value, r_type))

    return bytes(text_data[fn_off : fn_off + fn_size]), relocs, bytes(ro_blob), abs_relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def read_cstr(uc: unicorn.Uc, addr: int) -> str:
    if addr == 0:
        return "<NULL>"
    raw = uc.mem_read(addr, 64)
    return raw.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def run_case(
    code_bytes: bytes,
    relocs: list[tuple[str, int]],
    ro_blob: bytes,
    abs_relocs: list[tuple[int, int, int]],
    *,
    is_orig: bool,
    ret_3538d4: int,
    ret_35fad8: int,
    ret_35382c: int,
    a3_0: int,
    a3_8: int,
    a3_18: int,
    items: list[tuple[int, int, int]],
    key_match: bool,
) -> tuple[int, list[tuple[str, tuple[object, ...]]], dict[str, int]]:
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
        if ro_blob:
            mu.mem_write(RODATA_BASE, ro_blob)
        for off, ro_off, _ in abs_relocs:
            cur = struct.unpack_from("<I", buf, off)[0]
            struct.pack_into("<I", buf, off, cur + RODATA_BASE + ro_off)
        for sname, off in relocs:
            if sname not in name_to_addr:
                raise RuntimeError(f"Unexpected reloc target: {sname}")
            patch_bl(buf, off, entry + off, name_to_addr[sname])

    mu.mem_write(entry, bytes(buf))
    for addr in STUBS:
        if is_orig and addr == 0x002C607C:
            # Verify whether orig uses blx #0x2c607c (Thumb!)
            mu.mem_write(addr, struct.pack("<H", 0x4770))
        else:
            mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[str, tuple[object, ...]]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = STUBS[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        if sname == "func_003538d4":
            calls.append((sname, (r0, r1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_3538d4 & 0xFFFFFFFF)
        elif sname == "func_003538b8":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x1111)
        elif sname == "func_003538c4":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x2222)
        elif sname == "func_0035334c":
            calls.append((sname, ()))
        elif sname == "func_0023a3a4":
            calls.append((sname, (read_cstr(uc, r0),)))
        elif sname == "func_003532a8":
            calls.append((sname, (r0,)))
        elif sname == "func_0035fad8":
            sp = uc.reg_read(arm.UC_ARM_REG_SP)
            stack_words = struct.unpack("<15I", uc.mem_read(sp, 60))
            calls.append((sname, (r0, r1, r2, r3, stack_words)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_35fad8 & 0xFFFFFFFF)
        elif sname == "engine_func_002b45f8":
            s0 = read_cstr(uc, r0)
            s1 = read_cstr(uc, r1)
            calls.append((sname, (s0, s1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0 if s0 == s1 else 1)
        elif sname == "script_vm_func_002c607c":
            calls.append((sname, (read_cstr(uc, r0), r1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, 1234 if r0 != 0 else 0)
        elif sname == "func_0035382c":
            p0, p1 = struct.unpack("<II", uc.mem_read(r1, 8))
            calls.append((sname, (r0, p0, p1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_35382c & 0xFFFFFFFF)

    for addr in STUBS:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G_471A50, struct.pack("<I", 0xAAAA0001))
    mu.mem_write(G_471A54, struct.pack("<I", 0xAAAA0002))

    mu.mem_write(A3_ADDR, b"\x00" * 0x40)
    mu.mem_write(A3_ADDR + 0x00, struct.pack("<IIII", a3_0, 0x3333, a3_8, 0x4444))
    mu.mem_write(A3_ADDR + 0x10, struct.pack("<III", 0x5555, 0x6666, a3_18))
    mu.mem_write(A3_ADDR + 0x28, struct.pack("<B", 0x77))
    mu.mem_write(A3_ADDR + 0x2C, struct.pack("<II", 0x8888, 0x9999))

    mu.mem_write(SELF_ADDR, struct.pack("<IIII", 0, HDR_ADDR if items else 0, 0x12, 0x34))
    mu.mem_write(HDR_ADDR, struct.pack("<II", ITEMS_ADDR, len(items)))

    mu.mem_write(STR_KEY_ADDR, b"TitleVersion\x00" if key_match else b"other.Key\x00")
    mu.mem_write(STR_VAL_ADDR, b"999\x00")

    for i, (w0, w4, cnt) in enumerate(items):
        base = ITEMS_ADDR + i * 0x30
        mu.mem_write(base, b"\x00" * 0x30)
        mu.mem_write(base + 0x00, struct.pack("<II", w0, w4))
        mu.mem_write(base + 0x18, struct.pack("<II", PAIRS_ADDR, cnt))
    mu.mem_write(PAIRS_ADDR, struct.pack("<II", STR_KEY_ADDR, STR_VAL_ADDR))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, 0x11)
    mu.reg_write(arm.UC_ARM_REG_R2, 0x22)
    mu.reg_write(arm.UC_ARM_REG_R3, A3_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    ret = mu.reg_read(arm.UC_ARM_REG_R0)
    if ret & 0x80000000:
        ret -= 0x100000000
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return ret, calls, regs


CASES = [
    dict(
        name="early_fail_3538d4",
        ret_3538d4=-5,
        ret_35fad8=0,
        ret_35382c=0,
        a3_0=0,
        a3_8=0,
        a3_18=0,
        items=[],
        key_match=False,
    ),
    dict(
        name="full_3_items_all_w4_modes",
        ret_3538d4=0,
        ret_35fad8=0,
        ret_35382c=0,
        a3_0=0x20007000,
        a3_8=0x20007100,
        a3_18=0x20007200,
        items=[
            (0x12345678, (0x10 << 14) | 0x8C, 1),
            (0xABCDEF01, (0x10 << 14) | 0x0D, 1),
            (0x55667788, (0x05 << 14) | 0x22, 0),
        ],
        key_match=True,
    ),
    dict(
        name="fail_35382c_and_key_miss",
        ret_3538d4=0,
        ret_35fad8=0,
        ret_35382c=-9,
        a3_0=0,
        a3_8=0,
        a3_18=0,
        items=[(0x11223344, 0x01020304, 1)],
        key_match=False,
    ),
    dict(
        name="fail_35fad8",
        ret_3538d4=0,
        ret_35fad8=-7,
        ret_35382c=0,
        a3_0=0,
        a3_8=0,
        a3_18=0,
        items=[],
        key_match=False,
    ),
]


def check_pair(
    orig_bytes: bytes,
    cand_bytes: bytes,
    relocs: list[tuple[str, int]],
    ro_blob: bytes,
    abs_relocs: list[tuple[int, int, int]],
    *,
    cand_is_orig: bool = False,
) -> tuple[bool, str]:
    for c in CASES:
        kw = {k: v for k, v in c.items() if k != "name"}
        o_ret, o_calls, o_regs = run_case(orig_bytes, [], b"", [], is_orig=True, **kw)
        c_ret, c_calls, c_regs = run_case(cand_bytes, relocs, ro_blob, abs_relocs, is_orig=cand_is_orig, **kw)
        if o_ret != c_ret:
            return False, f"{c['name']}: ret mismatch orig={o_ret} cand={c_ret}"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip 3538d4 < 0 branch bne -> beq
    m1 = bytearray(b)
    off1 = 0x00352DC0 - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x1
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x00000000)

    # 2. Flip 0x8C check cmpeq ip, #0x8c -> #0x8d
    m2 = bytearray(b)
    off2 = 0x00352F9C - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0x035C008C
    struct.pack_into("<I", m2, off2, 0x035C008D)

    # 3. Flip 0xD check cmpeq r0, #0xd -> #0xe
    m3 = bytearray(b)
    off3 = 0x00352FB4 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0x0350000D
    struct.pack_into("<I", m3, off3, 0x0350000E)

    # 4. Flip strtol base mov r2, #0xa -> #0x10
    m4 = bytearray(b)
    off4 = 0x00352F70 - FUNC_ADDR
    assert struct.unpack_from("<I", m4, off4)[0] == 0xE3A0200A
    struct.pack_into("<I", m4, off4, 0xE3A02010)

    # 5. Flip key_match branch beq -> bne (at 0x00352f5c)
    m5 = bytearray(b)
    off5 = 0x00352F5C - FUNC_ADDR
    insn5 = struct.unpack_from("<I", m5, off5)[0]
    assert (insn5 >> 28) == 0x0
    struct.pack_into("<I", m5, off5, (insn5 & 0x0FFFFFFF) | 0x10000000)

    return [
        ("3538d4_beq", bytes(m1)),
        ("cmp_8d", bytes(m2)),
        ("cmp_e", bytes(m3)),
        ("base_16", bytes(m4)),
        ("key_bne", bytes(m5)),
    ]


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    start = FUNC_ADDR - 0x00100000
    orig_bytes = orig_all[start : start + FUNC_SIZE]

    cand_bytes, relocs, ro_blob, abs_relocs = compile_candidate()
    ok, msg = check_pair(orig_bytes, cand_bytes, relocs, ro_blob, abs_relocs)
    if not ok:
        print(f"FAIL: {msg}")
        return 1

    detected = 0
    for mname, mbytes in mutate_bytes(orig_bytes):
        mok, _ = check_pair(orig_bytes, mbytes, [], b"", [], cand_is_orig=True)
        if not mok:
            detected += 1
        else:
            print(f"FAIL: mutant {mname} was not detected")
            return 1

    print(
        f"PASS: engine_func_00352d98 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
