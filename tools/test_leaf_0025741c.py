#!/usr/bin/env python3
"""Differential Unicorn verification for battle_func_0025741c (0x0025741c)."""

from __future__ import annotations

import struct
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from unicorn import UC_ARCH_ARM, UC_MODE_ARM, Uc
from unicorn.arm_const import (
    UC_ARM_REG_CPSR,
    UC_ARM_REG_LR,
    UC_ARM_REG_PC,
    UC_ARM_REG_R0,
    UC_ARM_REG_R1,
    UC_ARM_REG_R2,
    UC_ARM_REG_R3,
    UC_ARM_REG_SP,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.build_check import compile_tu_armv6k

TU_REL = "src/engine/leaf_batch46_a.cpp"
FUNC_NAME = "battle_func_0025741c"
ORIG_ADDR = 0x0025741C
ORIG_SIZE = 312
ORIG_CALLEE_BL = 0x002C5FA4
ORIG_GLOBAL_PTR = 0x0044EA00

ORIG_BYTES = bytes.fromhex(
    "2c119fe570402de9070050e30050a0e3"
    "004091e500f19f377080bde854742500"
    "547425009c742500d8742500d8742500"
    "14752500147525000020a0e30710a0e3"
    "0600a0e3cfba01eb014a84e2ab4f84e2"
    "001094e5012184e0081092e5080082e5"
    "1820d4e5000052e300005101e9ffff0a"
    "1c1094e531ff2fe11850c4e57080bde8"
    "0020a0e30110a0e30600a0e3bdba01eb"
    "014a84e2ab4f84e2001094e5012184e0"
    "081092e5080082e51820d4e5000052e3"
    "00005101d7ffff0aecffffea0220a0e3"
    "0110a0e30600a0e3aeba01eb014a84e2"
    "ab4f84e2001094e5012184e0081092e5"
    "080082e51820d4e5000052e300005101"
    "c8ffff0addffffea0120a0e30010a0e3"
    "0500a0e39fba01eb014a84e2ab4f84e2"
    "001094e5012184e0081092e5080082e5"
    "1820d4e5000052e300005101cfffff1a"
    "7080bde800ea4400"
)
assert len(ORIG_BYTES) == ORIG_SIZE

CODE_BASE = 0x00100000
CODE_SIZE = 0x00400000
CAND_BASE = 0x00500000
CAND_SIZE = 0x00100000
DATA_BASE = 0x00600000
DATA_SIZE = 0x00200000
STACK_BASE = 0x00900000
STACK_SIZE = 0x00020000
GPU_BASE = 0x00620000
LOG_BASE = 0x00640000
FLUSH_STUB = 0x00660000
SENTINEL = 0x005F0000


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

    symtab_idx, sym_sh, sym_bytes = sections[".symtab"]
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
    text_bytes = b""
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
    cand_callees = {
        "battle_func_002c5fa4": 0,
    }
    global_ptr_addr = CAND_BASE + 0x50000
    uc.mem_write(global_ptr_addr, struct.pack("<I", GPU_BASE))

    def get_stub(name: str) -> int:
        if name not in ext_stubs:
            ext_stubs[name] = stub_cursor
            # bx lr
            uc.mem_write(stub_cursor, struct.pack("<I", 0xE12FFF1E))
            return stub_cursor
        return ext_stubs[name]

    for target_sec, r_offset, r_type, r_sym in rel_entries:
        patch_addr = sec_addrs[target_sec] + r_offset
        sym_name, sym_val, _, _, sym_shndx = syms[r_sym]
        if sym_shndx == 0:
            if sym_name == "g_AsdGpuState":
                target_addr = global_ptr_addr
            else:
                target_addr = get_stub(sym_name)
                if ext_stubs[sym_name] == stub_cursor:
                    stub_cursor += 4
                cand_callees[sym_name] = target_addr
        else:
            target_addr = sec_addrs[sym_shndx] + sym_val

        cur_word = struct.unpack("<I", uc.mem_read(patch_addr, 4))[0]
        if r_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            imm24 = ((target_addr - (patch_addr + 8)) >> 2) & 0x00FFFFFF
            patched = (cur_word & 0xFF000000) | imm24
            uc.mem_write(patch_addr, struct.pack("<I", patched))
        elif r_type == 2:  # R_ARM_ABS32
            uc.mem_write(patch_addr, struct.pack("<I", (cur_word + target_addr) & 0xFFFFFFFF))
        elif r_type in (43, 44):  # R_ARM_MOVW_ABS_NC / R_ARM_MOVT_ABS
            imm16 = (target_addr & 0xFFFF) if r_type == 43 else ((target_addr >> 16) & 0xFFFF)
            imm4 = (imm16 >> 12) & 0xF
            imm12 = imm16 & 0xFFF
            patched = (cur_word & 0xFFF0F000) | (imm4 << 16) | imm12
            uc.mem_write(patch_addr, struct.pack("<I", patched))
        elif r_type == 42:  # R_ARM_PREL31 (.ARM.exidx)
            continue
        else:
            raise RuntimeError(f"unsupported reloc type {r_type} for {sym_name}")

    return cand_callees["battle_func_002c5fa4"], global_ptr_addr


def run_one(
    use_candidate: bool,
    cand_info,
    mode: int,
    idx: int,
    init_slot_val: int,
    init_flag: int,
    mutate_kind: str = "",
):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_map(CAND_BASE, CAND_SIZE)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)

    uc.mem_write(SENTINEL, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(FLUSH_STUB, struct.pack("<I", 0xE12FFF1E))

    # Initialize GPU state
    uc.mem_write(GPU_BASE, b"\x00" * 0x2000)
    state_addr = GPU_BASE + 0x12AC
    uc.mem_write(state_addr + 0x00, struct.pack("<I", idx))
    uc.mem_write(state_addr + 0x08 + idx * 4, struct.pack("<I", init_slot_val))
    uc.mem_write(state_addr + 0x18, bytes([init_flag]))
    uc.mem_write(state_addr + 0x1C, struct.pack("<I", FLUSH_STUB))

    if not use_candidate:
        uc.mem_write(ORIG_ADDR, ORIG_BYTES)
        uc.mem_write(ORIG_GLOBAL_PTR, struct.pack("<I", GPU_BASE))
        uc.mem_write(ORIG_CALLEE_BL, struct.pack("<I", 0xE12FFF1E))
        entry_addr = ORIG_ADDR
        bl_addr = ORIG_CALLEE_BL
    else:
        func_addr, _, sec_addrs, sec_by_idx, syms, rel_entries = cand_info
        bl_addr, _ = build_cand_stubs_and_relocate(
            uc, sec_addrs, sec_by_idx, syms, rel_entries
        )
        entry_addr = func_addr

    events: List[Tuple[str, Tuple[int, ...]]] = []

    def hook_code(uc_inst: Uc, address: int, size: int, user_data):
        if address == bl_addr:
            a0 = uc_inst.reg_read(UC_ARM_REG_R0)
            a1 = uc_inst.reg_read(UC_ARM_REG_R1)
            a2 = uc_inst.reg_read(UC_ARM_REG_R2)
            events.append(("cmd", (a0, a1, a2)))
            ret_val = ((a0 * 0x10000) ^ (a1 * 0x100) ^ a2 ^ 0x12345678) & 0xFFFFFFFF
            if mutate_kind == "bad_ret":
                ret_val ^= 1
            uc_inst.reg_write(UC_ARM_REG_R0, ret_val)
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))
        elif address == FLUSH_STUB:
            events.append(("flush", ()))
            uc_inst.reg_write(UC_ARM_REG_PC, uc_inst.reg_read(UC_ARM_REG_LR))

    from unicorn import UC_HOOK_CODE

    uc.hook_add(UC_HOOK_CODE, hook_code)

    sp = STACK_BASE + STACK_SIZE - 0x200
    uc.reg_write(UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(UC_ARM_REG_SP, sp)
    uc.reg_write(UC_ARM_REG_LR, SENTINEL)
    uc.reg_write(UC_ARM_REG_R0, mode)
    uc.reg_write(UC_ARM_REG_R1, 0x11111111)
    uc.reg_write(UC_ARM_REG_R2, 0x22222222)
    uc.reg_write(UC_ARM_REG_R3, 0x33333333)

    if mutate_kind == "skip_call":
        return events, b""

    uc.emu_start(entry_addr, SENTINEL, timeout=2_000_000, count=200_000)

    if mutate_kind == "corrupt_flag":
        uc.mem_write(state_addr + 0x18, b"\x55")
    elif mutate_kind == "corrupt_slot":
        uc.mem_write(state_addr + 0x08 + idx * 4, struct.pack("<I", 0xDEADBEEF))
    elif mutate_kind == "extra_flush":
        events.append(("flush", ()))

    state_dump = bytes(uc.mem_read(state_addr, 0x24))
    return events, state_dump


def main() -> int:
    obj_path = REPO_ROOT / "build" / "leaf_0025741c" / "leaf_batch46_a.o"
    obj_path.parent.mkdir(parents=True, exist_ok=True)
    res = compile_tu_armv6k(REPO_ROOT / TU_REL, obj_path, REPO_ROOT)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        return res.returncode
    cand_info = load_candidate_func(obj_path, FUNC_NAME)
    _, cand_size, _, _, _, _ = cand_info

    # Compute expected return values for each mode to test both prev == val and prev != val
    def expected_val(m: int) -> int:
        if m in (0, 1):
            a0, a1, a2 = 6, 7, 0
        elif m == 2:
            a0, a1, a2 = 6, 1, 0
        elif m in (3, 4):
            a0, a1, a2 = 6, 1, 2
        else:
            a0, a1, a2 = 5, 0, 1
        return ((a0 * 0x10000) ^ (a1 * 0x100) ^ a2 ^ 0x12345678) & 0xFFFFFFFF

    cases: List[Tuple[int, int, int, int]] = []
    # All modes 0..6 with prev != val and flag == 0
    for m in range(7):
        cases.append((m, m % 4, 0xCAFEBABE, 0))
    # All modes 0..6 with prev == val and flag == 0 (should NOT flush)
    for m in range(7):
        cases.append((m, (m + 1) % 4, expected_val(m), 0))
    # All modes 0..6 with prev == val and flag == 1 (SHOULD flush and clear flag)
    for m in range(7):
        cases.append((m, (m + 2) % 4, expected_val(m), 1))
    # Out-of-range modes >= 7 (early return, no cmd, no flush, flag untouched)
    for m in (7, 8, 0xFFFFFFFF):
        cases.append((m, 0, 0x11223344, 1))
        cases.append((m, 2, 0x11223344, 0))

    for i, (m, idx, init_val, init_flag) in enumerate(cases):
        o_ev, o_mem = run_one(False, cand_info, m, idx, init_val, init_flag)
        c_ev, c_mem = run_one(True, cand_info, m, idx, init_val, init_flag)
        if o_ev != c_ev or o_mem != c_mem:
            print(f"MISMATCH on case {i} (mode={m}, idx={idx}, init_val=0x{init_val:08x}, flag={init_flag}):")
            print(f"  orig ev={o_ev} mem={o_mem.hex()}")
            print(f"  cand ev={c_ev} mem={c_mem.hex()}")
            return 1

    mutants = [
        ("skip_call", (0, 0, 0xCAFEBABE, 0)),
        ("bad_ret", (2, 1, 0xCAFEBABE, 0)),
        ("corrupt_flag", (0, 0, expected_val(0), 1)),
        ("corrupt_slot", (3, 2, 0xCAFEBABE, 0)),
        ("extra_flush", (5, 0, expected_val(5), 0)),
    ]
    detected = 0
    for name, (m, idx, init_val, init_flag) in mutants:
        o_ev, o_mem = run_one(False, cand_info, m, idx, init_val, init_flag)
        m_ev, m_mem = run_one(True, cand_info, m, idx, init_val, init_flag, mutate_kind=name)
        if (o_ev, o_mem) != (m_ev, m_mem):
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
