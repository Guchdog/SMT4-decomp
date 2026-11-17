#!/usr/bin/env python3
"""Differential test for func_002f9914 (0x002F9914) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the func_002f9914 body,
resolves its direct call (0x00269CB8) and indirect handler table (0x00472718)
to deterministic stubs, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.
"""

from __future__ import annotations

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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_002f9914"

FUNC_ADDR = 0x002F9914
FUNC_SIZE = 736

CODE_ADDR = 0x00260000
CODE_SIZE = 0x000B0000  # covers 0x00269CB8..0x002F9914 + handler stub
GLOBAL1_ADDR = 0x00470000
GLOBAL1_SIZE = 0x00010000  # covers 0x00472550 and 0x00472718
GLOBAL2_ADDR = 0x004E0000
GLOBAL2_SIZE = 0x00010000  # covers 0x004EA91C..0x004EA94C
MEM_ADDR = 0x00700000
MEM_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_269CB8 = 0x00269CB8  # ui_func_00269cb8
STUB_HANDLER = 0x002D0000  # handler from 0x00472718

STUB_NAMES = {
    STUB_269CB8: "ui_func_00269cb8",
    STUB_HANDLER: "owner_handler",
}
SYMBOL_TO_ADDRESS = {name: address for address, name in STUB_NAMES.items()}

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("func_002f9914")
    if candidate is None:
        raise RuntimeError(f"func_002f9914 not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = SYMBOL_TO_ADDRESS.get(rel.symbol_name)
        if target is None:
            raise RuntimeError(f"unresolved relocation {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if offset & 3:
            raise RuntimeError(f"unaligned ARM target 0x{target:08x}")
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | ((offset >> 2) & 0x00FFFFFF))
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compile failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"mutant {name} compile failed:\n{result.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (GLOBAL1_ADDR, GLOBAL1_SIZE),
            (GLOBAL2_ADDR, GLOBAL2_SIZE),
            (MEM_ADDR, MEM_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(addr, size)

        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=STUB_269CB8,
            end=STUB_HANDLER + 4,
        )

        self.case: dict = {}
        self.call_log: list[tuple] = []

    def _on_stub(self, uc, address, size, user_data) -> None:
        if address not in STUB_NAMES:
            return
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        if address == STUB_269CB8:
            self.call_log.append(("269cb8",))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["delta_frame"])
        elif address == STUB_HANDLER:
            self.call_log.append(("handler", r0))

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)

        # Globals
        self.uc.mem_write(0x00472550, struct.pack("<4f", 0.0, 0.0, 0.0, 1.0))
        self.uc.mem_write(0x00472718 + case["owner_type"] * 24 + 0x0C, struct.pack("<I", STUB_HANDLER))
        self.uc.mem_write(0x004EA91C, b"\x00" * 0x30)

        self.uc.mem_write(MEM_ADDR, b"\x00" * MEM_SIZE)
        # Layout inside MEM_ADDR:
        # +0x0000: self
        # +0x0100: desc
        # +0x0200: weights
        # +0x0300: owner
        # +0x0400: target
        # +0x0500: state
        # +0x0600: holder
        # +0x0700: first
        # +0x0800: target_data
        # +0x0900: in_table
        # +0x1000: dst_buf
        # +0x2000: src_buf (offset +0x100 so negative src[-9] is safe)
        self_p = MEM_ADDR + 0x0000
        desc_p = MEM_ADDR + 0x0100
        weights_p = MEM_ADDR + 0x0200
        owner_p = MEM_ADDR + 0x0300
        target_p = MEM_ADDR + 0x0400
        state_p = MEM_ADDR + 0x0500
        holder_p = MEM_ADDR + 0x0600
        first_p = MEM_ADDR + 0x0700
        target_data_p = MEM_ADDR + 0x0800
        in_table_p = MEM_ADDR + 0x0900
        dst_p = MEM_ADDR + 0x1000
        src_p = MEM_ADDR + 0x2100

        self.uc.mem_write(self_p + 0x34, struct.pack("<i", case["frame"]))
        self.uc.mem_write(self_p + 0x3C, struct.pack("<II", desc_p, state_p))

        self.uc.mem_write(desc_p + 0x00, struct.pack("<III", weights_p, owner_p, target_p))
        self.uc.mem_write(weights_p, struct.pack("<4f", *case["weights"]))

        self.uc.mem_write(owner_p + 0x34, struct.pack("<III", 10, case["owner_type"], holder_p))
        self.uc.mem_write(holder_p, struct.pack("<I", first_p))

        self.uc.mem_write(first_p + 0x02, struct.pack("<h", case["joint_count"]))
        self.uc.mem_write(first_p + 0x08, struct.pack("<I", in_table_p))
        self.uc.mem_write(first_p + 0x54, struct.pack("<I", 0))

        self.uc.mem_write(target_p + 0x08, struct.pack("<I", target_data_p))
        self.uc.mem_write(target_p + 0x54, struct.pack("<I", 0))
        self.uc.mem_write(target_data_p + 0x30, struct.pack("<I", dst_p))

        self.uc.mem_write(in_table_p + 0x30, struct.pack("<I", src_p))

        self.uc.mem_write(state_p + 0x34, struct.pack("<iI", case["total"], case["joint_total"]))
        self.uc.mem_write(state_p + 0xC4, struct.pack("<B", case["state_c4"]))

        # Populate src_p[-0x40..+0x200] with distinct floats
        for k in range(-16, 64):
            val = float(k + 20) * (1.0 if k % 2 == 0 else -0.5)
            self.uc.mem_write(src_p + k * 4, struct.pack("<f", val))
        if case["zero_diff"]:
            # Make src[3..5] == src[9..11] for joint 0 so length == 0.0f
            for idx in range(3):
                self.uc.mem_write(src_p + (3 + idx) * 4, struct.pack("<f", 5.0))
                self.uc.mem_write(src_p + (9 + idx) * 4, struct.pack("<f", 5.0))

        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_R0, self_p)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "call_log": list(self.call_log),
            "mem": bytes(self.uc.mem_read(MEM_ADDR, MEM_SIZE)),
            "g_bufs": bytes(self.uc.mem_read(0x004EA91C, 0x30)),
            "g_scratch": bytes(self.uc.mem_read(0x00472550, 16)),
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "frame": 3,
        "total": 10,
        "owner_type": 2,
        "delta_frame": 1,
        "joint_count": 4,
        "joint_total": 3,
        "state_c4": 0,
        "weights": (0.5, 0.75, 1.0, 0.25),
        "zero_diff": False,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="early_exit_frame_gt_total", frame=11, total=10),
        base_case(name="total_zero_runs_loop_skipped", frame=5, total=0, joint_total=0),
        base_case(name="state_c4_nonzero_skips_loop", state_c4=1),
        base_case(name="three_joints_normal"),
        base_case(name="joint0_zero_diff_length0", zero_diff=True, joint_total=2),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "call_log", "mem", "g_bufs", "g_scratch"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code = compile_candidate_baseline()
    print(f"func_002f9914: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner().run(cand_code, case)
        diffs = compare_results(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{case['name']}]: {diffs}")
            print("  orig log:", orig_res["call_log"])
            print("  cand log:", cand_res["call_log"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("handler_slot", "owner_type * 6 + 3", "owner_type * 6 + 2"),
        ("flag4_target", "*reinterpret_cast<u32*>(target + 0x54) |= 4u;", "*reinterpret_cast<u32*>(target + 0x54) |= 8u;"),
        ("flag4_again", "*reinterpret_cast<u32*>(again + 0x54) |= 4u;", "*reinterpret_cast<u32*>(again + 0x54) |= 8u;"),
        ("last_rest_off", "src + joint_count_m1 * 3 - 18", "src + joint_count_m1 * 3 - 15"),
        ("c4_gate", "state[0xC4] != 0", "state[0xC5] != 0"),
    ]
    for name, old, new in mutants:
        m_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, case)
            try:
                bad_res = Runner().run(m_code, case)
            except unicorn.UcError:
                detected = True
                break
            if compare_results(orig_res, bad_res):
                detected = True
                break
        if not detected:
            print(f"FAIL [mutant {name}]: not detected!")
            return 1
        print(f"PASS [mutant {name} detected]")

    print(f"ALL PASS: {len(cases)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
