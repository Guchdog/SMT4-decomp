#!/usr/bin/env python3
"""Differential Unicorn verification for ui_func_0025beb8 (0x0025beb8)."""

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
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
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
FUNC_NAME = "ui_func_0025beb8"
ORIG_ADDR = 0x0025BEB8
ORIG_SIZE = 324
ORIG_RAND_BL = 0x00297004
ORIG_SPAWN_B = 0x002920E4
ORIG_PTR_00447E88 = 0x00447E88
ORIG_STATE_0049F91C = 0x0049F91C

ORIG_BYTES = bytes.fromhex(
    "10402de920019fe51410a0e3048b2ded"
    "000090e5088a90ed078ad0ed099a90ed"
    "1300e0e348ec00eb100a00ee1410a0e3"
    "1300e0e3c00ab8ee808a78ee42ec00eb"
    "100a01ee6410a0e30000a0e3c10ab8ee"
    "009a39ee3cec00ebd0109fe5030000e2"
    "de12d1e1050051e301f19f372c0000ea"
    "3cbf25005cbf25007cbf25009cbf2500"
    "bcbf2500491ab0ee480af0ee680ab0ee"
    "9c109fe5048bbdec010080e01040bde8"
    "61d800ea491ab0ee480af0ee680ab0ee"
    "048bbdec010480e2820f80e21040bde8"
    "59d800ea491ab0ee480af0ee680ab0ee"
    "60109fe5048bbdec010040e01040bde8"
    "51d800ea491ab0ee480af0ee680ab0ee"
    "44109fe5048bbdec010080e01040bde8"
    "49d800ea491ab0ee480af0ee680ab0ee"
    "28109fe5048bbdec010080e01040bde8"
    "41d800ea048bbdec1080bde8887e4400"
    "1cf9490003020001f3fdfffe12020001"
    "17020001"
)
assert len(ORIG_BYTES) == ORIG_SIZE

CODE_BASE = 0x00100000
CODE_SIZE = 0x00500000  # covers 0x00100000..0x005fffff (including 0x00447e88, 0x0049f91c)
CAND_BASE = 0x00600000
CAND_SIZE = 0x00100000
DATA_BASE = 0x00700000
DATA_SIZE = 0x00100000
STACK_BASE = 0x00900000
STACK_SIZE = 0x00020000
OBJ_BASE = 0x00720000
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
        if sh[2] & 0x2:  # SHF_ALLOC
            align = max(4, sh[8])
            cursor = (cursor + align - 1) & ~(align - 1)
            sec_addrs[idx] = cursor
            cursor += max(4, len(sbytes))

    for name, (idx, sh, sbytes) in sections.items():
        if sh[1] == 9:  # SHT_REL
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
) -> Tuple[int, int]:
    for idx, addr in sec_addrs.items():
        _, _, sbytes = sec_by_idx[idx]
        if sbytes:
            uc.mem_write(addr, sbytes)

    stub_cursor = CAND_BASE + 0x40000
    ext_stubs: Dict[str, int] = {}
    cand_callees: Dict[str, int] = {}

    def get_stub(name: str) -> int:
        if name not in ext_stubs:
            ext_stubs[name] = stub_cursor
            uc.mem_write(stub_cursor, struct.pack("<I", 0xE12FFF1E))
            return stub_cursor
        return ext_stubs[name]

    for target_sec, r_offset, r_type, r_sym in rel_entries:
        if r_type == 42:  # R_ARM_PREL31 (.ARM.exidx)
            continue
        patch_addr = sec_addrs[target_sec] + r_offset
        sym_name, sym_val, _, _, sym_shndx = syms[r_sym]
        if sym_shndx == 0:
            target_addr = get_stub(sym_name)
            if ext_stubs[sym_name] == stub_cursor:
                stub_cursor += 4
            cand_callees[sym_name] = target_addr
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

    return cand_callees["ui_func_00297004"], cand_callees["script_vm_func_002920e4"]


def run_one(
    use_candidate: bool,
    cand_info,
    pos_xyz: Tuple[float, float, float],
    state_byte: int,
    rand_draws: Tuple[int, int, int],
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    enable_vfp(uc)

    # Set up global pointer at 0x00447E88 and state byte at 0x0049F91C + 0x2E
    uc.mem_write(ORIG_PTR_00447E88, struct.pack("<I", OBJ_BASE))
    uc.mem_write(OBJ_BASE + 0x1C, struct.pack("<3f", *pos_xyz))
    uc.mem_write(ORIG_STATE_0049F91C + 0x2E, struct.pack("<b", state_byte))

    if not use_candidate:
        uc.mem_write(ORIG_ADDR, ORIG_BYTES)
        uc.mem_write(ORIG_RAND_BL, struct.pack("<I", 0xE12FFF1E))
        uc.mem_write(ORIG_SPAWN_B, struct.pack("<I", 0xE12FFF1E))
        entry_addr = ORIG_ADDR
        rand_addr = ORIG_RAND_BL
        spawn_addr = ORIG_SPAWN_B
    else:
        func_addr, _, sec_addrs, sec_by_idx, syms, rel_entries = cand_info
        rand_addr, spawn_addr = build_cand_stubs_and_relocate(
            uc, sec_addrs, sec_by_idx, syms, rel_entries
        )
        entry_addr = func_addr

    events: List[Tuple] = []
    draw_idx = [0]

    def hook_code(uc_inst: Uc, address: int, size: int, user_data):
        if address == rand_addr:
            lo = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_R0)))[0]
            hi = struct.unpack("<i", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_R1)))[0]
            val = rand_draws[draw_idx[0]]
            draw_idx[0] += 1
            if mutate_kind == "bad_rand" and draw_idx[0] == 1:
                val += 1
            events.append(("rand", lo, hi, val))
            uc_inst.reg_write(UC_ARM_REG_R0, val & 0xFFFFFFFF)
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))
        elif address == spawn_addr:
            fx_id = uc_inst.reg_read(UC_ARM_REG_R0)
            s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S0)))[0]
            s1 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S1)))[0]
            s2 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S2)))[0]
            if mutate_kind == "bad_fx_id":
                fx_id ^= 1
            elif mutate_kind == "bad_x":
                s0 += 1.0
            elif mutate_kind == "bad_z":
                s2 -= 1.0
            events.append(("spawn", fx_id, s0, s1, s2))
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)

    if mutate_kind == "skip_all":
        return events

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    return events


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_0025beb8" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases: List[Tuple[Tuple[float, float, float], int, Tuple[int, int, int]]] = []
    for state in (-128, -1, 0, 1, 2, 3, 4, 5, 127):
        for r2 in (0, 1, 2, 3, 7, 100):
            cases.append(((10.5, -3.25, 42.0), state, (-20 + (r2 % 41), 20 - (r2 % 41), r2)))

    for i, (xyz, st, draws) in enumerate(cases):
        o_ev = run_one(False, cand_info, xyz, st, draws)
        c_ev = run_one(True, cand_info, xyz, st, draws)
        if o_ev != c_ev:
            print(f"MISMATCH on case {i} (xyz={xyz}, state={st}, draws={draws}):")
            print(f"  orig={o_ev}")
            print(f"  cand={c_ev}")
            return 1

    mutants = [
        ("skip_all", ((10.5, -3.25, 42.0), 0, (5, -5, 3))),
        ("bad_rand", ((10.5, -3.25, 42.0), 1, (5, -5, 3))),
        ("bad_fx_id", ((10.5, -3.25, 42.0), 2, (5, -5, 3))),
        ("bad_x", ((10.5, -3.25, 42.0), 3, (5, -5, 3))),
        ("bad_z", ((10.5, -3.25, 42.0), 4, (5, -5, 3))),
    ]
    detected = 0
    for name, (xyz, st, draws) in mutants:
        o_ev = run_one(False, cand_info, xyz, st, draws)
        m_ev = run_one(True, cand_info, xyz, st, draws, mutate_kind=name)
        if o_ev != m_ev:
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
