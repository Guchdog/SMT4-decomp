#!/usr/bin/env python3
"""Differential test for camp_func_002626fc (0x002626fc) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_002626fc"

FUNC_ADDR = 0x002626FC
FUNC_SIZE = 684

STUBS = {
    0x00311D20: "camp_func_00311d20",
    0x0029ED44: "camp_func_0029ed44",
    0x003C8FDC: "camp_func_003c8fdc",
    0x002B9364: "camp_func_002b9364",
    0x0029EC14: "camp_func_0029ec14",
    0x002B7F0A: "func_002b7f0a",
    0x003C997C: "camp_func_003c997c",
}

SELF_ADDR = 0x20000000
OUT_ADDR = 0x20001000
PAIR_ADDR = 0x20002000
INFO_ADDR = 0x20003000
SINFO_BASE = 0x20004000

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
            if name == "camp_func_002626fc":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("camp_func_002626fc not found in object")

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
    id1: int,
    id2: int,
    pair_null: bool,
    res_id: int,
    ret_29ed44: int,
    ret_3c8fdc: int,
    init_count: int,
    init_slots: list[int],
    info_skills: list[int],
    flag_17d: int,
) -> tuple[int, bytes, bytes, list[tuple[str, tuple[int, ...]]], dict[str, int]]:
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
            dst = name_to_addr[sname]
            if dst & 2:
                dst = 0x002B7F00
            patch_bl(buf, off, entry + off, dst)

    mu.mem_write(entry, bytes(buf))
    for addr in STUBS:
        if addr == 0x002B7F0A:
            # Put Thumb bx lr at 0x002b7f0a and ARM bx lr at 0x002b7f00
            mu.mem_write(0x002B7F00, make_stub_bx_lr())
            mu.mem_write(0x002B7F0A, struct.pack("<H", 0x4770))
        else:
            mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[str, tuple[int, ...]]] = []

    addr_to_name = dict(STUBS)
    addr_to_name[0x002B7F00] = "func_002b7f0a"

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        sname = addr_to_name[addr]
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        if sname == "camp_func_00311d20":
            calls.append((sname, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0 if pair_null else PAIR_ADDR)
        elif sname == "camp_func_0029ed44":
            calls.append((sname, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_29ed44)
        elif sname == "camp_func_003c8fdc":
            calls.append((sname, (r0, r1, r2, r3)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_3c8fdc)
        elif sname == "camp_func_002b9364":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, INFO_ADDR)
        elif sname == "camp_func_0029ec14":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, SINFO_BASE + (r0 & 0xF) * 0x10)
        elif sname == "func_002b7f0a":
            calls.append((sname, (r0, r1, r2, r3)))
            # Sort non-zero elements to the front, zeros at the back (deterministic mock qsort)
            arr = list(struct.unpack(f"<{r1}H", uc.mem_read(r0, r1 * 2))) if r1 > 0 else []
            arr.sort(key=lambda x: (x == 0, -x))
            if r1 > 0:
                uc.mem_write(r0, struct.pack(f"<{r1}H", *arr))
        elif sname == "camp_func_003c997c":
            calls.append((sname, (r0, r1, r2, r3)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x42)

    for addr in addr_to_name:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(PAIR_ADDR, struct.pack("<II", 0, res_id))
    mu.mem_write(OUT_ADDR, struct.pack("<II", 0xDEADBEEF, 0xCAFEBABE))

    mu.mem_write(SELF_ADDR, b"\x00" * 0x200)
    for idx, val in enumerate(init_slots):
        mu.mem_write(SELF_ADDR + 0x146 + idx * 2, struct.pack("<H", val))
    mu.mem_write(SELF_ADDR + 0x178, struct.pack("<I", init_count))
    mu.mem_write(SELF_ADDR + 0x17D, struct.pack("<B", flag_17d))

    mu.mem_write(INFO_ADDR, b"\x00" * 0x80)
    mu.mem_write(INFO_ADDR + 3, struct.pack("<B", 7))
    mu.mem_write(INFO_ADDR + 0x1A, struct.pack("<5H", 10, 20, 30, 40, 50))
    for i, sk in enumerate(info_skills):
        mu.mem_write(INFO_ADDR + 0x3C + i * 2, struct.pack("<H", sk))

    for i in range(16):
        # Even ids have 0x20 bit set (valid), odd ids do not
        b3 = (0x20 | (i & 0x1F)) if (i % 2 == 0) else (i & 0x1F)
        mu.mem_write(SINFO_BASE + i * 0x10 + 3, struct.pack("<B", b3))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, id1)
    mu.reg_write(arm.UC_ARM_REG_R2, id2)
    mu.reg_write(arm.UC_ARM_REG_R3, OUT_ADDR)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, val in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), val)

    mu.emu_start(entry, LR_SENTINEL, count=100000)

    ret = mu.reg_read(arm.UC_ARM_REG_R0)
    out_mem = bytes(mu.mem_read(OUT_ADDR, 8))
    self_mem = bytes(mu.mem_read(SELF_ADDR + 0x146, 0x38))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return ret, out_mem, self_mem, calls, regs


CASES = [
    dict(
        name="full_fusion_cost",
        id1=0x0102,
        id2=0x0204,
        pair_null=False,
        res_id=0x0345,
        ret_29ed44=1,
        ret_3c8fdc=1,
        init_count=2,
        init_slots=[2, 3],
        info_skills=[4, 5, 6, 0, 8, 0, 10, 12],
        flag_17d=1,
    ),
    dict(
        name="swapped_ids_no_cost",
        id1=0x0500,
        id2=0x0100,
        pair_null=False,
        res_id=0x0123,
        ret_29ed44=1,
        ret_3c8fdc=1,
        init_count=1,
        init_slots=[2],
        info_skills=[4, 0, 0, 0, 0, 0, 0, 0],
        flag_17d=0,
    ),
    dict(
        name="pair_null",
        id1=10,
        id2=20,
        pair_null=True,
        res_id=0x111,
        ret_29ed44=1,
        ret_3c8fdc=1,
        init_count=0,
        init_slots=[],
        info_skills=[0] * 8,
        flag_17d=1,
    ),
    dict(
        name="fail_3c8fdc",
        id1=10,
        id2=20,
        pair_null=False,
        res_id=0x111,
        ret_29ed44=1,
        ret_3c8fdc=0,
        init_count=0,
        init_slots=[],
        info_skills=[0] * 8,
        flag_17d=1,
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
        o_ret, o_out, o_self, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_ret, c_out, c_self, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_ret != c_ret:
            return False, f"{c['name']}: ret mismatch orig={o_ret} cand={c_ret}"
        if o_out != c_out:
            return False, f"{c['name']}: out mismatch orig={o_out.hex()} cand={c_out.hex()}"
        if o_self != c_self:
            return False, f"{c['name']}: self mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch orig={o_calls} cand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip id1 < id2 branch bhs -> blo
    m1 = bytearray(b)
    off1 = 0x00262718 - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x2
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x30000000)

    # 2. Flip cmp r0, #8 -> #7 in skill copy loop
    m2 = bytearray(b)
    off2 = 0x00262830 - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0xE3500008
    struct.pack_into("<I", m2, off2, 0xE3500007)

    # 3. Flip tst r0, #0x20 -> #0x40
    m3 = bytearray(b)
    off3 = 0x00262870 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xE3100020
    struct.pack_into("<I", m3, off3, 0xE3100040)

    # 4. Flip flag_17d == 0 branch beq -> bne
    m4 = bytearray(b)
    off4 = 0x002628E8 - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    assert (insn4 >> 28) == 0x0
    struct.pack_into("<I", m4, off4, (insn4 & 0x0FFFFFFF) | 0x10000000)

    # 5. Flip cost shift lsl #17 -> lsl #18
    m5 = bytearray(b)
    off5 = 0x00262964 - FUNC_ADDR
    insn5 = struct.unpack_from("<I", m5, off5)[0]
    struct.pack_into("<I", m5, off5, insn5 ^ 0x00000080)

    return [
        ("id1_id2_blo", bytes(m1)),
        ("skill_loop_7", bytes(m2)),
        ("skill_flag_40", bytes(m3)),
        ("flag_17d_bne", bytes(m4)),
        ("cost_shift_18", bytes(m5)),
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
        f"PASS: camp_func_002626fc (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
