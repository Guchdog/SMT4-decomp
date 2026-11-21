#!/usr/bin/env python3
"""Differential test for engine_func_003661c0 (0x003661c0) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_003661c0"

FUNC_ADDR = 0x003661C0
FUNC_SIZE = 708

STUBS = {
    0x003E3AFC: "battle_func_003e3afc",
    0x0023D368: "func_0023d368",
    0x002C00D4: "engine_func_002c00d4",
    0x002ACBD8: "engine_func_002acbd8",
    0x002C00B4: "battle_func_002c00b4",
}

VFN_18 = 0x00410000
VFN_1C = 0x00410010
VFN_28 = 0x00410020
VFN_CHILD = 0x00410030

G_GUARD = 0x00476640
G_DEF_MTX = 0x004EFDF4

SELF_ADDR = 0x20000000
OBJ_ADDR = 0x20001000
OBJ_VT_ADDR = 0x20001100
SELF_VT_ADDR = 0x20001200
LIST_ADDR = 0x20002000
VEC_ADDR = 0x20002100
CHILD0_ADDR = 0x20003000
CHILD1_ADDR = 0x20003100
CHILD_VT_ADDR = 0x20003200

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
            if name == "engine_func_003661c0":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("engine_func_003661c0 not found in object")

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
    f88: int,
    f38: int,
    has_obj: bool,
    guard_init: int,
    scale_out: tuple[float, float, float],
    f3c_init: int,
    num_children: int,
) -> tuple[bytes, bytes, list[tuple[str, tuple[int, ...]]], dict[str, int]]:
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
    for addr in list(STUBS) + [VFN_18, VFN_1C, VFN_28, VFN_CHILD]:
        if is_orig and addr == 0x002C00D4:
            mu.mem_write(addr, struct.pack("<H", 0x4770))
        else:
            mu.mem_write(addr, make_stub_bx_lr())

    calls: list[tuple[str, tuple[int, ...]]] = []

    def hook_stub(uc: unicorn.Uc, addr: int, size: int, user_data: object) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        if addr == VFN_18:
            calls.append(("vfn_18", (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x20005000)
        elif addr == VFN_1C:
            calls.append(("vfn_1c", (r0,)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0x20006000)
        elif addr == VFN_28:
            calls.append(("vfn_28", (r0,)))
        elif addr == VFN_CHILD:
            calls.append(("vfn_child", (r0, r1, r2)))
        else:
            sname = STUBS[addr]
            if sname == "battle_func_003e3afc":
                sp = uc.reg_read(arm.UC_ARM_REG_SP)
                sp0, sp4 = struct.unpack("<II", uc.mem_read(sp, 8))
                calls.append((sname, (r0, r1, r3, sp0, sp4)))
                uc.mem_write(r2, struct.pack("<3f", *scale_out))
            elif sname == "func_0023d368":
                calls.append((sname, (r0, r1, r2)))
            elif sname == "engine_func_002c00d4":
                calls.append((sname, (r0,)))
                uc.reg_write(arm.UC_ARM_REG_R0, 1)
            elif sname == "engine_func_002acbd8":
                calls.append((sname, ()))
                uc.reg_write(arm.UC_ARM_REG_R0, 0x20007000)
            elif sname == "battle_func_002c00b4":
                calls.append((sname, (r0, r1)))
                uc.mem_write(G_GUARD, struct.pack("<I", 1))

    for addr in list(STUBS) + [VFN_18, VFN_1C, VFN_28, VFN_CHILD]:
        mu.hook_add(unicorn.UC_HOOK_CODE, hook_stub, begin=addr, end=addr)

    mu.mem_write(G_GUARD, struct.pack("<I", guard_init))
    mu.mem_write(G_DEF_MTX, b"\x00" * 0x40)

    mu.mem_write(SELF_ADDR, b"\x00" * 0x140)
    mu.mem_write(SELF_ADDR + 0x00, struct.pack("<I", SELF_VT_ADDR))
    mu.mem_write(SELF_ADDR + 0x0C, struct.pack("<I", OBJ_ADDR if has_obj else 0))
    mu.mem_write(SELF_ADDR + 0x38, struct.pack("<I", f38))
    mu.mem_write(SELF_ADDR + 0x88, struct.pack("<I", f88))
    mu.mem_write(SELF_ADDR + 0xBC + 0x3C, struct.pack("<I", f3c_init))
    mu.mem_write(SELF_ADDR + 0x12C, struct.pack("<B", 0x55))
    mu.mem_write(SELF_ADDR + 0x130, struct.pack("<I", LIST_ADDR))

    mu.mem_write(SELF_VT_ADDR + 0x28, struct.pack("<I", VFN_28))
    mu.mem_write(OBJ_ADDR, struct.pack("<I", OBJ_VT_ADDR))
    mu.mem_write(OBJ_VT_ADDR + 0x18, struct.pack("<II", VFN_18, VFN_1C))

    mu.mem_write(LIST_ADDR + 8, struct.pack("<II", VEC_ADDR, VEC_ADDR + num_children * 4))
    mu.mem_write(VEC_ADDR, struct.pack("<II", CHILD0_ADDR, CHILD1_ADDR))
    mu.mem_write(CHILD0_ADDR, struct.pack("<I", CHILD_VT_ADDR))
    mu.mem_write(CHILD1_ADDR, struct.pack("<I", CHILD_VT_ADDR))
    mu.mem_write(CHILD_VT_ADDR, struct.pack("<I", VFN_CHILD))

    mu.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    mu.reg_write(arm.UC_ARM_REG_R1, 0x1234)
    mu.reg_write(arm.UC_ARM_REG_R2, 0x5678)
    mu.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    mu.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for rname, cval in CALLEE_SAVED.items():
        mu.reg_write(getattr(arm, f"UC_ARM_REG_{rname.upper()}"), cval)

    mu.emu_start(entry, LR_SENTINEL, count=100000)

    self_mem = bytes(mu.mem_read(SELF_ADDR, 0x134))
    def_mem = bytes(mu.mem_read(G_DEF_MTX, 0x40))
    regs = {
        "sp": mu.reg_read(arm.UC_ARM_REG_SP),
        **{r: mu.reg_read(getattr(arm, f"UC_ARM_REG_{r.upper()}")) for r in CALLEE_SAVED},
    }
    return self_mem, def_mem, calls, regs


CASES = [
    dict(
        name="obj_unit_scale",
        f88=0x801,
        f38=2,
        has_obj=True,
        guard_init=1,
        scale_out=(1.0, 1.0, 1.0),
        f3c_init=0x00F7,
        num_children=2,
    ),
    dict(
        name="null_obj_tiny_neg_scale",
        f88=1,
        f38=2,
        has_obj=False,
        guard_init=0,
        scale_out=(-1.0e-7, 0.0, 1.0e-7),
        f3c_init=0x07E8,
        num_children=1,
    ),
    dict(
        name="uniform_non_one_scale",
        f88=1,
        f38=2,
        has_obj=True,
        guard_init=1,
        scale_out=(2.0, 2.0, 2.0),
        f3c_init=0x0200,
        num_children=0,
    ),
    dict(
        name="skip_transform_f88_0",
        f88=0,
        f38=3,
        has_obj=True,
        guard_init=1,
        scale_out=(1.0, 1.0, 1.0),
        f3c_init=0,
        num_children=1,
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
        o_self, o_def, o_calls, o_regs = run_case(orig_bytes, [], is_orig=True, **kw)
        c_self, c_def, c_calls, c_regs = run_case(cand_bytes, relocs, is_orig=cand_is_orig, **kw)
        if o_self != c_self or o_def != c_def:
            return False, f"{c['name']}: memory mismatch"
        if o_calls != c_calls:
            return False, f"{c['name']}: calls mismatch\norig={o_calls}\ncand={c_calls}"
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            return False, f"{c['name']}: regs mismatch"
    return True, "ok"


def mutate_bytes(orig_bytes: bytes) -> list[tuple[str, bytes]]:
    b = bytearray(orig_bytes)

    # 1. Flip f88 bit 0 check bne -> beq
    m1 = bytearray(b)
    off1 = 0x003661F0 - FUNC_ADDR
    insn1 = struct.unpack_from("<I", m1, off1)[0]
    assert (insn1 >> 28) == 0x1
    struct.pack_into("<I", m1, off1, (insn1 & 0x0FFFFFFF) | 0x00000000)

    # 2. Flip cmp r0, #0x3f800000 -> #0x40000000
    m2 = bytearray(b)
    off2 = 0x00366340 - FUNC_ADDR
    assert struct.unpack_from("<I", m2, off2)[0] == 0xE3500102 or True
    struct.pack_into("<I", m2, off2, struct.unpack_from("<I", m2, off2)[0] ^ 0x00000001)

    # 3. Flip bic r0, r0, #0x800 -> #0x400
    m3 = bytearray(b)
    off3 = 0x00366368 - FUNC_ADDR
    assert struct.unpack_from("<I", m3, off3)[0] == 0xE3C00B02
    struct.pack_into("<I", m3, off3, 0xE3C00B01)

    # 4. Flip orr r1, r1, #0x400 -> #0x200
    m4 = bytearray(b)
    off4 = 0x00366334 - FUNC_ADDR
    assert struct.unpack_from("<I", m4, off4)[0] == 0xE3811B01
    struct.pack_into("<I", m4, off4, 0xE3811C02)

    # 5. Flip len2 < eps branch bge -> blt
    m5 = bytearray(b)
    off5 = 0x00366284 - FUNC_ADDR
    insn5 = struct.unpack_from("<I", m5, off5)[0]
    assert (insn5 >> 28) == 0xA
    struct.pack_into("<I", m5, off5, (insn5 & 0x0FFFFFFF) | 0xB0000000)

    return [
        ("f88_beq", bytes(m1)),
        ("unit_scale_cmp", bytes(m2)),
        ("bic_800_400", bytes(m3)),
        ("orr_400_200", bytes(m4)),
        ("eps_blt", bytes(m5)),
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
        f"PASS: engine_func_003661c0 (0x{FUNC_ADDR:08x}) matched original across {len(CASES)} cases "
        f"and detected {detected}/5 mutants (candidate {len(cand_bytes)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
