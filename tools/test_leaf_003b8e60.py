#!/usr/bin/env python3
"""Differential test for script_vm_func_003b8e60 (0x003b8e60) with Unicorn ARM."""

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
OUT_DIR = ROOT / "build" / "test_leaf_003b8e60"

FUNC_ADDR = 0x003B8E60
FUNC_SIZE = 536

STUBS = {
    0x0022B2E0: "script_vm_func_0022b2e0",
    0x0019DFBC: "script_vm_func_0019dfbc",
    0x0022B1F8: "script_vm_func_0022b1f8",
    0x002337A0: "shop_func_002337a0",
    0x0027E9E4: "script_vm_func_0027e9e4",
    0x0027EA24: "script_vm_func_0027ea24",
    0x00291018: "script_vm_func_00291018",
    0x002971E4: "script_vm_func_002971e4",
    0x002B8B78: "script_vm_func_002b8b78",
    0x002C5E2C: "script_vm_func_002c5e2c",
    0x002972F8: "scrScriptProcess_func_002972f8",
}

ADDR_MGR_PTR = 0x00432FC8
MGR_ADDR = 0x20000000
OBJ_ADDR = 0x20001000
D5C_ADDR = 0x20002000
PROC_ADDR = 0x20002100
RODATA_BASE = 0x18000000
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


def _layout_rodata(obj_file: Path) -> tuple[bytes, dict[int, int]]:
    data = obj_file.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    raw_secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = raw_secs[e_shstrndx][4]
    names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in raw_secs]

    image = bytearray()
    sec_addr: dict[int, int] = {}
    for i, s in enumerate(raw_secs):
        if s[1] == 1 and (s[2] & 2) and not names[i].startswith(".text"):
            align = max(s[8], 1)
            while len(image) % align:
                image.append(0)
            sec_addr[i] = RODATA_BASE + len(image)
            image.extend(data[s[4] : s[4] + s[5]])

    for i, s in enumerate(raw_secs):
        if s[1] == 9 and s[7] in sec_addr:
            target_off = sec_addr[s[7]] - RODATA_BASE
            symtab = raw_secs[s[6]]
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if r_type == 2:
                    st_shndx = struct.unpack_from("<H", data, symtab[4] + sym_idx * 16 + 14)[0]
                    if st_shndx in sec_addr:
                        val = struct.unpack_from("<I", image, target_off + r_off)[0]
                        struct.pack_into("<I", image, target_off + r_off, sec_addr[st_shndx] + val)

    return bytes(image), sec_addr


def compile_candidate() -> tuple[bytes, bytes, list[tuple[str, int]]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_path = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_path)
    if res.returncode != 0:
        raise RuntimeError(f"compile failed:\n{res.stderr}\n{res.stdout}")

    rodata, sec_addr = _layout_rodata(obj_path)
    data = obj_path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    secs = [struct.unpack_from("<10I", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    shstr_off = secs[e_shstrndx][4]
    sec_names = [data[shstr_off + s[0] : data.index(b"\x00", shstr_off + s[0])].decode("ascii", errors="replace") for s in secs]
    tidx = sec_names.index(".text")
    text_data = bytearray(data[secs[tidx][4] : secs[tidx][4] + secs[tidx][5]])

    symtab = next(s for s in secs if s[1] == 2)
    strtab_off = secs[symtab[6]][4]
    fn_off = fn_size = None
    for idx in range(symtab[5] // 16):
        st_name, st_value, st_size, _st_info, _st_other, st_shndx = struct.unpack_from("<IIIbbH", data, symtab[4] + idx * 16)
        if st_shndx == tidx:
            name = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
            if name == "script_vm_func_003b8e60":
                fn_off, fn_size = st_value, st_size
                break
    if fn_off is None or fn_size is None:
        raise RuntimeError("candidate symbol script_vm_func_003b8e60 not found")

    relocs: list[tuple[str, int]] = []
    for s in secs:
        if s[1] == 9 and s[7] == tidx:
            for k in range(s[5] // 8):
                r_off, r_info = struct.unpack_from("<II", data, s[4] + k * 8)
                sym_idx, r_type = r_info >> 8, r_info & 0xFF
                if not (fn_off <= r_off < fn_off + fn_size):
                    continue
                if r_type in (28, 29):
                    st_name = struct.unpack_from("<I", data, symtab[4] + sym_idx * 16)[0]
                    sname = data[strtab_off + st_name : data.index(b"\x00", strtab_off + st_name)].decode("ascii", errors="replace")
                    relocs.append((sname, r_off - fn_off))
                elif r_type == 2:
                    st_value, _, _, _, st_shndx = struct.unpack_from("<IIbbH", data, symtab[4] + sym_idx * 16 + 4)
                    if st_shndx in sec_addr:
                        addend = struct.unpack_from("<I", text_data, r_off)[0]
                        struct.pack_into("<I", text_data, r_off, sec_addr[st_shndx] + st_value + addend)

    return bytes(text_data[fn_off : fn_off + fn_size]), rodata, relocs


def patch_bl(code: bytearray, at_off: int, src_pc: int, dst_pc: int) -> None:
    delta = (dst_pc - (src_pc + 8)) >> 2
    hi = code[at_off + 3]
    insn = (hi << 24) | (delta & 0x00FFFFFF)
    struct.pack_into("<I", code, at_off, insn)


def read_cstr(uc: unicorn.Uc, ptr: int, max_len: int = 32) -> bytes:
    raw = bytes(uc.mem_read(ptr, max_len))
    nul = raw.find(b"\x00")
    return raw[:nul] if nul >= 0 else raw


def run_one(
    code_bytes: bytes,
    base_addr: int,
    cand_rodata: bytes | None,
    relocs: list[tuple[str, int]] | None,
    ready: int,
    status: int,
    mgr_c1: int,
    mode: int,
) -> tuple[bytes, bytes, bytes, list[tuple], dict[str, int]]:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(0x00100000, 0x00400000)
    uc.mem_map(RODATA_BASE, 0x00100000)
    uc.mem_map(0x20000000, 0x00010000)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    if cand_rodata is not None:
        uc.mem_write(RODATA_BASE, cand_rodata)

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

    uc.mem_write(ADDR_MGR_PTR, struct.pack("<I", MGR_ADDR))
    mgr = bytearray(0xD0)
    mgr[0xC1] = mgr_c1
    uc.mem_write(MGR_ADDR, bytes(mgr))

    d5c = bytearray(0x50)
    d5c[0x3F] = 0x2A
    uc.mem_write(D5C_ADDR, bytes(d5c))
    uc.mem_write(PROC_ADDR, b"\x00" * 0x120)

    obj = bytearray(0xE00)
    struct.pack_into("<I", obj, 0x28, 0x99999999)
    struct.pack_into("<I", obj, 0x2C, 0x88888888)
    struct.pack_into("<I", obj, 0xD5C, D5C_ADDR)
    struct.pack_into("<I", obj, 0xD74, 0x1234)
    struct.pack_into("<I", obj, 0xD80, 0x5678)
    struct.pack_into("<I", obj, 0xD94, 0x9ABC)
    struct.pack_into("<I", obj, 0xD9C, 0xDEF0)
    struct.pack_into("<I", obj, 0xDB0, mode)
    uc.mem_write(OBJ_ADDR, bytes(obj))

    uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
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
        if tag == "script_vm_func_0022b2e0":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, ready)
        elif tag == "script_vm_func_0019dfbc":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, status)
        elif tag == "script_vm_func_0022b1f8":
            calls.append((tag, r0))
        elif tag == "shop_func_002337a0":
            calls.append((tag, r0))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 0x4321)
        elif tag == "script_vm_func_00291018":
            calls.append((tag, r0, read_cstr(uc_inst, r1)))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 0x55)
        elif tag == "script_vm_func_002971e4":
            calls.append((tag, r0, r1))
        elif tag == "script_vm_func_002b8b78":
            calls.append((tag, r0))
        elif tag == "script_vm_func_002c5e2c":
            s = read_cstr(uc_inst, r0)
            calls.append((tag, s))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, 0x6601 if b".bf" in s else 0x6602)
        elif tag == "scrScriptProcess_func_002972f8":
            calls.append((tag, r0, r1))
            uc_inst.reg_write(arm.UC_ARM_REG_R0, PROC_ADDR)
        elif tag in ("script_vm_func_0027e9e4", "script_vm_func_0027ea24"):
            calls.append((tag, r0, r1))

    for addr in STUBS:
        uc.hook_add(unicorn.UC_HOOK_CODE, hook_code, begin=addr, end=addr)

    uc.emu_start(base_addr, LR_SENTINEL, count=50000)

    out_obj = bytes(uc.mem_read(OBJ_ADDR, 0xE00))
    out_mgr = bytes(uc.mem_read(MGR_ADDR, 0xD0))
    out_proc = bytes(uc.mem_read(PROC_ADDR, 0x120))
    regs = {
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        **{n: uc.reg_read(getattr(arm, f"UC_ARM_REG_{n.upper()}")) for n in CALLEE_SAVED},
    }
    return out_obj, out_mgr, out_proc, calls, regs


def main() -> int:
    orig_all = ORIG_BIN.read_bytes()
    orig_code = orig_all[FUNC_ADDR - 0x00100000 : FUNC_ADDR - 0x00100000 + FUNC_SIZE]
    cand_code, cand_rodata, cand_relocs = compile_candidate()

    cases = [
        ("not_ready", 0, 2, 0, 1),
        ("bad_status", 1, 1, 0, 1),
        ("mgr_c1_set", 1, 2, 1, 1),
        ("mode_1", 1, 2, 0, 1),
        ("mode_2", 1, 2, 0, 2),
        ("mode_3", 1, 2, 0, 3),
        ("mode_4", 1, 2, 0, 4),
        ("mode_0_default", 1, 2, 0, 0),
        ("mode_5_default", 1, 2, 0, 5),
    ]

    for name, *args in cases:
        o_obj, o_mgr, o_proc, o_calls, o_regs = run_one(orig_code, FUNC_ADDR, None, None, *args)
        c_obj, c_mgr, c_proc, c_calls, c_regs = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, *args)
        if o_obj != c_obj or o_mgr != c_mgr or o_proc != c_proc:
            print(f"FAIL {name}: mem mismatch")
            return 1
        if o_calls != c_calls:
            print(f"FAIL {name}: calls mismatch\n  orig={o_calls}\n  cand={c_calls}")
            return 1
        if o_regs != c_regs or c_regs["sp"] != STACK_INIT:
            print(f"FAIL {name}: regs mismatch")
            return 1

    # 5 negative / mutation controls
    ref = run_one(orig_code, FUNC_ADDR, None, None, 1, 2, 0, 3)[:4]
    mutants = [
        ("mut_mgr_c1", (1, 2, 1, 3)),
        ("mut_mode_1", (1, 2, 0, 1)),
        ("mut_mode_2", (1, 2, 0, 2)),
        ("mut_mode_4", (1, 2, 0, 4)),
        ("mut_mode_0", (1, 2, 0, 0)),
    ]
    detected = 0
    for mname, margs in mutants:
        cur = run_one(cand_code, 0x00180000, cand_rodata, cand_relocs, *margs)[:4]
        if cur != ref:
            detected += 1
        else:
            print(f"FAIL mutant not detected: {mname}")
            return 1

    print(
        f"PASS: script_vm_func_003b8e60 (0x003b8e60) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants (candidate {len(cand_code)} B vs original {FUNC_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
