#!/usr/bin/env python3
"""Differential test for Status_Destroy (0x00289158) with Unicorn ARM.

Compiles src/ui/status.cpp, extracts Status_Destroy, resolves its calls and
globals against the pinned target addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11 and d8;
  * ordered call log (stub address, r0, s0_bits);
  * *out_x and *out_y values;
  * unexpected writes outside out_x, out_y, and stack.
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

ORIG_BIN = ROOT / "extracted" / "exefs" / "code.bin"
SOURCE = ROOT / "src" / "ui" / "status.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00289158"

FUNC_ADDR = 0x00289158
FUNC_SIZE = 112

G_STATUS_MANAGER_ADDR = 0x0044E140
G_ASD_GPU_STATE_ADDR = 0x0044EA00

STUB_GET_POS_X = 0x002BEF7C
STUB_TRANSFORM_COORD = 0x002BA46C
STUB_GET_POS_Y = 0x002BEF70

STUB_NAMES = {
    STUB_GET_POS_X: "UiAnimSprite_GetPosX",
    STUB_TRANSFORM_COORD: "UiGpu_TransformCoord",
    STUB_GET_POS_Y: "UiAnimSprite_GetPosY",
}

PTR_WORK = 0x20000000
WORK_SIZE = 0x1EBC
PTR_GPU_STATE = 0x20010000
PTR_OUT_X = 0x20020000
PTR_OUT_Y = 0x20020010
STACK_BASE = 0x7F000000
STACK_SIZE = 0x10000
STACK_INIT = STACK_BASE + STACK_SIZE - 0x200
LR_SENTINEL = 0x90000000

CALLEE_SAVED = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


def f32_bits(val: float) -> int:
    return struct.unpack("<I", struct.pack("<f", val))[0]


def bits_f32(bits: int) -> float:
    return struct.unpack("<f", struct.pack("<I", bits & 0xFFFFFFFF))[0]


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def _stub_address(symbol_name: str) -> int | None:
    for addr, name in STUB_NAMES.items():
        if name in symbol_name:
            return addr
    return None


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "Status_Destroy" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"Status_Destroy not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = _stub_address(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if "g_StatusManager" in rel.symbol_name:
                target = G_STATUS_MANAGER_ADDR + addend
            elif "g_AsdGpuState" in rel.symbol_name:
                target = G_ASD_GPU_STATE_ADDR + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {rel.symbol_name!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "status.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"status_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"status_mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant {name} compilation failed: {result.stderr}")
    return relocate_candidate(mutant_obj)


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0x00100000, 0x00400000)
        self.uc.mem_map(PTR_WORK, 0x30000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(
        self, code: bytes, panel_idx: int, scale: float
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x2000)
        uc.mem_write(FUNC_ADDR, code)

        # Populate g_StatusManager.work and g_AsdGpuState
        uc.mem_write(G_STATUS_MANAGER_ADDR, struct.pack("<II", 1, PTR_WORK))
        uc.mem_write(G_ASD_GPU_STATE_ADDR, struct.pack("<I", PTR_GPU_STATE))

        uc.mem_write(PTR_WORK, b"\x00" * WORK_SIZE)
        uc.mem_write(PTR_OUT_X, struct.pack("<i", -123456))
        uc.mem_write(PTR_OUT_Y, struct.pack("<i", -654321))
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        # Stubs: bx lr
        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            uc.mem_write(addr, bx_lr)
        uc.mem_write(LR_SENTINEL & ~1, bx_lr)

        calls: list[tuple[int, int, int]] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            s0_bits = emu.reg_read(arm.UC_ARM_REG_S0)
            calls.append((addr, r0, s0_bits))
            if addr == STUB_GET_POS_X:
                emu.reg_write(arm.UC_ARM_REG_R0, (r0 - PTR_WORK) + 17)
            elif addr == STUB_TRANSFORM_COORD:
                val = bits_f32(s0_bits) * 10.5
                emu.reg_write(arm.UC_ARM_REG_S0, f32_bits(val))
            elif addr == STUB_GET_POS_Y:
                emu.reg_write(arm.UC_ARM_REG_R0, (r0 - PTR_WORK) + 42)

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if addr in (PTR_OUT_X, PTR_OUT_Y) and size == 4:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_OUT_X)
        uc.reg_write(arm.UC_ARM_REG_R1, PTR_OUT_Y)
        uc.reg_write(arm.UC_ARM_REG_R2, panel_idx)
        uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(scale))
        uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=2_000_000, count=2000)
        for hook in hooks:
            uc.hook_del(hook)

        out_x = struct.unpack("<i", uc.mem_read(PTR_OUT_X, 4))[0]
        out_y = struct.unpack("<i", uc.mem_read(PTR_OUT_Y, 4))[0]
        callee = {
            name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{name.upper()}"))
            for name in CALLEE_SAVED
        }
        callee["d8"] = uc.reg_read(arm.UC_ARM_REG_D8)
        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "out_x": out_x,
            "out_y": out_y,
            "bad_writes": bad_writes,
        }


def compare(orig: dict[str, object], cand: dict[str, object]) -> list[str]:
    diffs: list[str] = []
    if orig["pc"] != cand["pc"]:
        diffs.append(f"pc: orig={orig['pc']:#x} cand={cand['pc']:#x}")
    if orig["sp"] != cand["sp"]:
        diffs.append(f"sp: orig={orig['sp']:#x} cand={cand['sp']:#x}")
    if orig["callee"] != cand["callee"]:
        diffs.append("callee-saved register mismatch")
    if orig["calls"] != cand["calls"]:
        diffs.append(f"calls: orig={orig['calls']} cand={cand['calls']}")
    if orig["out_x"] != cand["out_x"]:
        diffs.append(f"out_x: orig={orig['out_x']} cand={cand['out_x']}")
    if orig["out_y"] != cand["out_y"]:
        diffs.append(f"out_y: orig={orig['out_y']} cand={cand['out_y']}")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("idx0_pos", 0, 1.5),
        ("idx3_neg", 3, -2.25),
        ("idx7_zero", 7, 0.0),
    ]
    for label, panel_idx, scale in cases:
        orig_res = Runner().run(orig_bytes, panel_idx, scale)
        cand_res = Runner().run(cand_bytes, panel_idx, scale)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_stride", "panel_idx * 0x8C", "panel_idx * 0x88"),
        ("wrong_base", "(0x44 - 0x18)", "(0x48 - 0x18)"),
        ("drop_pos_x", "static_cast<s32>(offset_x) + pos_x", "static_cast<s32>(offset_x)"),
        ("wrong_out_y", "*out_y = UiAnimSprite_GetPosY(sprite);", "*out_y = pos_x;"),
        ("zero_scale", "UiGpu_TransformCoord(g_AsdGpuState, scale)", "UiGpu_TransformCoord(g_AsdGpuState, 0.0f)"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, panel_idx, scale in cases:
            if compare(Runner().run(orig_bytes, panel_idx, scale), Runner().run(mut_bytes, panel_idx, scale)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: Status_Destroy (0x00289158) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
