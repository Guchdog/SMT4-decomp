#!/usr/bin/env python3
"""Differential test for engine_func_0011bf0c (0x0011bf0c) using Unicorn ARM emulation."""

import struct
import sys
from pathlib import Path
import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
FUNC_ADDR = 0x0011bf0c
FUNC_SIZE = 632

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
HEAP_ADDR  = 0x00200000
HEAP_SIZE  = 0x00020000  # 128KB
TRAP_ADDR  = 0x90000000

def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)

def get_symbol_offset(obj_file, sym_name):
    data = Path(obj_file).read_bytes()
    e_shoff, e_shentsize, e_shnum, e_shstrndx = struct.unpack_from("<IIHH", data, 32)[0], struct.unpack_from("<H", data, 46)[0], struct.unpack_from("<H", data, 48)[0], struct.unpack_from("<H", data, 50)[0]
    sections = [struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize) for i in range(e_shnum)]
    symtab = [s for s in sections if s[1] == 2][0]
    strtab = sections[symtab[6]]
    for i in range(symtab[5] // 16):
        st_name, st_val, st_size, st_info, st_other, st_shndx = struct.unpack_from("<IIIBBH", data, symtab[4] + i * 16)
        name = data[strtab[4] + st_name:].split(b"\x00")[0].decode("ascii", errors="replace")
        if sym_name == name or name == f"_{sym_name}":
            return st_val
    return 0

def compile_candidate():
    out_dir = ROOT / "build/test_leaf_0011bf0c"
    out_dir.mkdir(parents=True, exist_ok=True)
    obj_file = out_dir / "leaf_batch45_a.o"
    src_file = ROOT / "src/engine/leaf_batch45_a.cpp"
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    cand_entry = None
    for k in funcs:
        if "0011bf0c" in k:
            cand_entry = funcs[k]
            break
    if not cand_entry:
        raise RuntimeError(f"Function engine_func_0011bf0c not found in {obj_file}: available {list(funcs.keys())}")
    
    code_raw, relocs = cand_entry
    code = bytearray(code_raw)
    func_sym_offset = get_symbol_offset(obj_file, "engine_func_0011bf0c")

    for rel in relocs:
        offset = rel.offset
        sym = rel.symbol_name
        if rel.relocation_type == 2:  # R_ARM_ABS32
            orig_addend = struct.unpack_from("<I", code, offset)[0]
            if sym == ".text":
                target = FUNC_ADDR + (orig_addend - func_sym_offset)
                struct.pack_into("<I", code, offset, target)
    return bytes(code)

class HeapRunner:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(FUNC_ADDR & ~0xFFF, 0x10000)
        self.uc.mem_map(HEAP_ADDR, HEAP_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

    def run(self, code_bytes, heap_image, r0, r1, r2):
        self.uc.mem_write(FUNC_ADDR, code_bytes)
        self.uc.mem_write(HEAP_ADDR, heap_image)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, r0)
        self.uc.reg_write(arm.UC_ARM_REG_R1, r1)
        self.uc.reg_write(arm.UC_ARM_REG_R2, r2)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except Exception as e:
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {e}")

        ret_r0 = self.uc.reg_read(arm.UC_ARM_REG_R0)
        heap_out = bytes(self.uc.mem_read(HEAP_ADDR, len(heap_image)))
        return ret_r0, heap_out

def build_test_heap(opt_flag=0):
    # Returns bytearray of size 0x2000 representing heap memory
    buf = bytearray(0x2000)
    # heap is at HEAP_ADDR
    # heap + 0x18:
    # heap + 0x38 (0x18 + 0x20): optFlag
    struct.pack_into("<I", buf, 0x38, opt_flag)
    # heap + 0x3c (0x18 + 0x24): freeList.head
    # heap + 0x40 (0x18 + 0x28): freeList.tail
    return buf

def set_mblock(buf, offset, sig, attr, size, prev=0, next_=0):
    struct.pack_into("<HHI", buf, offset, sig, attr, size)
    struct.pack_into("<II", buf, offset + 8, prev, next_)

def main():
    print("Testing engine_func_0011bf0c (0x0011bf0c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()

    runner = HeapRunner()

    test_cases = []

    # Case 1: Same size -> no-op return
    h1 = build_test_heap()
    # mem_block at HEAP_ADDR + 0x200 (header at 0x1f0)
    set_mblock(h1, 0x1f0, 0x5544, 0, 64) # 'UD'
    test_cases.append({
        "name": "Same size (64 -> 64)",
        "heap": bytes(h1),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 64
    })

    # Case 2: Same size with unaligned request (64 -> 63)
    test_cases.append({
        "name": "Same size unaligned (64 -> 63)",
        "heap": bytes(h1),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 63
    })

    # Case 3: Expand - no adjacent free block
    test_cases.append({
        "name": "Expand with empty free list (should fail -> 0)",
        "heap": bytes(h1),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 128
    })

    # Case 4: Expand - adjacent free block too small
    h4 = build_test_heap()
    set_mblock(h4, 0x1f0, 0x5544, 0, 64)
    # adjacent free block at 0x200 + 64 = 0x240, size 32 (total available = 64 + 32 + 16 = 112)
    set_mblock(h4, 0x240, 0x4652, 0, 32, 0, 0)
    struct.pack_into("<II", h4, 0x3c, HEAP_ADDR + 0x240, HEAP_ADDR + 0x240)
    test_cases.append({
        "name": "Expand adjacent free block too small (avail 112, req 128 -> 0)",
        "heap": bytes(h4),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 128
    })

    # Case 5: Expand - adjacent free block exact fit (remaining < 16)
    # req 110 (aligned to 112), available is 112 -> absorbs entire free block
    test_cases.append({
        "name": "Expand adjacent free block exact fit (absorb all)",
        "heap": bytes(h4),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 110
    })

    # Case 6: Expand - with leftover >= 16 (creates new free block)
    h6 = build_test_heap(opt_flag=1)
    set_mblock(h6, 0x1f0, 0x5544, 0, 64)
    # free block at 0x240, size 128 (total available = 64 + 128 + 16 = 208)
    set_mblock(h6, 0x240, 0x4652, 0, 128, 0, 0)
    struct.pack_into("<II", h6, 0x3c, HEAP_ADDR + 0x240, HEAP_ADDR + 0x240)
    # fill free payload with 0xAA to verify zero-clearing
    for i in range(128):
        h6[0x250 + i] = 0xAA
    test_cases.append({
        "name": "Expand with leftover and zero-fill optFlag=1 (req 96)",
        "heap": bytes(h6),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 96
    })

    # Case 7: Shrink - leftover < 16 (cannot shrink, reverts)
    h7 = build_test_heap()
    set_mblock(h7, 0x1f0, 0x5544, 0, 64)
    test_cases.append({
        "name": "Shrink leftover < 16 (64 -> 56, diff 8 < 16 -> revert 64)",
        "heap": bytes(h7),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 56
    })

    # Case 8: Shrink - creates new free block, no merges
    test_cases.append({
        "name": "Shrink no merge (64 -> 32, freed 32 >= 16)",
        "heap": bytes(h7),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 32
    })

    # Case 9: Shrink - merges with next free block
    h9 = build_test_heap()
    set_mblock(h9, 0x1f0, 0x5544, 0, 64)
    # free block at 0x240 (size 48)
    set_mblock(h9, 0x240, 0x4652, 0, 48, 0, 0)
    struct.pack_into("<II", h9, 0x3c, HEAP_ADDR + 0x240, HEAP_ADDR + 0x240)
    test_cases.append({
        "name": "Shrink merges with next adjacent free block",
        "heap": bytes(h9),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 32
    })

    # Case 10: Shrink - merges with prev free block
    h10 = build_test_heap()
    # free block at 0x1a0 (header 0x190), size 0x50 (ends at 0x190 + 0x10 + 0x50 = 0x1f0)
    set_mblock(h10, 0x190, 0x4652, 0, 0x50, 0, 0)
    set_mblock(h10, 0x1f0, 0x5544, 0, 64)
    struct.pack_into("<II", h10, 0x3c, HEAP_ADDR + 0x190, HEAP_ADDR + 0x190)
    test_cases.append({
        "name": "Shrink merges with prev adjacent free block (shrink to 0)",
        "heap": bytes(h10),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 0
    })

    # Case 11: Shrink - merges with BOTH prev and next free blocks!
    h11 = build_test_heap()
    set_mblock(h11, 0x190, 0x4652, 0, 0x50, 0, HEAP_ADDR + 0x240)
    set_mblock(h11, 0x1f0, 0x5544, 0, 64)
    set_mblock(h11, 0x240, 0x4652, 0, 48, HEAP_ADDR + 0x190, 0)
    struct.pack_into("<II", h11, 0x3c, HEAP_ADDR + 0x190, HEAP_ADDR + 0x240)
    test_cases.append({
        "name": "Shrink merges with BOTH prev and next free blocks (shrink to 0)",
        "heap": bytes(h11),
        "r0": HEAP_ADDR,
        "r1": HEAP_ADDR + 0x200,
        "r2": 0
    })

    total = 0
    passed = 0
    for tc in test_cases:
        total += 1
        ret_orig, mem_orig = runner.run(orig_code, tc["heap"], tc["r0"], tc["r1"], tc["r2"])
        ret_cand, mem_cand = runner.run(cand_code, tc["heap"], tc["r0"], tc["r1"], tc["r2"])

        assert ret_orig == ret_cand, f"Return value mismatch on {tc['name']}: orig={ret_orig}, cand={ret_cand}"
        assert mem_orig == mem_cand, f"Heap memory mismatch on {tc['name']}"
        passed += 1
        print(f"  [PASS] {tc['name']}: returned {ret_cand}")

    print(f"\nAll {passed}/{total} differential test cases PASSED!")

if __name__ == "__main__":
    main()
