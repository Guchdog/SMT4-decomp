#!/usr/bin/env python3
"""Differential Unicorn verification for script_vm_func_002dcaf8 (0x002dcaf8)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_CPSR,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

TU_REL = "src/engine/leaf_batch46_a.cpp"
FUNC_NAME = "script_vm_func_002dcaf8"
ORIG_ADDR = 0x002DCAF8
ORIG_SIZE = 384
ORIG_LOOKUP_BL = 0x002B6700

ORIG_BYTES = bytes.fromhex(
    "70402de90040a0e1b000d0e10150a0e1"
    "fc66ffeb0060a0e1b000d5e1f966ffeb"
    "000056e35300000a000050e30600d015"
    "4f00000a0a0050e300f19f371b0000ea"
    "68cb2d00a8cb2d0080cb2d0088cb2d00"
    "70cb2d0078cb2d0060cb2d0090cb2d00"
    "98cb2d00a0cb2d000100a0e3100000ea"
    "0200a0e30e0000ea0300a0e30c0000ea"
    "0400a0e30a0000ea0500a0e3080000ea"
    "0600a0e3060000ea0700a0e3040000ea"
    "0800a0e3020000ea0900a0e3000000ea"
    "0000a0e30610d6e50a0051e301f19f37"
    "1b0000eaecCb2d002ccc2d0004cc2d00"
    "0ccc2d00f4cb2d00fccb2d00e4cb2d00"
    "14cc2d001ccc2d0024cc2d000110a0e3"
    "100000ea0210a0e30e0000ea0310a0e3"
    "0c0000ea0410a0e30a0000ea0510a0e3"
    "080000ea0610a0e3060000ea0710a0e3"
    "040000ea0810a0e3020000ea0910a0e3"
    "000000ea0010a0e3010050e00c00001a"
    "b000d4e1af66ffeb0040a0e1b000d5e1"
    "ac66ffeb000054e300f020e30500000a"
    "000050e30200000ab400d0e1b410d4e1"
    "010040e07080bde80000a0e37080bde8"
)
assert len(ORIG_BYTES) == ORIG_SIZE

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
CAND_BASE = 0x00600000
CAND_SIZE = 0x00100000
DATA_BASE = 0x00700000
DATA_SIZE = 0x00100000
STACK_BASE = 0x00900000
STACK_SIZE = 0x00020000
ARG_A = 0x00720000
ARG_B = 0x00720010
ITEM_A = 0x00730000
ITEM_B = 0x00730100
SENTINEL = 0x006F0000


def parse_elf32(data: bytes):
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<HHH", data, 46)
    shdrs = [
        struct.unpack_from("<10I", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]

    def read_str(strtab_idx: int, off: int) -> str:
        s_off = shdrs[strtab_idx][4]
        end = data.index(b"\x00", s_off + off)
        return data[s_off + off : end].decode("ascii", "replace")

    sections = {}
    for i, sh in enumerate(shdrs):
        name = read_str(e_shstrndx, sh[0])
        sections[name] = (i, sh, data[sh[4] : sh[4] + sh[5]])

    _, sym_sh, sym_bytes = sections[".symtab"]
    strtab_idx = sym_sh[6]
    syms = []
    for off in range(0, len(sym_bytes), 16):
        st_name, st_value, st_size, st_info, st_other, st_shndx = struct.unpack_from(
            "<IIIBBH", sym_bytes, off
        )
        syms.append((read_str(strtab_idx, st_name), st_value, st_size, st_info, st_shndx))

    return shdrs, sections, syms


def load_candidate_func(obj_path: Path, func_name: str):
    data = obj_path.read_bytes()
    shdrs, sections, syms = parse_elf32(data)
    target = None
    for s in syms:
        if s[0] == func_name:
            target = s
            break
    assert target is not None, f"missing symbol {func_name}"
    _, st_value, st_size, _, st_shndx = target
    assert st_size > 0, f"{func_name} has zero size"

    sec_addrs: Dict[int, int] = {}
    cursor = CAND_BASE
    rel_entries: List[Tuple[int, int, int, int]] = []
    sec_by_idx: Dict[int, Tuple[str, Tuple[int, ...], bytes]] = {}
    for name, (idx, sh, sbytes) in sections.items():
        sec_by_idx[idx] = (name, sh, sbytes)

    for idx, (name, sh, sbytes) in sec_by_idx.items():
        if sh[2] & 0x2:
            align = max(4, sh[8])
            cursor = (cursor + align - 1) & ~(align - 1)
            sec_addrs[idx] = cursor
            cursor += max(4, len(sbytes))

    for name, (idx, sh, sbytes) in sections.items():
        if sh[1] == 9:
            target_sec = sh[7]
            if target_sec not in sec_addrs:
                continue
            for off in range(0, len(sbytes), 8):
                r_offset, r_info = struct.unpack_from("<II", sbytes, off)
                r_type = r_info & 0xFF
                r_sym = r_info >> 8
                rel_entries.append((target_sec, r_offset, r_type, r_sym))

    func_addr = sec_addrs[st_shndx] + st_value
    return func_addr, st_size, sec_addrs, sec_by_idx, syms, rel_entries


def build_cand_stubs_and_relocate(
    uc: Uc, sec_addrs, sec_by_idx, syms, rel_entries
) -> int:
    for idx, addr in sec_addrs.items():
        _, _, sbytes = sec_by_idx[idx]
        if sbytes:
            uc.mem_write(addr, sbytes)

    stub_cursor = CAND_BASE + 0x40000
    ext_stubs: Dict[str, int] = {}

    def get_stub(name: str) -> int:
        nonlocal stub_cursor
        if name not in ext_stubs:
            ext_stubs[name] = stub_cursor
            uc.mem_write(stub_cursor, struct.pack("<I", 0xE12FFF1E))
            stub_cursor += 4
        return ext_stubs[name]

    for target_sec, r_offset, r_type, r_sym in rel_entries:
        if r_type == 42:
            continue
        patch_addr = sec_addrs[target_sec] + r_offset
        sym_name, sym_val, _, _, sym_shndx = syms[r_sym]
        if sym_shndx == 0:
            target_addr = get_stub(sym_name)
        else:
            target_addr = sec_addrs[sym_shndx] + sym_val

        cur_word = struct.unpack("<I", uc.mem_read(patch_addr, 4))[0]
        if r_type in (28, 29):
            imm24 = ((target_addr - (patch_addr + 8)) >> 2) & 0x00FFFFFF
            patched = (cur_word & 0xFF000000) | imm24
            uc.mem_write(patch_addr, struct.pack("<I", patched))
        elif r_type == 2:
            uc.mem_write(patch_addr, struct.pack("<I", (cur_word + target_addr) & 0xFFFFFFFF))
        elif r_type in (43, 44):
            imm16 = (target_addr & 0xFFFF) if r_type == 43 else ((target_addr >> 16) & 0xFFFF)
            imm4 = (imm16 >> 12) & 0xF
            imm12 = imm16 & 0xFFF
            patched = (cur_word & 0xFFF0F000) | (imm4 << 16) | imm12
            uc.mem_write(patch_addr, struct.pack("<I", patched))
        else:
            raise RuntimeError(f"unsupported reloc type {r_type} for {sym_name}")

    return ext_stubs["script_vm_func_002b6700"]


def run_one(
    use_candidate: bool,
    cand_info,
    id_a: int,
    id_b: int,
    ptr_a: int,
    ptr_b: int,
    kind_a: int,
    kind_b: int,
    sub_a: int,
    sub_b: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(ARG_A, struct.pack("<H", id_a))
    uc.mem_write(ARG_B, struct.pack("<H", id_b))
    uc.mem_write(ITEM_A, b"\x00" * 0x20)
    uc.mem_write(ITEM_B, b"\x00" * 0x20)
    uc.mem_write(ITEM_A + 4, struct.pack("<H", sub_a))
    uc.mem_write(ITEM_A + 6, bytes([kind_a]))
    uc.mem_write(ITEM_B + 4, struct.pack("<H", sub_b))
    uc.mem_write(ITEM_B + 6, bytes([kind_b]))

    if not use_candidate:
        uc.mem_write(ORIG_ADDR, ORIG_BYTES)
        uc.mem_write(ORIG_LOOKUP_BL, struct.pack("<I", 0xE12FFF1E))
        lookup_addr = ORIG_LOOKUP_BL
        entry_addr = ORIG_ADDR
    else:
        func_addr, _, sec_addrs, sec_by_idx, syms, rel_entries = cand_info
        lookup_addr = build_cand_stubs_and_relocate(
            uc, sec_addrs, sec_by_idx, syms, rel_entries
        )
        entry_addr = func_addr

    calls: List[int] = []

    def hook_code(uc_inst: Uc, address: int, size_i: int, user_data):
        if address == lookup_addr:
            r0 = uc_inst.reg_read(UC_ARM_REG_R0)
            calls.append(r0)
            if r0 == id_a:
                ret_p = ptr_a
            elif r0 == id_b:
                ret_p = ptr_b
            else:
                ret_p = 0
            if mutate_kind == "bad_lookup":
                ret_p = 0
            uc_inst.reg_write(UC_ARM_REG_R0, ret_p)
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, ARG_A)
    uc.reg_write(UC_ARM_REG_R1, ARG_B)

    if mutate_kind == "skip_all":
        return calls, 0

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    ret = struct.unpack("<i", struct.pack("<I", uc.reg_read(UC_ARM_REG_R0)))[0]
    if mutate_kind == "negate_ret":
        ret = -ret
    elif mutate_kind == "add_one":
        ret += 1
    elif mutate_kind == "zero_ret":
        ret = 0
    return calls, ret


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_002dcaf8" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = [
        # null pointers
        (1, 2, 0, ITEM_B, 0, 0, 10, 20),
        (1, 2, ITEM_A, 0, 0, 0, 10, 20),
        (1, 2, 0, 0, 0, 0, 10, 20),
        # same rank -> sub tiebreak
        (1, 2, ITEM_A, ITEM_B, 0, 0, 10, 25),
        (1, 2, ITEM_A, ITEM_B, 0, 0, 25, 10),
        (1, 2, ITEM_A, ITEM_B, 0, 0, 10, 10),
        # all pairs across 0..11
    ]
    for ka in range(12):
        for kb in (0, 1, 2, 6, 10):
            cases.append((100, 200, ITEM_A, ITEM_B, ka, kb, 50, 75))

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params}):")
            print(f"  orig={o}")
            print(f"  cand={c}")
            return 1

    mutants = [
        ("skip_all", (1, 2, ITEM_A, ITEM_B, 0, 2, 10, 20)),
        ("bad_lookup", (1, 2, ITEM_A, ITEM_B, 0, 2, 10, 20)),
        ("negate_ret", (1, 2, ITEM_A, ITEM_B, 0, 2, 10, 20)),
        ("add_one", (1, 2, ITEM_A, ITEM_B, 0, 0, 10, 10)),
        ("zero_ret", (1, 2, ITEM_A, ITEM_B, 0, 0, 10, 25)),
    ]
    detected = 0
    for name, params in mutants:
        o = run_one(False, cand_info, *params)
        m = run_one(True, cand_info, *params, mutate_kind=name)
        if o != m:
            detected += 1
        else:
            print(f"MUTANT NOT DETECTED: {name}")
            return 1

    print(
        f"PASS: {FUNC_NAME} (0x{ORIG_ADDR:08x}) matched original across {len(cases)} cases "
        f"and detected {detected}/{len(mutants)} mutants "
        f"(candidate {cand_size} B vs original {ORIG_SIZE} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
