#!/usr/bin/env python3
"""Differential test for StatusCamera_Init (0x00258e38) with Unicorn ARM.

Compiles src/ui/status.cpp, extracts StatusCamera_Init, resolves g_StatusCamera
and direct calls, and compares the pinned original (extracted/exefs/code.bin)
against the candidate in Unicorn.
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
OUT_DIR = ROOT / "build" / "test_leaf_00258e38"

FUNC_ADDR = 0x00258E38
FUNC_SIZE = 480

G_CAM_ADDR = 0x0044E178

STUB_ALLOC = 0x002C4B84
STUB_ZERO = 0x002C4B30
STUB_2BC828 = 0x002BC828
STUB_2C2210 = 0x002C2210
STUB_2C20A8 = 0x002C20A8
STUB_2C1FFC = 0x002C1FFC
STUB_298FEC = 0x00298FEC
STUB_2C1740 = 0x002C1740
STUB_2C1774 = 0x002C1774

STUB_NAMES = {
    STUB_ALLOC: "AsdMem_Alloc",
    STUB_ZERO: "AsdMem_Zero",
    STUB_2BC828: "engine_func_002bc828",
    STUB_2C2210: "engine_func_002c2210",
    STUB_2C20A8: "engine_func_002c20a8",
    STUB_2C1FFC: "ui_func_002c1ffc",
    STUB_298FEC: "ui_func_00298fec",
    STUB_2C1740: "battle_func_002c1740",
    STUB_2C1774: "ui_func_002c1774",
}

PTR_CAM = 0x20000000
CAM_SIZE = 0x53C
PTR_POS = 0x20010000
PTR_TARGET = 0x20010020
PTR_UP = 0x20010040
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
        if "StatusCamera_Init" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"StatusCamera_Init not found in {obj_file}")

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
            if "g_StatusCamera" in rel.symbol_name:
                target = G_CAM_ADDR + addend
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
        self.uc.mem_map(PTR_CAM, 0x20000)
        self.uc.mem_map(STACK_BASE, STACK_SIZE)
        self.uc.mem_map(LR_SENTINEL, 0x1000)

    def run(self, code: bytes, cam_ptr: int) -> dict[str, object]:
        uc = self.uc
        uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        uc.mem_write(FUNC_ADDR, code)

        uc.mem_write(G_CAM_ADDR, struct.pack("<I", cam_ptr))
        uc.mem_write(PTR_CAM, b"\xAA" * CAM_SIZE)
        uc.mem_write(PTR_POS, struct.pack("<fff", 1.5, -2.0, 3.25))
        uc.mem_write(PTR_TARGET, struct.pack("<fff", 0.25, 0.5, -0.75))
        uc.mem_write(PTR_UP, struct.pack("<fff", 0.0, 1.0, 0.5))
        uc.mem_write(STACK_BASE, b"\x00" * STACK_SIZE)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            uc.mem_write(addr, bx_lr)
        uc.mem_write(LR_SENTINEL, bx_lr)

        calls: list[tuple[object, ...]] = []
        bad_writes: list[tuple[int, int, int]] = []

        def on_stub(emu: unicorn.Uc, addr: int, _size: int, _user: object) -> None:
            r0 = emu.reg_read(arm.UC_ARM_REG_R0)
            r1 = emu.reg_read(arm.UC_ARM_REG_R1)
            r2 = emu.reg_read(arm.UC_ARM_REG_R2)
            r3 = emu.reg_read(arm.UC_ARM_REG_R3)
            sp = emu.reg_read(arm.UC_ARM_REG_SP)
            if addr == STUB_ALLOC:
                sp0 = struct.unpack("<I", emu.mem_read(sp, 4))[0]
                calls.append((addr, r0, r1, r2, r3, sp0))
                emu.reg_write(arm.UC_ARM_REG_R0, PTR_CAM)
            elif addr == STUB_ZERO:
                calls.append((addr, r0, r1))
                emu.mem_write(r0, b"\x00" * r1)
            elif addr == STUB_2BC828:
                calls.append((addr, r0, r1, r2, r3))
            elif addr == STUB_2C2210:
                calls.append((addr, r0, r1))
            elif addr == STUB_2C20A8:
                pos_v = struct.unpack("<III", emu.mem_read(r1, 12))
                look_v = struct.unpack("<III", emu.mem_read(r2, 12))
                up_v = struct.unpack("<III", emu.mem_read(r3, 12))
                calls.append((addr, r0, pos_v, look_v, up_v))
            elif addr == STUB_2C1FFC:
                s0 = emu.reg_read(arm.UC_ARM_REG_S0)
                s1 = emu.reg_read(arm.UC_ARM_REG_S1)
                s2 = emu.reg_read(arm.UC_ARM_REG_S2)
                s3 = emu.reg_read(arm.UC_ARM_REG_S3)
                calls.append((addr, r0, r1, s0, s1, s2, s3))
            elif addr in (STUB_298FEC, STUB_2C1740):
                calls.append((addr, r0))
            elif addr == STUB_2C1774:
                s0 = emu.reg_read(arm.UC_ARM_REG_S0)
                s1 = emu.reg_read(arm.UC_ARM_REG_S1)
                calls.append((addr, r0, s0, s1))

        def on_write(
            _emu: unicorn.Uc, _access: int, addr: int, size: int, value: int, _user: object
        ) -> None:
            if G_CAM_ADDR <= addr < G_CAM_ADDR + 4:
                return
            if PTR_CAM <= addr < PTR_CAM + CAM_SIZE:
                return
            if STACK_BASE <= addr < STACK_BASE + STACK_SIZE:
                return
            bad_writes.append((addr, size, value))

        hooks = [
            uc.hook_add(unicorn.UC_HOOK_CODE, on_stub, None, addr, addr)
            for addr in STUB_NAMES
        ]
        hooks.append(uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write))

        uc.reg_write(arm.UC_ARM_REG_R0, PTR_POS)
        uc.reg_write(arm.UC_ARM_REG_R1, PTR_TARGET)
        uc.reg_write(arm.UC_ARM_REG_R2, PTR_UP)
        uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(45.0))
        uc.reg_write(arm.UC_ARM_REG_S1, f32_bits(1.25))
        uc.reg_write(arm.UC_ARM_REG_S2, f32_bits(0.5))
        uc.reg_write(arm.UC_ARM_REG_S3, f32_bits(100.0))
        uc.reg_write(arm.UC_ARM_REG_S4, f32_bits(2.5))
        uc.reg_write(arm.UC_ARM_REG_D8, 0x1122334455667788)
        uc.reg_write(arm.UC_ARM_REG_D9, 0x2233445566778899)
        uc.reg_write(arm.UC_ARM_REG_D10, 0x33445566778899AA)
        uc.reg_write(arm.UC_ARM_REG_SP, STACK_INIT)
        uc.reg_write(arm.UC_ARM_REG_LR, LR_SENTINEL)
        for reg_name, val in CALLEE_SAVED.items():
            uc.reg_write(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"), val)

        uc.emu_start(FUNC_ADDR, LR_SENTINEL, timeout=1_000_000, count=2000)
        for hook in hooks:
            uc.hook_del(hook)

        callee = {
            name: uc.reg_read(getattr(arm, f"UC_ARM_REG_{reg_name.upper()}"))
            for name, reg_name in zip(CALLEE_SAVED, CALLEE_SAVED)
        }
        callee["d8"] = uc.reg_read(arm.UC_ARM_REG_D8)
        callee["d9"] = uc.reg_read(arm.UC_ARM_REG_D9)
        callee["d10"] = uc.reg_read(arm.UC_ARM_REG_D10)
        return {
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": callee,
            "calls": calls,
            "g_cam": struct.unpack("<I", uc.mem_read(G_CAM_ADDR, 4))[0],
            "cam": bytes(uc.mem_read(PTR_CAM, CAM_SIZE)),
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
    if orig["g_cam"] != cand["g_cam"]:
        diffs.append(f"g_cam: orig={orig['g_cam']:#x} cand={cand['g_cam']:#x}")
    if orig["cam"] != cand["cam"]:
        diffs.append("cam memory mismatch")
    if cand["bad_writes"]:
        diffs.append(f"unexpected writes: {cand['bad_writes'][:4]}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes = compile_candidate()
    cases = [("null_cam", 0), ("existing_cam", PTR_CAM)]
    for label, cam_ptr in cases:
        orig_res = Runner().run(orig_bytes, cam_ptr)
        cand_res = Runner().run(cand_bytes, cam_ptr)
        diffs = compare(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{label}]: " + "; ".join(diffs))
            return 1

    mutants = [
        ("wrong_ratio", "kDefaultRatio = 5.0f / 3.0f;", "kDefaultRatio = 2.0f;"),
        ("drop_zero", "AsdMem_Zero(cam, sizeof(StatusCameraWork));", ""),
        ("wrong_look_z", "target_dst[0] * far_z,", "target_dst[0] * near_z,"),
        ("wrong_up_axis", "up_axis[3] = {0.0f, 1.0f, 0.0f};", "up_axis[3] = {0.0f, 0.0f, 1.0f};"),
        ("wrong_rect_h", "engine_func_002bc828(0xC8, 0, 0xC8, 0xF0);", "engine_func_002bc828(0xC8, 0, 0xC8, 0xE0);"),
    ]
    detected = 0
    for name, old, new in mutants:
        mut_bytes = compile_candidate_mutant(name, old, new)
        any_diff = False
        for _label, cam_ptr in cases:
            if compare(Runner().run(orig_bytes, cam_ptr), Runner().run(mut_bytes, cam_ptr)):
                any_diff = True
                break
        if not any_diff:
            print(f"FAIL: mutant {name} was not detected")
            return 1
        detected += 1

    print(
        f"PASS: StatusCamera_Init (0x00258e38) matched original across "
        f"{len(cases)} cases and detected {detected}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
