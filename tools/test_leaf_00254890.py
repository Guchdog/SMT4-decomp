#!/usr/bin/env python3
"""Differential Unicorn verification for ui_func_00254890 (0x00254890)."""

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
    UC_ARM_REG_S0,
    UC_ARM_REG_S1,
    UC_ARM_REG_S2,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

TU_REL = "src/engine/leaf_batch46_a.cpp"
FUNC_NAME = "ui_func_00254890"
ORIG_ADDR = 0x00254890
ORIG_SIZE = 468

TBL_00402930 = 0x00402930

CALLEES_ORIG = {
    "ui_func_002940ac": 0x002940AC,
    "ui_func_00282f00": 0x00282F00,
    "ui_func_00294054": 0x00294054,
    "ui_func_0020fe84": 0x0020FE84,
}

ORIG_BYTES = bytes.fromhex(
    "10402de9671a9fed680a9fed680adfed"
    "050051e3048b2ded10d04de20040a0e1"
    "619adfed638adfed638a9fed639a9fed"
    "01f19f37350000eadc48250044492500"
    "ac492500e8492500084a2500060a94ed"
    "6c119fe5100a10ee010050e1040000aa"
    "010a30ee280094e5010080e2060a84ed"
    "280084e5060a94ed1c0094e5401ab0ee"
    "400af0eee4fd00eb680ab0ee491ab0ee"
    "480af0ee280094e5000050e3190000da"
    "900a01ee480af0eee11af8eea90a41ee"
    "140000ea0c119fe5180094e5010050e1"
    "050000da100a00ee281094e5010041e2"
    "410a30ee060a84ed280084e5060a94ed"
    "1c0094e5401ab0ee400af0eecafd00eb"
    "680ab0ee491ab0ee480af0ee280094e5"
    "000050e3e5ffffca00f020e357b900eb"
    "10d08de2048bbdec1080bde8041a94ed"
    "a4109fe5000a31ee100a10ee040a84ed"
    "010050e1600a30ce000000da040a84ed"
    "1c0094e50c1084e29dfd00eb10d08de2"
    "048bbdec1080bde8041a94ed400a31ee"
    "040a84ede80ab4ee10faf1ee200a303e"
    "f2ffff2af0ffffea50209fe5680ab0ee"
    "070092e8400af0ee07008de8240094e5"
    "00119de71c0094e515edfeeb10d08de2"
    "048bbdec1080bde86f12033a0ad7a33d"
    "0000a0400000b443000000009a99c940"
    "000090408fc2f53ca69b443c0000b443"
    "30294000"
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
    op: int,
    f10: float,
    f18: float,
    f24: int,
    f28: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    enable_vfp(uc)

    uc.mem_write(TBL_00402930, struct.pack("<3I", 0x1111, 0x2222, 0x3333))
    uc.mem_write(SELF_BASE, b"\x00" * 0x40)
    uc.mem_write(SELF_BASE + 0x10, struct.pack("<f", f10))
    uc.mem_write(SELF_BASE + 0x18, struct.pack("<f", f18))
    uc.mem_write(SELF_BASE + 0x1C, struct.pack("<I", 0x77778888))
    uc.mem_write(SELF_BASE + 0x24, struct.pack("<I", f24))
    uc.mem_write(SELF_BASE + 0x28, struct.pack("<i", f28))

    if not use_candidate:
        uc.mem_write(ORIG_ADDR, ORIG_BYTES)
        for addr in CALLEES_ORIG.values():
            uc.mem_write(addr, struct.pack("<I", 0xE12FFF1E))
        stub_map = {v: k for k, v in CALLEES_ORIG.items()}
        entry_addr = ORIG_ADDR
    else:
        func_addr, _, sec_addrs, sec_by_idx, syms, rel_entries = cand_info
        ext_stubs = build_cand_stubs_and_relocate(
            uc, sec_addrs, sec_by_idx, syms, rel_entries
        )
        stub_map = {v: k for k, v in ext_stubs.items()}
        entry_addr = func_addr

    events: List[Tuple] = []

    def hook_code(uc_inst: Uc, address: int, size_i: int, user_data):
        name = stub_map.get(address)
        if name is None:
            return
        r0 = uc_inst.reg_read(UC_ARM_REG_R0)
        r1 = uc_inst.reg_read(UC_ARM_REG_R1)
        s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S0)))[0]
        s1 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S1)))[0]
        s2 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S2)))[0]
        if name == "ui_func_002940ac":
            events.append((name, r0, s0, s1, s2))
        elif name == "ui_func_00282f00":
            if mutate_kind == "bad_s1":
                s1 += 1.0
            events.append((name, s0, s1, s2))
        elif name == "ui_func_00294054":
            if mutate_kind == "bad_4054":
                r1 ^= 4
            events.append((name, r0, r1))
        elif name == "ui_func_0020fe84":
            if mutate_kind == "bad_fe84":
                r1 ^= 1
            events.append((name, r0, r1, s0, s1))
        uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)
    uc.reg_write(UC_ARM_REG_R1, op)

    if mutate_kind == "skip_all":
        return events, b""

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    if mutate_kind == "corrupt_mem":
        uc.mem_write(SELF_BASE + 0x10, struct.pack("<f", 999.0))

    return events, bytes(uc.mem_read(SELF_BASE, 0x30))


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_00254890" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = [
        (0, 0.0, 0.02, 0, 0),
        (0, 0.0, 0.02, 0, 3),
        (0, 0.0, 0.03, 0, 2),
        (1, 0.0, 0.012, 0, 1),
        (1, 0.0, 0.02, 0, 1),
        (1, 0.0, 0.02, 0, 5),
        (2, 100.0, 0.0, 0, 0),
        (2, 358.0, 0.0, 0, 0),
        (3, 10.0, 0.0, 0, 0),
        (3, 2.0, 0.0, 0, 0),
        (4, 0.0, 0.0, 0, 0),
        (4, 0.0, 0.0, 1, 0),
        (4, 0.0, 0.0, 2, 0),
        (5, 0.0, 0.0, 0, 0),
    ]

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params}):")
            print(f"  orig ev={o[0]}")
            print(f"  cand ev={c[0]}")
            return 1

    mutants = [
        ("skip_all", (0, 0.0, 0.02, 0, 3)),
        ("bad_s1", (0, 0.0, 0.02, 0, 3)),
        ("bad_4054", (2, 100.0, 0.0, 0, 0)),
        ("bad_fe84", (4, 0.0, 0.0, 1, 0)),
        ("corrupt_mem", (3, 2.0, 0.0, 0, 0)),
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
