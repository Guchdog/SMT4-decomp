#!/usr/bin/env python3
"""Differential test for PlaceWin_Calc (0x00263bb4) with Unicorn ARM.

Compiles src/ui/window.cpp, extracts PlaceWin_Calc, resolves its direct calls
and function-pointer symbols against the pinned target addresses, and runs
the pinned original (extracted/exefs/code.bin) against the candidate in
separate Unicorn machines.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11 and d8;
  * ordered call log (stub address, r0, r1, s0_bits, s1_bits, s2_bits, s3_bits);
  * work (+0x00..+0x570) and sub objects (+0x00..+0x60);
  * unexpected writes outside work, sub objects, and stack.
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
SOURCE = ROOT / "src" / "ui" / "window.cpp"
OUT_DIR = ROOT / "build" / "test_leaf_00263bb4"

FUNC_ADDR = 0x00263BB4
FUNC_SIZE = 660

STUB_29C56C = 0x0029C56C
STUB_2A06DC = 0x002A06DC
STUB_2A58EC = 0x002A58EC
STUB_2C2BE8 = 0x002C2BE8
STUB_2D5780 = 0x002D5780
STUB_2E11BC = 0x002E11BC
STUB_VTABLE_20 = 0x003F0100
STUB_BLEND_FN = 0x003F0200

FUNC_00151404 = 0x00151404
FUNC_0015555C = 0x0015555C

STUB_NAMES = {
    STUB_29C56C: "camp_func_0029c56c",
    STUB_2A06DC: "camp_func_002a06dc",
    STUB_2A58EC: "engine_func_002a58ec",
    STUB_2C2BE8: "engine_func_002c2be8",
    STUB_2D5780: "script_vm_func_002d5780",
    STUB_2E11BC: "script_vm_func_002e11bc",
    STUB_VTABLE_20: "vtable_20",
    STUB_BLEND_FN: "blend_fn",
}

PTR_WORK = 0x20000000
WORK_SIZE = 0x600
PTR_SLOTS_BASE = 0x20010000
PTR_VTABLE = 0x20020000
PTR_POS_SLOT = 0x20021000
PTR_POS_TARGET = 0x20022000
PTR_SCALE_SLOT = 0x20023000
PTR_SCALE_TARGET = 0x20024000
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
        if "PlaceWin_Calc" in name and "Draft" not in name and "0032ac30" not in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"PlaceWin_Calc not found in {obj_file}: {sorted(funcs)}")

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
            if "func_00151404" in rel.symbol_name:
                target = FUNC_00151404 + addend
            elif "func_0015555c" in rel.symbol_name:
                target = FUNC_0015555C + addend
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
    obj_file = OUT_DIR / "window.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"Mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"window_mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"window_mutant_{name}.o"
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
        self, code: bytes, prev_mode: int, mode: int, slot560: int = 1
    ) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x2000)
        uc.mem_write(FUNC_ADDR, code)

        # Load PlaceWin_SetPos and PlaceWin_SetScale from code.bin for orig calls
        with open(ORIG_BIN, "rb") as handle:
            handle.seek(0x0026385C - 0x00100000)
            uc.mem_write(0x0026385C, handle.read(128))

        uc.mem_write(0x004D9880 + 0x264, struct.pack("<I", PTR_POS_SLOT))
        uc.mem_write(0x004D9D88 + 0x264, struct.pack("<I", PTR_SCALE_SLOT))
        uc.mem_write(PTR_POS_SLOT, b"\x00" * 0x20)
        uc.mem_write(PTR_POS_SLOT + 8, struct.pack("<I", PTR_POS_TARGET))
        uc.mem_write(PTR_SCALE_SLOT, b"\x00" * 0x20)
        uc.mem_write(PTR_SCALE_SLOT + 8, struct.pack("<I", PTR_SCALE_TARGET))
        uc.mem_write(PTR_POS_TARGET, b"\x00" * 0x120)
        uc.mem_write(PTR_SCALE_TARGET, b"\x00" * 0x120)

        uc.mem_write(PTR_WORK, b"\x00" * WORK_SIZE)
        uc.mem_write(PTR_SLOTS_BASE, b"\x00" * 0x2000)
        uc.mem_write(PTR_VTABLE, b"\x00" * 0x100)
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        # Vtable slot +0x20
        uc.mem_write(PTR_VTABLE + 0x20, struct.pack("<I", STUB_VTABLE_20))

        # Populate work+0x34[0..1] (for slot560) and work+0x3C[0..4] (for mode)
        for idx in range(2):
            obj34 = PTR_SLOTS_BASE + idx * 0x100
            uc.mem_write(PTR_WORK + 0x34 + idx * 4, struct.pack("<I", obj34))
        sub_addrs: list[int] = []
        for idx in range(5):
            obj3c = PTR_SLOTS_BASE + 0x800 + idx * 0x100
            sub = PTR_SLOTS_BASE + 0x1000 + idx * 0x100
            sub_addrs.append(sub)
            uc.mem_write(PTR_WORK + 0x3C + idx * 4, struct.pack("<I", obj3c))
            uc.mem_write(obj3c + 0x04, struct.pack("<I", sub))
            uc.mem_write(sub + 0x00, struct.pack("<I", PTR_VTABLE))
            uc.mem_write(sub + 0x38, struct.pack("<f", 0.25 + idx * 0.1))
            uc.mem_write(sub + 0x44, struct.pack("<ff", 1.25 + idx, 2.5 + idx))
            uc.mem_write(sub + 0x4C, struct.pack("<II", STUB_BLEND_FN, 0x3000 + idx))

        uc.mem_write(PTR_WORK + 0x550, struct.pack("<i", prev_mode))
        uc.mem_write(PTR_WORK + 0x560, struct.pack("<i", slot560))

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            uc.mem_write(addr, bx_lr)
        uc.mem_write(LR_SENTINEL & ~1, bx_lr)

        calls: list[tuple[int, int, int, int, int, int, int]] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            s0 = emu.reg_read(arm.UC_ARM_REG_S0)
            s1 = emu.reg_read(arm.UC_ARM_REG_S1)
            s2 = emu.reg_read(arm.UC_ARM_REG_S2)
            s3 = emu.reg_read(arm.UC_ARM_REG_S3)
            # For engine_func_002c2be8(floats), record the 4 float values instead of stack ptr
            if addr == STUB_2C2BE8:
                vals = struct.unpack("<IIII", emu.mem_read(r0, 16))
                calls.append((addr, 0, 0, vals[0], vals[1], vals[2], vals[3]))
                emu.reg_write(arm.UC_ARM_REG_R0, 0x12345678)
                return
            calls.append((addr, r0, r1, s0, s1, s2, s3))
            if addr == STUB_BLEND_FN:
                res = bits_f32(s0) + bits_f32(s1) * 2.0
                emu.reg_write(arm.UC_ARM_REG_S0, f32_bits(res))

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if PTR_WORK <= addr < PTR_WORK + WORK_SIZE:
                return
            if PTR_SLOTS_BASE <= addr < PTR_SLOTS_BASE + 0x2000:
                return
            if PTR_POS_TARGET <= addr < PTR_POS_TARGET + 0x120:
                return
            if PTR_SCALE_TARGET <= addr < PTR_SCALE_TARGET + 0x120:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_WORK)
        uc.reg_write(arm.UC_ARM_REG_R1, mode)
        uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=2_000_000, count=5000)
        for hook in hooks:
            uc.hook_del(hook)

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
            "work": bytes(uc.mem_read(PTR_WORK, WORK_SIZE)),
            "subs": [bytes(uc.mem_read(s, 0x60)) for s in sub_addrs],
            "pos_target": bytes(uc.mem_read(PTR_POS_TARGET, 0x120)),
            "scale_target": bytes(uc.mem_read(PTR_SCALE_TARGET, 0x120)),
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
        diffs.append(f"calls mismatch (orig {len(orig['calls'])} vs cand {len(cand['calls'])})")
    if orig["work"] != cand["work"]:
        diffs.append("work memory mismatch")
    if orig["subs"] != cand["subs"]:
        diffs.append("sub object memory mismatch")
    if orig["pos_target"] != cand["pos_target"]:
        diffs.append("pos_target memory mismatch")
    if orig["scale_target"] != cand["scale_target"]:
        diffs.append("scale_target memory mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [
        ("same_mode", 1, 1),
        ("init_mode0", -1, 0),
        ("0_to_1", 0, 1),
        ("1_to_2", 1, 2),
        ("2_to_3", 2, 3),
    ]
    for label, prev_mode, mode in cases:
        orig_res = Runner().run(orig_bytes, prev_mode, mode)
        cand_res = Runner().run(cand_bytes, prev_mode, mode)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("drop_early_ret", "if (prev_mode == mode) {\n        return;\n    }", "if (false) {\n        return;\n    }"),
        ("skip_prev_cleanup", "if (prev_mode != -1)", "if (false)"),
        ("wrong_mode2_flag", "mode == 2 ? 1 : 0", "0"),
        ("wrong_mode1_cb", "reinterpret_cast<void*>(&func_0015555c)", "reinterpret_cast<void*>(&func_00151404)"),
        ("wrong_focus_scale", "kFocusScale = 0.6f;", "kFocusScale = 0.5f;"),
        ("drop_blend_store", "*reinterpret_cast<f32*>(cur_sub + 0x38) = blend_res;", "*reinterpret_cast<f32*>(cur_sub + 0x38) = 0.0f;"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, prev_mode, mode in cases:
            if compare(Runner().run(orig_bytes, prev_mode, mode), Runner().run(mut_bytes, prev_mode, mode)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: PlaceWin_Calc (0x00263bb4) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
