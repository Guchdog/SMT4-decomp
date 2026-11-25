#!/usr/bin/env python3
"""Differential Unicorn verification for ui_func_0033d324 (0x0033d324)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from unicorn import UC_ARCH_ARM, UC_HOOK_CODE, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_C1_C0_2,
    UC_ARM_REG_CPSR,
    UC_ARM_REG_FPEXC,
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
FUNC_NAME = "ui_func_0033d324"
ORIG_ADDR = 0x0033D324
ORIG_SIZE = 440
ORIG_IDIVMOD = 0x002C615C

ORIG_BYTES = bytes.fromhex(
    "f0472de90040a0e10180a0e394719fe5"
    "621a9fed028b2ded900390e5608a9fed"
    "040050e300f19f37090000ea60d33300"
    "80d33300f4d3330098d43300e60a94ed"
    "080a30ee100a10eee60a84ed010150e3"
    "908384a5028bbdecf087bde8e61f84e2"
    "e81ad4ed0000a0e3020a91ec881a71ee"
    "080a30ee880a70eee81ac4ed101a10ee"
    "070051e1e61f84e20100a0a3020a81ec"
    "901a10eee61a84ad070051e1901a11ee"
    "010080a2e71a84ad410451e3020000ba"
    "010080e23c0a9fede80a84ed030050e3"
    "0200a0033200000a028bbdecf087bde8"
    "f40294e50050a0e3000050e3dcffffda"
    "c8909fe5328adfed00a0a0e3850165e0"
    "800080e0006184e02c0096e5000050e3"
    "010050131400000a0d0a96ed3800d6e5"
    "080a30ee000050e3100a10ee0d0a86ed"
    "0300000a090050e10d8ac6ad38a0c6a5"
    "090000ea070050e1070000ba300096e5"
    "010080e2300086e52c1096e53923feeb"
    "301086e50d8ac6ed3880c6e5f40294e5"
    "015085e2050050e1dfffffca028bbdec"
    "f087bde8e50a94ed080a30ee100a10ee"
    "e50a84ed070050e10400a0a3e51a84ad"
    "afffffba900384e5028bbdecf087bde8"
    "000080400000803f0000804000000041"
    "0000a04100000000"
)
# Check line 63: 301086ed -> 301086e5! Let's assert len
assert len(ORIG_BYTES) == ORIG_SIZE

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000
CAND_BASE = 0x00600000
CAND_SIZE = 0x00100000
DATA_BASE = 0x00700000
DATA_SIZE = 0x00100000
STACK_BASE = 0x00900000
STACK_SIZE = 0x00020000
SELF_BASE = 0x00720000
SENTINEL = 0x006F0000


def enable_vfp(uc: Uc) -> None:
    uc.reg_write(UC_ARM_REG_C1_C0_2, uc.reg_read(UC_ARM_REG_C1_C0_2) | 0x00F00000)
    uc.reg_write(UC_ARM_REG_FPEXC, 0x40000000)


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
) -> Dict[str, int]:
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

    return ext_stubs


def run_one(
    use_candidate: bool,
    cand_info,
    state: int,
    f394: float,
    f398: float,
    f39c: float,
    f3a0: float,
    elems: List[Tuple[int, int, float, int]],
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    enable_vfp(uc)

    uc.mem_write(SELF_BASE, b"\x00" * 0x400)
    uc.mem_write(SELF_BASE + 0x2F4, struct.pack("<i", len(elems)))
    for i, (n, cur, tm, flag) in enumerate(elems):
        e_addr = SELF_BASE + i * 0x54
        uc.mem_write(e_addr + 0x2C, struct.pack("<ii f B", n, cur, tm, flag))
    uc.mem_write(SELF_BASE + 0x390, struct.pack("<Iffff", state, f394, f398, f39c, f3a0))

    if not use_candidate:
        uc.mem_write(ORIG_ADDR, ORIG_BYTES)
        uc.mem_write(ORIG_IDIVMOD, struct.pack("<I", 0xE12FFF1E))
        idivmod_addr = ORIG_IDIVMOD
        entry_addr = ORIG_ADDR
    else:
        func_addr, _, sec_addrs, sec_by_idx, syms, rel_entries = cand_info
        ext_stubs = build_cand_stubs_and_relocate(
            uc, sec_addrs, sec_by_idx, syms, rel_entries
        )
        idivmod_addr = ext_stubs.get("__aeabi_idivmod", 0)
        entry_addr = func_addr

    def hook_code(uc_inst: Uc, address: int, size_i: int, user_data):
        if idivmod_addr != 0 and address == idivmod_addr:
            a = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_R0)))[0]
            b = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_R1)))[0]
            q = int(a / b)
            r = a - q * b
            uc_inst.reg_write(UC_ARM_REG_R0, q & 0xFFFFFFFF)
            uc_inst.reg_write(UC_ARM_REG_R1, r & 0xFFFFFFFF)
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)

    if mutate_kind == "skip_all":
        return bytes(uc.mem_read(SELF_BASE, 0x3B0))

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)

    if mutate_kind == "corrupt_390":
        uc.mem_write(SELF_BASE + 0x390, struct.pack("<I", 99))
    elif mutate_kind == "corrupt_398":
        uc.mem_write(SELF_BASE + 0x398, struct.pack("<f", 99.0))
    elif mutate_kind == "corrupt_elem30":
        uc.mem_write(SELF_BASE + 0x30, struct.pack("<I", 99))
    elif mutate_kind == "corrupt_394":
        uc.mem_write(SELF_BASE + 0x394, struct.pack("<f", 99.0))

    return bytes(uc.mem_read(SELF_BASE, 0x3B0))


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_0033d324" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    elems_sample = [
        (0, 0, 0.0, 0),
        (1, 0, 0.0, 0),
        (3, 2, 19.0, 1),
        (3, 2, 18.0, 1),
        (3, 2, 3.0, 0),
        (3, 2, 2.0, 0),
    ]
    cases = [
        (0, 0.0, 0.5, 0.0, 0.0, []),
        (0, 0.0, 1.0, 0.0, 0.0, []),
        (1, 0.0, 2.5, 2.5, 6.5, []),
        (1, 0.0, 3.0, 3.0, 7.0, []),
        (1, 0.0, 3.0, 2.5, 7.0, []),
        (2, 0.0, 0.0, 0.0, 0.0, []),
        (2, 0.0, 0.0, 0.0, 0.0, elems_sample),
        (3, 2.5, 0.0, 0.0, 0.0, []),
        (3, 3.0, 0.0, 0.0, 0.0, []),
        (4, 0.0, 0.0, 0.0, 0.0, []),
    ]

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params})")
            return 1

    mutants = [
        ("skip_all", (0, 0.0, 0.5, 0.0, 0.0, [])),
        ("corrupt_390", (1, 0.0, 3.0, 3.0, 7.0, [])),
        ("corrupt_398", (0, 0.0, 0.5, 0.0, 0.0, [])),
        ("corrupt_elem30", (2, 0.0, 0.0, 0.0, 0.0, elems_sample)),
        ("corrupt_394", (3, 3.0, 0.0, 0.0, 0.0, [])),
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
