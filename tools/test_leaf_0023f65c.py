#!/usr/bin/env python3
"""Differential test for script_vm_func_0023f65c (0x0023f65c) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_0023f65c"

FUNC_ADDR = 0x0023F65C
FUNC_SIZE = 668

G42C8_PTR = 0x004342C8
SELF_ADDR = 0x20000000
CTX_ADDR = 0x20001000
ARR_ADDR = 0x20006000
UNIT_ADDR = 0x2000A000

STUBS = {
    0x002C4B30: "engine_func_002c4b30",
    0x00240578: "engine_func_00240578",
    0x002BF86C: "engine_func_002bf86c",
    0x00240420: "script_vm_func_00240420",
    0x002C4360: "engine_func_002c4360",
    0x00297704: "script_vm_func_00297704",
    0x00240158: "script_vm_func_00240158",
    0x00270298: "script_vm_func_00270298",
    0x0033868C: "func_0033868c",
    0x0033A378: "func_0033a378",
    0x00338658: "func_00338658",
    0x0033A014: "func_0033a014",
    0x003D7228: "func_003d7228",
    0x0027DCA0: "ui_func_0027dca0",
    0x002406F8: "func_002406f8",
    0x00250800: "battle_func_00250800",
    0x00255198: "script_vm_func_00255198",
    0x00394E88: "ui_func_00394e88",
    0x002C2BD0: "script_vm_func_002c2bd0",
    0x002C2BA4: "script_vm_func_002c2ba4",
    0x00289924: "script_vm_func_00289924",
    0x0023FD38: "battle_func_0023fd38",
}

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
            if name == "script_vm_func_0023f65c":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None:
        raise RuntimeError("script_vm_func_0023f65c not found in object")

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


def run_one(
    code_bytes: bytes,
    base_addr: int,
    relocs: list[tuple[str, int]] | None,
    ret_40420: int,
    self_w1: int,
    ctx_44a0: int,
    ctx_44b7: int,
    ctx_e0: int,
    ctx_e4: int,
    ret_406f8: int,
    ret_2c2bd0_0: int,
    ret_2c2bd0_1: int,
    ret_289924: int,
) -> tuple[bytes, bytes, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    buf = bytearray(code_bytes)
    if relocs is not None:
        name_to_addr = {v: k for k, v in STUBS.items()}
        for sym_name, off in relocs:
            target = name_to_addr.get(sym_name)
            if target is None:
                raise RuntimeError(f"unexpected relocation: {sym_name}")
            patch_bl(buf, off, base_addr + off, target)

    uc.mem_write(base_addr, bytes(buf))
    for addr in STUBS:
        uc.mem_write(addr, make_stub_bx_lr())

    uc.mem_write(G42C8_PTR, struct.pack("<I", 0xCAFE42C8))

    self_buf = bytearray(0x20)
    struct.pack_into("<II", self_buf, 0x00, 0, self_w1)
    struct.pack_into("<I", self_buf, 0x0C, 0x12345678)
    uc.mem_write(SELF_ADDR, bytes(self_buf))

    ctx_buf = bytearray(0x4500)
    struct.pack_into("<II", ctx_buf, 0xE0, ctx_e0, ctx_e4)
    struct.pack_into("<I", ctx_buf, 0x1E98, ARR_ADDR)
    struct.pack_into("<I", ctx_buf, 0x44A0, ctx_44a0)
    ctx_buf[0x44B7] = ctx_44b7
    uc.mem_write(CTX_ADDR, bytes(ctx_buf))

    arr_buf = bytearray(0x36 * 0x114)
    for idx, (w50, w54, h58) in [(4, (3, 8, 0)), (5, (3, 8, 0x800)), (6, (1, 8, 0))]:
        off = idx * 0x114
        struct.pack_into("<IIH", arr_buf, off + 0x50, w50, w54, h58)
        struct.pack_into("<h", arr_buf, off + 0x62, 10 + idx)
    uc.mem_write(ARR_ADDR, bytes(arr_buf))
    uc.mem_write(UNIT_ADDR, struct.pack("<HH", 0, 0x77))

    uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, CTX_ADDR)
    uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
    uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
    for name, val in CALLEE_SAVED.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), val)

    calls: list[tuple] = []

    def hook_code(uc_inst, address, size, user_data):
        tag = STUBS.get(address)
        if tag is None:
            return
        r0 = uc_inst.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc_inst.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc_inst.reg_read(arm.UC_ARM_REG_R3)
        if tag == "engine_func_002c4b30":
            uc_inst.mem_write(r0, b"\x00" * r1)
            calls.append((tag, r1))
        elif tag == "engine_func_00240578":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 0xCAFE0578)
        elif tag == "engine_func_002bf86c":
            uc_inst.mem_write(r0, b"save.dat\x00")
            calls.append((tag, r1))
        elif tag == "script_vm_func_00240420":
            s = bytes(uc_inst.mem_read(r1, 16)).split(b"\x00", 1)[0]
            calls.append((tag, r0, s))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_40420)
        elif tag in ("engine_func_002c4360", "script_vm_func_00270298", "func_0033868c", "func_0033a378", "func_00338658", "func_0033a014", "func_003d7228", "script_vm_func_00255198", "ui_func_00394e88"):
            calls.append((tag, r0))
        elif tag == "script_vm_func_00297704":
            s = bytes(uc_inst.mem_read(r0, 16)).split(b"\x00", 1)[0]
            uc_inst.mem_write(r1, struct.pack("<I", 0xABCD1234))
            calls.append((tag, s, r2))
        elif tag in ("script_vm_func_00240158", "battle_func_0023fd38"):
            calls.append((tag, r0, r1))
        elif tag == "ui_func_0027dca0":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, UNIT_ADDR)
        elif tag == "func_002406f8":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_406f8)
        elif tag == "battle_func_00250800":
            sp = uc_inst.reg_read(arm.UC_ARM_REG_SP)
            s = struct.unpack_from("<3I", uc_inst.mem_read(sp, 12))
            calls.append((tag, r0, r1, r2, r3, *s))
        elif tag == "script_vm_func_002c2bd0":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_2c2bd0_0 if r0 == 0 else ret_2c2bd0_1)
        elif tag == "script_vm_func_002c2ba4":
            calls.append((tag, r0, r1, r2))
        elif tag == "script_vm_func_00289924":
            calls.append((tag,))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ret_289924)

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=100000)

    out_self = bytes(uc.mem_read(SELF_ADDR, 0x20))
    out_ctx = bytes(uc.mem_read(CTX_ADDR, 0x4500))
    out_arr = bytes(uc.mem_read(ARR_ADDR, 0x36 * 0x114))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_self, out_ctx, out_arr, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_relocs = compile_candidate()

    cases = [
        ("found_existing_w1", 1, 0x1111, 0, 0, 0, 0, 0, 0, 0, 0),
        ("found_null_w1", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0),
        ("not_found_full_e0_se_done", 0, 0, 0, 0, 0x02000000, 0, 0, 3, 3, 1),
        ("not_found_44a0_40000002_e4_20", 0, 0, 0x40000002, 0, 0, 0x20, 1, 0, 3, 0),
        ("not_found_44b7_set_skip", 0, 0, 0x40000000, 1, 0x02000000, 0, 0, 3, 0, 0),
    ]

    for name, *args in cases:
        o_s, o_c, o_a, o_calls, o_r = run_one(orig_code, FUNC_ADDR, None, *args)
        c_s, c_c, c_a, c_calls, c_r = run_one(cand_code, 0x00180000, cand_relocs, *args)
        if (o_s, o_c, o_a) != (c_s, c_c, c_a):
            print(f"FAIL {name}: memory mismatch")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_r != c_r:
            print(f"FAIL {name}: callee-saved mismatch")
            return 1

    # 5 mutation controls
    patched_cand = bytearray(cand_code)
    name_to_addr = {v: k for k, v in STUBS.items()}
    for sym_name, off in cand_relocs:
        patch_bl(patched_cand, off, 0x00180000 + off, name_to_addr[sym_name])

    def check_mutant(patch_fn, case_args):
        mc = bytearray(patched_cand)
        if not patch_fn(mc):
            return False
        o_s, o_c, o_a, o_calls, _ = run_one(orig_code, FUNC_ADDR, None, *case_args)
        m_s, m_c, m_a, m_calls, _ = run_one(bytes(mc), 0x00180000, None, *case_args)
        return (m_s, m_c, m_a, m_calls) != (o_s, o_c, o_a, o_calls)

    def mut_nop_reloc(reloc_idx: int):
        def _fn(mc: bytearray) -> bool:
            if reloc_idx >= len(cand_relocs):
                return False
            off = cand_relocs[reloc_idx][1]
            struct.pack_into("<I", mc, off, 0xE1A00000)
            return True
        return _fn

    reloc_map = {sym: idx for idx, (sym, _) in enumerate(cand_relocs)}
    mut_specs = [
        (mut_nop_reloc(reloc_map["script_vm_func_00240158"]), cases[0][1:]),
        (mut_nop_reloc(reloc_map["engine_func_002c4360"]), cases[0][1:]),
        (mut_nop_reloc(reloc_map["script_vm_func_00270298"]), cases[2][1:]),
        (mut_nop_reloc(reloc_map["battle_func_00250800"]), cases[2][1:]),
        (mut_nop_reloc(reloc_map["battle_func_0023fd38"]), cases[2][1:]),
    ]
    mutants_ok = sum(1 for fn, cargs in mut_specs if check_mutant(fn, cargs))
    if mutants_ok != 5:
        print(f"FAIL: detected only {mutants_ok}/5 mutants")
        return 1

    print(
        f"PASS: script_vm_func_0023f65c (0x{FUNC_ADDR:08x}) matched original across "
        f"{len(cases)} cases and detected {mutants_ok}/5 mutants "
        f"(candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
