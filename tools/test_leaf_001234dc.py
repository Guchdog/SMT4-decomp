#!/usr/bin/env python3
"""Differential test for func_001234dc (0x001234dc) using Unicorn ARM.

The original selects one of two render views from its mode argument
(0x400/0x402 -> view 0, 0x401/0x402 -> view 1, everything else is ignored),
classifies the view's scene-node type, folds the node/state fields into three
parameters, merges an extra scene node for renderer state 0x702, calls the
7-argument renderer wrapper at 0x001376a4, and inverts the view's boolean.

The renderer wrapper is stubbed deterministically so the original and the
compiled C++ candidate can be compared on call order/arguments (including the
three stack words), return PC/SP, callee-saved registers, and the full
observable state/node/stack memory.
"""

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
FUNC_ADDR = 0x001234DC
FUNC_SIZE = 408

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers 0x00100000..0x00300000 (stub address)
STATE_ADDR = 0x004C6000
STATE_SIZE = 0x00001000
STATE_BASE = 0x004C6290
NODE_ADDR = 0x00500000
NODE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

NODE0 = NODE_ADDR
NODE1 = NODE_ADDR + 0x1000
NODE_EXTRA = NODE_ADDR + 0x2000

STUB_RENDER = 0x002F0000  # func_001376a4 wrapper around 0x0013AAF0

STUB_BY_SYMBOL = {
    "func_001376a4": STUB_RENDER,
}

# State offsets read by the original.
OFF_SOURCE0 = 0x008
OFF_SOURCE1 = 0x00C
OFF_NODE0 = 0x128
OFF_NODE1 = 0x12C
OFF_NODE_EXTRA = 0x130
OFF_BIAS0 = 0x134
OFF_BIAS1 = 0x138
OFF_LIMIT0 = 0x140
OFF_LIMIT1 = 0x144
OFF_EXTRA_EXTENT = 0x148
OFF_FLAG0 = 0x14C
OFF_FLAG1 = 0x150
OFF_EXTRA_BIAS = 0x13C
OFF_RENDERER_STATE = 0x164

# Scene-node offsets.
N_BASE = 0x04
N_TYPE = 0x08
N_SCALE = 0x0C
N_EXTENT = 0x10
N_MODE = 0x14


def get_orig_bytes():
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def get_symbol_offset(obj_file, sym_name):
    data = Path(obj_file).read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    symtab = [s for s in sections if s[1] == 2][0]
    for i in range(symtab[5] // 16):
        st_name, st_val, st_size, st_info, st_other, st_shndx = struct.unpack_from(
            "<IIIBBH", data, symtab[4] + i * 16
        )
        name = data[sections[symtab[6]][4] + st_name:].split(b"\x00")[0]
        if name.decode("ascii", errors="replace") == sym_name:
            return st_val
    return 0


def compile_candidate_from(src_file, obj_file):
    res = compile_tu_armv6k(src_file, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")

    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get("func_001234dc")
    if entry is None:
        raise RuntimeError(
            "func_001234dc not found in object: " + ", ".join(sorted(funcs))
        )

    code = bytearray(entry[0])
    relocs = entry[1]
    errors = []
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            errors.append(f"unexpected relocation {rel.relocation_type} {rel.symbol_name}")
            continue
        target = STUB_BY_SYMBOL.get(rel.symbol_name)
        if target is None:
            errors.append(f"no stub for {rel.symbol_name}")
            continue
        pc = FUNC_ADDR + rel.offset + 8
        disp = (target - pc) >> 2
        orig_inst = struct.unpack_from("<I", code, rel.offset)[0]
        cond = orig_inst & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (disp & 0x00FFFFFF))
    if errors:
        raise RuntimeError("; ".join(errors))

    return bytes(code)


def compile_candidate():
    out_dir = ROOT / "build/test_leaf_001234dc"
    out_dir.mkdir(parents=True, exist_ok=True)
    return compile_candidate_from(
        ROOT / "src/engine/leaf_batch28_a.cpp",
        out_dir / "engine" / "leaf_batch28_a.o",
    )


def compile_mutant(name, old, new):
    out_dir = ROOT / "build/test_leaf_001234dc"
    out_dir.mkdir(parents=True, exist_ok=True)
    source = ROOT / "src/engine/leaf_batch28_a.cpp"
    text = source.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = out_dir / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate_from(mutant_src, out_dir / f"mutant_{name}.o")


def default_node(type=0x8057, base=0x100, scale=2, extent=0x40, mode=0x10000):
    return {
        N_BASE: base,
        N_TYPE: type,
        N_SCALE: scale,
        N_EXTENT: extent,
        N_MODE: mode,
    }


def default_state(overrides=None):
    state = {
        OFF_SOURCE0: 0x10,
        OFF_SOURCE1: 0x20,
        OFF_BIAS0: 0x30,
        OFF_BIAS1: 0x34,
        OFF_LIMIT0: 0x08,
        OFF_LIMIT1: 0x0C,
        OFF_EXTRA_EXTENT: 0x44,
        OFF_FLAG0: 0,
        OFF_FLAG1: 0,
        OFF_EXTRA_BIAS: 0x48,
        OFF_RENDERER_STATE: 0x700,
    }
    state.update(overrides or {})
    return state


class Runner:
    def __init__(self):
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        self.call_log = []
        self.stub_flag_value = None

        self.uc.mem_write(STUB_RENDER, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_render, begin=STUB_RENDER, end=STUB_RENDER
        )

    def _on_render(self, uc, address, size, user_data):
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        stack = struct.unpack("<III", uc.mem_read(sp, 12))
        self.call_log.append(("func_001376a4", r0, r1, r2, r3, *stack))
        if self.stub_flag_value is not None:
            flag_addr = STATE_BASE + OFF_FLAG0 + r0 * 4
            uc.mem_write(
                flag_addr, struct.pack("<I", self.stub_flag_value & 0xFFFFFFFF)
            )

    def run(self, code_bytes, case):
        self.call_log = []
        self.stub_flag_value = case.get("stub_flag_value")

        self.uc.mem_write(FUNC_ADDR, code_bytes)
        # Unicorn caches translated blocks; overwriting the function at the
        # same addresses requires an explicit flush between runs.
        self.uc.ctl_remove_cache(FUNC_ADDR, FUNC_ADDR + 0x1000)

        self.uc.mem_write(STATE_ADDR, b"\x00" * STATE_SIZE)
        self.uc.mem_write(NODE_ADDR, b"\x00" * NODE_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        state = bytearray(self.uc.mem_read(STATE_BASE, 0x200))
        for offset, value in case["state"].items():
            struct.pack_into("<I", state, offset, value & 0xFFFFFFFF)
        struct.pack_into("<I", state, OFF_NODE0, NODE0)
        struct.pack_into("<I", state, OFF_NODE1, NODE1)
        struct.pack_into("<I", state, OFF_NODE_EXTRA, NODE_EXTRA)
        self.uc.mem_write(STATE_BASE, bytes(state))

        for node_addr, fields in (
            (NODE0, case["node0"]),
            (NODE1, case["node1"]),
            (NODE_EXTRA, case["node_extra"]),
        ):
            for offset, value in fields.items():
                self.uc.mem_write(
                    node_addr + offset, struct.pack("<I", value & 0xFFFFFFFF)
                )

        sp = STACK_ADDR + STACK_SIZE - 0x100
        self.uc.reg_write(arm.UC_ARM_REG_SP, sp)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["mode"])
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)

        callee_saved = [
            arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
            arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8, arm.UC_ARM_REG_R9,
            arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11,
        ]
        for index, reg in enumerate(callee_saved):
            self.uc.reg_write(reg, 0x11110000 + index * 0x11)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5000000)
        except unicorn.UcError as exc:
            raise RuntimeError(
                f"Crash at PC=0x{self.uc.reg_read(arm.UC_ARM_REG_PC):08x}: {exc}"
            )

        return {
            "call_log": list(self.call_log),
            "state": bytes(self.uc.mem_read(STATE_BASE, 0x200)),
            "nodes": bytes(self.uc.mem_read(NODE_ADDR, 0x3000)),
            "stack": bytes(self.uc.mem_read(STACK_ADDR, STACK_SIZE)),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "callee_saved": [self.uc.reg_read(reg) for reg in callee_saved],
        }


def make_cases():
    return [
        {
            "name": "view 0, type 0x8057, mode 0x10000, state 0x700, flag 0",
            "mode": 0x402,
            "state": default_state(),
            "node0": default_node(),
            "node1": default_node(type=0x8051),
            "node_extra": default_node(type=0x8D62),
        },
        {
            "name": "view 0 via 0x400, type 0x8051, non-0x10000 mode, flag nonzero",
            "mode": 0x400,
            "state": default_state({OFF_FLAG0: 0xDEADBEEF}),
            "node0": default_node(type=0x8051, mode=0x10001),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "view 0, type 0x8056, state 0x701 clears the 0x40 bit",
            "mode": 0x402,
            "state": default_state({OFF_RENDERER_STATE: 0x701}),
            "node0": default_node(type=0x8056),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "view 0, type 0x8058, state 0x702 merges the extra node",
            "mode": 0x402,
            "state": default_state({OFF_RENDERER_STATE: 0x702, OFF_FLAG0: 1}),
            "node0": default_node(type=0x8058),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(
                base=0x200, type=0x8057, scale=5, extent=0x60, mode=0x10001
            ),
        },
        {
            "name": "view 0, type 0x8D62, state 0x6FF keeps the 0x40 bit",
            "mode": 0x402,
            "state": default_state({OFF_RENDERER_STATE: 0x6FF}),
            "node0": default_node(type=0x8D62, mode=0),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "view 0, unknown type, state 0x703 keeps the 0x40 bit",
            "mode": 0x402,
            "state": default_state({OFF_RENDERER_STATE: 0x703}),
            "node0": default_node(type=0),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "view 1 via 0x401, type 0x8057, view-1 flag nonzero",            "mode": 0x401,
            "state": default_state({OFF_FLAG1: 0x12345678, OFF_RENDERER_STATE: 0x702}),
            "node0": default_node(type=0x8051),
            "node1": default_node(type=0x8057, mode=0x10001),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "view 1 via 0x401, signed boundary type 0x80000000 takes the low branch",
            "mode": 0x401,
            "state": default_state(),
            "node0": default_node(type=0x8057),
            "node1": default_node(type=0x80000000),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "view 1 via 0x401, type 0x8058, 32-bit multiply/add wrap",
            "mode": 0x401,
            "state": default_state(
                {
                    OFF_SOURCE1: 0xFFFFFFFE,
                    OFF_BIAS1: 0xFFFFFFF0,
                    OFF_LIMIT1: 1,
                }
            ),
            "node0": default_node(type=0x8057),
            "node1": default_node(
                base=0x7FFFFFFF,
                type=0x8058,
                scale=0xFFFFFFFF,
                extent=0xFFFFFFFF,
                mode=0xFFFFFFFF,
            ),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "post-call re-read: stub clears a non-zero view-0 flag",
            "mode": 0x400,
            "state": default_state({OFF_FLAG0: 5}),
            "node0": default_node(type=0x8057),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
            "stub_flag_value": 0,
        },
        {
            "name": "post-call re-read: stub sets a zero view-0 flag",
            "mode": 0x400,
            "state": default_state({OFF_FLAG0: 0}),
            "node0": default_node(type=0x8057),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
            "stub_flag_value": 7,
        },
        {
            "name": "no work for mode 0x000",
            "mode": 0x000,
            "state": default_state({OFF_FLAG0: 7, OFF_FLAG1: 9}),
            "node0": default_node(type=0x8057),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "no work for mode 0x3FF",
            "mode": 0x3FF,
            "state": default_state({OFF_FLAG0: 7, OFF_FLAG1: 9}),
            "node0": default_node(type=0x8057),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
        },
        {
            "name": "no work for mode 0x404",
            "mode": 0x404,
            "state": default_state({OFF_FLAG0: 7, OFF_FLAG1: 9}),
            "node0": default_node(type=0x8057),
            "node1": default_node(type=0x8057),
            "node_extra": default_node(type=0x8057),
        },
    ]


def main():
    print("Testing func_001234dc (0x001234dc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()

    runner = Runner()
    cases = make_cases()

    passed = 0
    for case in cases:
        res_orig = runner.run(orig_code, case)
        res_cand = runner.run(cand_code, case)

        assert res_orig["call_log"] == res_cand["call_log"], (
            f"Call log mismatch on {case['name']}:\n"
            f"  Orig: {res_orig['call_log']}\n  Cand: {res_cand['call_log']}"
        )
        assert res_orig["state"] == res_cand["state"], (
            f"State memory mismatch on {case['name']}"
        )
        assert res_orig["nodes"] == res_cand["nodes"], (
            f"Node memory mismatch on {case['name']}"
        )
        assert res_orig["stack"] == res_cand["stack"], (
            f"Stack memory mismatch on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"], (
            f"SP mismatch on {case['name']}: {res_orig['sp']:#x} vs {res_cand['sp']:#x}"
        )
        assert res_orig["pc"] == res_cand["pc"] == TRAP_ADDR, (
            f"PC mismatch on {case['name']}: {res_orig['pc']:#x} vs {res_cand['pc']:#x}"
        )
        assert res_orig["callee_saved"] == res_cand["callee_saved"], (
            f"callee-saved register mismatch on {case['name']}"
        )

        entry_sp = STACK_ADDR + STACK_SIZE - 0x100
        assert res_orig["sp"] == entry_sp, f"stack not restored on {case['name']}"

        passed += 1
        print(f"  [PASS] {case['name']}")

    # Derived expectations for the most important case: the renderer call and
    # the inverted view-0 boolean must actually be present.
    res = runner.run(orig_code, cases[0])
    assert len(res["call_log"]) == 2
    _name, slot, value, param_a, param_b, param_c, flags, value_copy = res["call_log"][0]
    assert slot == 0 and value == 0 and value_copy == 0
    assert param_b == 0
    assert flags == (3 | 0x100 | 0x40)
    assert (param_c, param_a) == (2 * 2, 2 * (2 * (0x40 - 0x10 - 0x08) + 0x30) + 0x100)
    second = res["call_log"][1]
    assert second[1] == 1 and second[7] == 0
    assert second[6] == (1 | 0x100)  # view 1 never takes the 0x40/0x20 bits
    assert struct.unpack_from("<I", res["state"], OFF_FLAG0)[0] == 1
    assert struct.unpack_from("<I", res["state"], OFF_FLAG1)[0] == 1
    print("  [PASS] derived renderer parameters and boolean inversion")

    print("\nNegative controls:")
    mutants = [
        (
            "misclassified_0x8056",
            "} else if (diff == 5) {",
            "} else if (diff == 6) {",
        ),
        (
            "swapped_node_mode_bits",
            "? 0x100u : 0x300u",
            "? 0x300u : 0x100u",
        ),
        (
            "extra_node_uses_view1_pointer",
            "loadNode(state, kExtraNode)",
            "loadNode(state, 0x12c)",
        ),
        (
            "toggle_always_one",
            "*flag = (*flag == 0) ? 1u : 0u;",
            "*flag = 1u;",
        ),
        (
            "state_701_keeps_40_bit",
            "            } else if (rendererState - 0x701u == 0) {\n                // 0x701: class/mode bits only, without the 0x40 bit.",
            "            } else if (rendererState - 0x701u == 0) {\n                flags |= 0x40u;",
        ),
    ]
    for name, old, new in mutants:
        mutant_code = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            res_orig = runner.run(orig_code, case)
            res_mut = runner.run(mutant_code, case)
            if res_orig != res_mut:
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential test cases PASSED!")


if __name__ == "__main__":
    main()
