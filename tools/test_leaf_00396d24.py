#!/usr/bin/env python3
"""Differential test for engine_func_00396d24 (0x00396d24) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_00396d24"

FUNC_ADDR = 0x00396D24
FUNC_SIZE = 740

STUBS = {
    0x002C0BCC: "engine_func_002c0bcc",
    0x0024F734: "script_vm_func_0024f734",
    0x00253634: "camp_func_00253634",
    0x00232C00: "engine_func_00232c00",
    0x00232B3C: "engine_func_00232b3c",
    0x00232B28: "func_00232b28",
    0x00232B14: "func_00232b14",
    0x00232B00: "func_00232b00",
    0x001E2860: "func_001e2860",
    0x001FA3F4: "battle_func_001fa3f4",
    0x002C0BA8: "script_vm_func_002c0ba8",
}

VFN_14 = 0x00410000
G_447E88 = 0x00447E88

SELF_ADDR = 0x20000000
REF_ADDR = 0x20001000
SLOT0_ADDR = 0x20002000
ENT_ADDR = 0x20003000
ENT_VT_ADDR = 0x20003100
PT_BASE = 0x20004000

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
            if name == "engine_func_00396d24":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_00396d24 not found in object")

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
    mode: int,
    ids: list[int],
    used_id: int,
    pts: dict[int, tuple[int, int, int]],
    ent_null: bool,
    ret_2c0ba8: int,
) -> tuple[bytes, list[tuple[str, tuple[object, ...]]], dict[str, int]]:
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
    for addr in list(STUBS) + [VFN_14]:
        mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[str, tuple[object, ...]]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        if addr == VFN_14:
            calls.append(("vfn_14", (r0,)))
            return
        sname = STUBS[addr]
        if sname == "engine_func_002c0bcc":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, r0)  # pick last valid index
        elif sname == "script_vm_func_0024f734":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, PT_BASE + (r0 & 0xF) * 0x10)
        elif sname == "camp_func_00253634":
            calls.append((sname, (r0, r1)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x4242)
        elif sname == "engine_func_00232c00":
            calls.append((sname, (r0, r1, r2)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0 if ent_null else ENT_ADDR)
        elif sname == "engine_func_00232b3c":
            calls.append((sname, (r0, r1)))
        elif sname in ("func_00232b28", "func_00232b14", "func_00232b00"):
            vec = struct.unpack("<3f", uc.mem_read(r1, 12))
            calls.append((sname, (r0, tuple(round(x, 4) for x in vec))))
        elif sname == "func_001e2860":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x7777)
        elif sname == "battle_func_001fa3f4":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x8888)
        elif sname == "script_vm_func_002c0ba8":
            calls.append((sname, (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, ret_2c0ba8)

    for addr in list(STUBS) + [VFN_14]:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G_447E88, struct.pack("<I", REF_ADDR))
    mu.mem_write(REF_ADDR, b"\x00" * 0x30)
    mu.mem_write(REF_ADDR + 0x1C, struct.pack("<3f", 0.0, 0.0, 0.0))

    mu.mem_write(SELF_ADDR, b"\x00" * 0x100)
    mu.mem_write(SELF_ADDR + 0x04, struct.pack("<II", 0x1111, 0x2222))
    mu.mem_write(SELF_ADDR + 0x18, struct.pack("<I", SLOT0_ADDR))
    mu.mem_write(SELF_ADDR + 0x98, struct.pack("<I", 0x3333))
    mu.mem_write(SELF_ADDR + 0xA0, struct.pack("<H", len(ids)))
    for i, val in enumerate(ids):
        mu.mem_write(SELF_ADDR + 0xA2 + i * 2, struct.pack("<H", val))

    mu.mem_write(SLOT0_ADDR + 0x20, struct.pack("<I", used_id))

    for pid, (x, y, z) in pts.items():
        mu.mem_write(PT_BASE + (pid & 0xF) * 0x10, struct.pack("<hhhh", 0, x, y, z))

    mu.mem_write(ENT_ADDR, b"\x00" * 0x80)
    mu.mem_write(ENT_ADDR, struct.pack("<I", ENT_VT_ADDR))
    mu.mem_write(ENT_VT_ADDR + 0x14, struct.pack("<I", VFN_14))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, mode)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=200000)

    ent_mem = bytes(mu.mem_read(ENT_ADDR, 0x70))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return ent_mem, calls, regs


CASES = [
    dict(
        name="mode1_filtered_and_vfn14",
        mode=1,
        ids=[1, 2, 3],
        used_id=1,
        pts={2: (500, 0, 0), 3: (1500, 0, 0)},
        ent_null=False,
        ret_2c0ba8=1,
    ),
    dict(
        name="mode2_filtered_no_vfn14",
        mode=2,
        ids=[1, 2],
        used_id=99,
        pts={1: (100, 0, 0), 2: (1000, 0, 0)},
        ent_null=False,
        ret_2c0ba8=1,
    ),
    dict(
        name="mode0_random_ent_null",
        mode=0,
        ids=[4, 5],
        used_id=4,
        pts={5: (10, 20, 30)},
        ent_null=True,
        ret_2c0ba8=0,
    ),
    dict(
        name="empty_ids",
        mode=0,
        ids=[],
        used_id=0,
        pts={},
        ent_null=False,
        ret_2c0ba8=0,
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
        o_ent, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_ent, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_ent != c_ent:
            return False, f"{c['name']}: ent_mem mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip total <= 0 branch ble -> bgt (at 0x00396d4c)
    m1 = bytearray(b)
    off1 = 0x00396D4C - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0xD
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0xC0000000)

    # 2. Flip mode == 0 branch beq -> bne (at 0x00396db4)
    m2 = bytearray(b)
    off2 = 0x00396DB4 - FUNC_ADDR
    insn2 = struct.unpack_from("<I", m2, off2)[0]
    assert (insn2 >> 28) == 0x0
    struct.pack_into("<I", m2, off2, (insn2 & 0x0FFFFFFF) | 0x10000000)

    # 3. Flip mode == 1 range bhs -> blo (at 0x00396e80)
    m3 = bytearray(b)
    off3 = 0x00396E80 - FUNC_ADDR
    insn3 = struct.unpack_from("<I", m3, off3)[0]
    assert (insn3 >> 28) == 0x2
    struct.pack_into("<I", m3, off3, (insn3 & 0x0FFFFFFF) | 0x30000000)

    # 4. Flip mode == 2 range bhs -> blo (at 0x00396e9c)
    m4 = bytearray(b)
    off4 = 0x00396E9C - FUNC_ADDR
    insn4 = struct.unpack_from("<I", m4, off4)[0]
    assert (insn4 >> 28) == 0x2
    struct.pack_into("<I", m4, off4, (insn4 & 0x0FFFFFFF) | 0x30000000)

    # 5. Flip vfn_14 mode == 1 check cmp r7, #1 -> #2 (at 0x00396fc8)
    m5 = bytearray(b)
    off5 = 0x00396FC8 - FUNC_ADDR
    assert struct.unpack_from("<I", m5, off5)[0] == 0xE3570001
    struct.pack_into("<I", m5, off5, 0xE3570002)

    return [
        ("total_bgt", bytes(m1)),
        ("mode0_bne", bytes(m2)),
        ("mode1_blo", bytes(m3)),
        ("mode2_blo", bytes(m4)),
        ("vfn14_mode2", bytes(m5)),
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
        f"PASS: engine_func_00396d24 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
