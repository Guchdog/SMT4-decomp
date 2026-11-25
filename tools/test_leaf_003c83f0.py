#!/usr/bin/env python3
"""Differential Unicorn verification for battle_func_003c83f0 (0x003c83f0)."""

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
FUNC_NAME = "battle_func_003c83f0"
ORIG_ADDR = 0x003C83F0
ORIG_SIZE = 428

GLOBAL_4398D0 = 0x004398D0
GLOBAL_4342C8 = 0x004342C8

CALLEES_ORIG = {
    "FrameTex_func_00280d30": 0x00280D30,
    "btlStage_func_003c8280": 0x003C8280,
    "engine_func_00340790": 0x00340790,
    "battle_func_003406d8": 0x003406D8,
    "battle_func_0034073c": 0x0034073C,
    "ui_func_0025bd6c": 0x0025BD6C,
    "PlaceWin_SetPos": 0x0026385C,
    "battle_func_003c7f18": 0x003C7F18,
    "script_vm_func_00275c2c": 0x00275C2C,
    "script_vm_func_0024f15c": 0x0024F15C,
    "battle_func_00340588": 0x00340588,
    "battle_func_00340674": 0x00340674,
}

ORIG_BYTES = bytes.fromhex(
    "70402de9000051e30040a0e1028b2ded"
    "5c00000a78019fe5040090e5000050e3"
    "5900000a800094e568519fe55a8a9fed"
    "050050e300f19f374d0000ea64853c00"
    "40843c0060843c00f4843c0020853c00"
    "0000a0e339e2faeb0400a0e100f020e3"
    "8affffeb0200a0e300f020e3220000ea"
    "b41bd4e10400a0e1000051e33c00000a"
    "c6e0fdeb000050e300f020e33800000a"
    "900084e2030a90ec0400a0e191e0fdeb"
    "480ab0ee000095e5010b80e2401ab0ee"
    "680ad0ed0400a0e1a3e0fdeb0020a0e3"
    "d8109fe50200a0e12b4efaeb340a9fed"
    "000050e30010a0a3400af0ee401ab0ee"
    "bc08c4e1e06cfaab081084e20400a0e1"
    "060091e88bfeffeb0400a0e3800084e5"
    "1b0000eaa00094e50050a0e3000050e3"
    "a0508415c8b5faeb0400a0e100f020e3"
    "111bfaeb805084e500f020e3100000ea"
    "900084e2030a90ec0400a0e169e0fdeb"
    "480ab0ee000095e5010b80e2401ab0ee"
    "680ad0ed0400a0e17be0fdeb0400a0e1"
    "00f020e30be0fdeb0400a0e100f020e3"
    "43e0fdebbc09d4e128109fe5010050e1"
    "01008032bc09c4310000a0e3028bbdec"
    "7080bde8d0984300c842430000000000"
    "f01740000000003fffff0000"
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
CAM_BASE = 0x00740000
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
    active: int,
    g_ready: int,
    state: int,
    hb4: int,
    ok_340790: int,
    win_ret: int,
    fa0: int,
    h9c: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    enable_vfp(uc)

    uc.mem_write(GLOBAL_4398D0 + 4, struct.pack("<I", g_ready))
    uc.mem_write(GLOBAL_4342C8, struct.pack("<I", CAM_BASE))
    uc.mem_write(CAM_BASE, b"\x00" * 0x600)
    uc.mem_write(CAM_BASE + 0x5A0, struct.pack("<f", 42.5))

    uc.mem_write(SELF_BASE, b"\x00" * 0xC0)
    uc.mem_write(SELF_BASE + 0x08, struct.pack("<II", 0x11112222, 0x33334444))
    uc.mem_write(SELF_BASE + 0x80, struct.pack("<I", state))
    uc.mem_write(SELF_BASE + 0x90, struct.pack("<3f", 1.5, -2.5, 3.25))
    uc.mem_write(SELF_BASE + 0x9C, struct.pack("<H", h9c))
    uc.mem_write(SELF_BASE + 0xA0, struct.pack("<I", fa0))
    uc.mem_write(SELF_BASE + 0xB4, struct.pack("<H", hb4))

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
        r2 = uc_inst.reg_read(UC_ARM_REG_R2)
        if name == "FrameTex_func_00280d30":
            events.append((name, r0))
        elif name in ("btlStage_func_003c8280", "script_vm_func_0024f15c", "battle_func_00340588", "battle_func_00340674"):
            events.append((name, r0))
        elif name == "engine_func_00340790":
            events.append((name, r0, r1))
            uc_inst.reg_write(UC_ARM_REG_R0, ok_340790)
        elif name in ("battle_func_003406d8", "battle_func_0034073c"):
            s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S0)))[0]
            s1 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S1)))[0]
            s2 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S2)))[0]
            if mutate_kind == "bad_cam_y" and name == "battle_func_0034073c":
                s1 += 1.0
            events.append((name, r0, s0, s1, s2))
        elif name == "ui_func_0025bd6c":
            events.append((name, r0, r1, r2))
            uc_inst.reg_write(UC_ARM_REG_R0, win_ret & 0xFFFFFFFF)
        elif name == "PlaceWin_SetPos":
            s0 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S0)))[0]
            s1 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S1)))[0]
            s2 = struct.unpack("<f", struct.pack("<I", uc_inst.reg_read(UC_ARM_REG_S2)))[0]
            if mutate_kind == "bad_placewin":
                s0 += 1.0
            events.append((name, r0, r1, s0, s1, s2))
        elif name == "battle_func_003c7f18":
            if mutate_kind == "bad_7f18":
                r2 ^= 1
            events.append((name, r0, r1, r2))
        elif name == "script_vm_func_00275c2c":
            events.append((name,))
        uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    uc.hook_add(UC_HOOK_CODE, hook_code)

    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, STACK_BASE + STACK_SIZE - 0x200)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, SELF_BASE)
    uc.reg_write(UC_ARM_REG_R1, active)

    if mutate_kind == "skip_all":
        return events, 0, b""

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)
    ret = uc.reg_read(UC_ARM_REG_R0)
    if mutate_kind == "corrupt_9c":
        uc.mem_write(SELF_BASE + 0x9C, struct.pack("<H", 0xBEEF))

    self_dump = bytes(uc.mem_read(SELF_BASE, 0xC0))
    return events, ret, self_dump


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_003c83f0" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    cases = [
        # early exits
        (0, 1, 1, 1, 1, 0, 0, 0),
        (1, 0, 1, 1, 1, 0, 0, 0),
        # state 0, 1
        (1, 1, 0, 0, 0, 0, 0, 10),
        (1, 1, 1, 0, 0, 0, 0, 10),
        # state 2 branches
        (1, 1, 2, 0, 1, 0, 0, 10),
        (1, 1, 2, 5, 0, 0, 0, 10),
        (1, 1, 2, 5, 1, -1, 0, 10),
        (1, 1, 2, 5, 1, 7, 0, 10),
        # state 3
        (1, 1, 3, 0, 0, 0, 0, 10),
        (1, 1, 3, 0, 0, 0, 9, 10),
        # state 4, 5, and 0xFFFF clamp
        (1, 1, 4, 0, 0, 0, 0, 0xFFFE),
        (1, 1, 4, 0, 0, 0, 0, 0xFFFF),
        (1, 1, 5, 0, 0, 0, 0, 0),
    ]

    for i, params in enumerate(cases):
        o = run_one(False, cand_info, *params)
        c = run_one(True, cand_info, *params)
        if o != c:
            print(f"MISMATCH on case {i} ({params}):")
            print(f"  orig ev={o[0]} ret={o[1]}")
            print(f"  cand ev={c[0]} ret={c[1]}")
            return 1

    mutants = [
        ("skip_all", (1, 1, 1, 0, 0, 0, 0, 10)),
        ("bad_cam_y", (1, 1, 4, 0, 0, 0, 0, 10)),
        ("bad_placewin", (1, 1, 2, 5, 1, 7, 0, 10)),
        ("bad_7f18", (1, 1, 2, 5, 1, -1, 0, 10)),
        ("corrupt_9c", (1, 1, 0, 0, 0, 0, 0, 10)),
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
