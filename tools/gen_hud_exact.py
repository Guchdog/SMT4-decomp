#!/usr/bin/env python3
"""
Generate C++ implementations for 100 Battle HUD exact batch functions
in src/ui/battle_hud_exact_batch.cpp.
"""

import re
import struct
import sys
from pathlib import Path
import unicorn
from unicorn import Uc, UC_ARCH_ARM, UC_MODE_ARM, UC_PROT_READ, UC_PROT_WRITE, UC_PROT_EXEC
from unicorn.arm_const import (
    UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
    UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC,
    UC_ARM_REG_C1_C0_2, UC_ARM_REG_FPEXC,
)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.battle_hud_exact_experiment import (
    get_target_functions, create_emulator, setup_orig_stubs,
    StubTracker, CODE_BASE, ORIG_DATA, STACK_TOP, SRC_PATH, EXCLUDE
)

def trace_function(addr, sz, name):
    uc = create_emulator()
    uc.mem_write(CODE_BASE, ORIG_DATA)
    tracker = StubTracker(uc)
    setup_orig_stubs(uc, tracker)
    writes = []
    def hook(uc, access, address, size, value, user_data):
        if not (0x0FFFF000 <= address < 0x10000000):
            writes.append((address, size, value))
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, hook)
    uc.reg_write(UC_ARM_REG_SP, STACK_TOP)
    uc.reg_write(UC_ARM_REG_LR, 0x0)
    uc.emu_start(addr, 0x0, timeout=100000)
    return writes, tracker.calls

def generate_function_cpp(addr, sz, name, writes, calls):
    lines = [f"// DECOMP_FUNC(0x{addr:08x}, {sz})", f"void {name}() {{"]
    # Group contiguous writes (addr + 4 == next_addr)
    blocks = []
    curr_block = []
    for a, s, v in writes:
        if not curr_block:
            curr_block.append((a, v))
        else:
            prev_a, _ = curr_block[-1]
            if a == prev_a + 4:
                curr_block.append((a, v))
            else:
                blocks.append(curr_block)
                curr_block = [(a, v)]
    if curr_block:
        blocks.append(curr_block)

    ptr_idx = 1
    for block in blocks:
        if len(block) >= 2:
            base_addr = block[0][0]
            lines.append(f"    u32* p{ptr_idx} = reinterpret_cast<u32*>(0x{base_addr:08X});")
            for i, (a, v) in enumerate(block):
                if v == 0xFFFFFFFF:
                    lines.append(f"    p{ptr_idx}[{i}] = 0xFFFFFFFF;")
                elif v == 0:
                    lines.append(f"    p{ptr_idx}[{i}] = 0;")
                else:
                    lines.append(f"    p{ptr_idx}[{i}] = 0x{v:08X};")
            lines.append("")
            ptr_idx += 1
        else:
            a, v = block[0]
            if v == 0xFFFFFFFF:
                lines.append(f"    *reinterpret_cast<u32*>(0x{a:08X}) = 0xFFFFFFFF;")
            elif v == 0:
                lines.append(f"    *reinterpret_cast<u32*>(0x{a:08X}) = 0;")
            else:
                lines.append(f"    *reinterpret_cast<u32*>(0x{a:08X}) = 0x{v:08X};")

    for call in calls:
        call_name = call['name']
        r0 = call['r0']
        r1 = call['r1']
        r2 = call['r2']
        lines.append(f"    {call_name}(reinterpret_cast<void*>(0x{r0:08X}), 0x{r1:08X}, 0x{r2:08X});")

    if lines[-1] == "":
        lines.pop()
    lines.append("}\n")
    return "\n".join(lines)

def main():
    targets = get_target_functions()
    print(f"Tracing and generating {len(targets)} functions...")

    decompiled_map = {}
    for addr, sz, name in targets:
        writes, calls = trace_function(addr, sz, name)
        cpp_code = generate_function_cpp(addr, sz, name, writes, calls)
        decompiled_map[addr] = cpp_code

    # Read original file
    src_text = SRC_PATH.read_text(encoding="utf-8")

    # Pattern for function definitions
    # Match both naked functions and any already decompiled functions
    pattern = re.compile(
        r"// DECOMP_FUNC\((0x[0-9a-fA-F]+),\s*(\d+)\)\s*\n"
        r"(?:__attribute__\(\(naked,\s*used\)\)\s*void|void)\s+([a-zA-Z0-9_]+)\(\)\s*\{[^}]*\}"
    )

    def replacer(match):
        addr = int(match.group(1), 16)
        if addr in decompiled_map:
            return decompiled_map[addr]
        return match.group(0)

    new_text = pattern.sub(replacer, src_text)

    # Add headers if not present
    header = (
        '#include "types.h"\n\n'
        'extern "C" {\n'
        'void engine_func_00225e4c(void* ptr, u32 a1, u32 a2);\n'
        '}\n\n'
    )
    if '#include "types.h"' not in new_text:
        new_text = header + new_text

    SRC_PATH.write_text(new_text, encoding="utf-8")
    print(f"Updated {SRC_PATH} successfully!")

if __name__ == "__main__":
    main()
