#!/usr/bin/env python3
"""Differential test for EffectProcess_func_002217d8 (0x002217d8) with Unicorn ARM.

Compiles src/battle/battle_extras.cpp, extracts EffectProcess_func_002217d8,
resolves its direct calls and literal-pool relocations against the pinned
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0 (calc_task), continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log including VFP arguments (s0..s3) for engine_func_002c1774
    and engine_func_002c1ffc, vector contents for engine_func_002c20a8, and
    stack arguments + task-name strings for engine_func_002c5978 and
    camp_func_002c4c00;
  * g_EffectProcessWork_00433260 (0x00433260) and work (+0x000..+0x534);
  * unexpected writes outside g_EffectProcessWork_00433260, work, and stack.

Coverage:
  * mode == 0 (calls battle_func_00317bd8, creates EffectDrawUp3D + EffectDrawDown2D);
  * mode == 1 and mode == 0xFF (skips battle_func_00317bd8, creates EffectDrawDown2D
    with tag 0x84);
  * negative/mutation controls on kWorkSize, kFarZ, kNearZ, kDrawUp3dTag,
    kDrawDown2dAltTag, and `if (work[0x530] != 0)`.
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
SOURCE = ROOT / "src/battle/battle_extras.cpp"
OUT_DIR = ROOT / "build/test_leaf_002217d8"

FUNC_ADDR = 0x002217D8
FUNC_SIZE = 648

CODE_ADDR = 0x00200000
CODE_SIZE = 0x00140000  # covers 0x002009AC..0x0032FFA8
GLOBALS_PAGE = 0x00433000
PTR_WORK = 0x00433260
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00001000
RODATA_ADDR = 0x00700000
PAGE_SIZE = 0x00001000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2C4B84 = 0x002C4B84
STUB_2C4B30 = 0x002C4B30
STUB_32FFA8 = 0x0032FFA8
STUB_2009AC = 0x002009AC
STUB_317BD8 = 0x00317BD8
STUB_221AB0 = 0x00221AB0
STUB_2C2210 = 0x002C2210
STUB_2C1774 = 0x002C1774
STUB_2C20A8 = 0x002C20A8
STUB_2C1FFC = 0x002C1FFC
STUB_2C5978 = 0x002C5978
STUB_2C4C00 = 0x002C4C00

FN_17FAE4 = 0x0017FAE4
FN_1DC8C8 = 0x001DC8C8
FN_1AA19C = 0x001AA19C
FN_1AA3A4 = 0x001AA3A4
FN_1DC954 = 0x001DC954

STUB_NAMES = {
    STUB_2C4B84: "engine_func_002c4b84",
    STUB_2C4B30: "engine_func_002c4b30",
    STUB_32FFA8: "battle_func_0032ffa8",
    STUB_2009AC: "battle_func_002009ac",
    STUB_317BD8: "battle_func_00317bd8",
    STUB_221AB0: "battle_func_00221ab0",
    STUB_2C2210: "engine_func_002c2210",
    STUB_2C1774: "engine_func_002c1774",
    STUB_2C20A8: "engine_func_002c20a8",
    STUB_2C1FFC: "engine_func_002c1ffc",
    STUB_2C5978: "engine_func_002c5978",
    STUB_2C4C00: "camp_func_002c4c00",
}

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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def elf_rodata(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + index * e_shentsize)
        for index in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        if name.startswith(".rodata"):
            result[name] = data[section[4] : section[4] + section[5]]
    return result


def _stub_address(symbol_name: str) -> int | None:
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "EffectProcess_func_002217d8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"EffectProcess_func_002217d8 not found in {obj_file}: {sorted(funcs)}"
        )

    rodata_sections = elf_rodata(obj_file)
    rodata_blobs: dict[int, bytes] = {}
    rodata_bases: dict[str, int] = {}
    cursor = RODATA_ADDR
    for sec_name, blob in sorted(rodata_sections.items()):
        if blob:
            rodata_bases[sec_name] = cursor
            rodata_blobs[cursor] = blob
            cursor += (len(blob) + 0xFF) & ~0xFF

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
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            sym = rel.symbol_name
            if "g_EffectProcessWork_00433260" in sym:
                target = PTR_WORK + addend
            elif "0017fae4" in sym:
                target = FN_17FAE4 + addend
            elif "001dc8c8" in sym:
                target = FN_1DC8C8 + addend
            elif "001aa19c" in sym:
                target = FN_1AA19C + addend
            elif "001aa3a4" in sym:
                target = FN_1AA3A4 + addend
            elif "001dc954" in sym:
                target = FN_1DC954 + addend
            elif sym in rodata_bases:
                target = rodata_bases[sym] + addend
            elif ".rodata" in sym or sym == "":
                base = rodata_bases.get(".rodata.str1.1") or next(iter(rodata_bases.values()))
                target = base + addend
            else:
                raise RuntimeError(f"unresolved ABS32 relocation: {sym!r}")
            struct.pack_into("<I", code, rel.offset, target)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    return bytes(code), rodata_blobs


def compile_candidate() -> tuple[bytes, dict[int, bytes]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "battle_extras.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(
    name: str, old: str, new: str
) -> tuple[bytes, dict[int, bytes]]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


class Runner:
    """One Unicorn machine with deterministic stubs for EffectProcess_func_002217d8."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(
            arm.UC_ARM_REG_C1_C0_2,
            self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2) | 0x00F00000,
        )
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE, PAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, bx_lr)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE320F000))

        self.task_seq = 0
        self.call_log: list[tuple] = []
        self.bad_writes: list[tuple[int, int, int]] = []

        for addr in STUB_NAMES:
            self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_stub, None, addr, addr)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _read_cstr(self, addr: int) -> bytes:
        raw = self.uc.mem_read(addr, 64)
        end = raw.find(b"\x00")
        return bytes(raw[:end] if end != -1 else raw)

    def _on_stub(
        self, uc: unicorn.Uc, address: int, size: int, user_data: object
    ) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)

        if address == STUB_2C4B84:
            stack_args = struct.unpack("<1I", self.uc.mem_read(sp, 4))
            self.call_log.append((address, r0, r1, r2, r3, stack_args))
            uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        elif address == STUB_2C4B30:
            self.call_log.append((address, r0, r1))
            self.uc.mem_write(r0, b"\x00" * r1)
        elif address in (STUB_32FFA8, STUB_221AB0):
            self.call_log.append((address,))
        elif address in (STUB_2009AC, STUB_317BD8):
            self.call_log.append((address, r0))
        elif address == STUB_2C2210:
            self.call_log.append((address, r0, r1))
        elif address == STUB_2C1774:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc.reg_read(arm.UC_ARM_REG_S1)
            self.call_log.append((address, r0, s0, s1))
        elif address == STUB_2C20A8:
            v1 = struct.unpack("<3f", self.uc.mem_read(r1, 12))
            v2 = struct.unpack("<3f", self.uc.mem_read(r2, 12))
            v3 = struct.unpack("<3f", self.uc.mem_read(r3, 12))
            self.call_log.append((address, r0, v1, v2, v3))
        elif address == STUB_2C1FFC:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc.reg_read(arm.UC_ARM_REG_S1)
            s2 = uc.reg_read(arm.UC_ARM_REG_S2)
            s3 = uc.reg_read(arm.UC_ARM_REG_S3)
            self.call_log.append((address, r0, r1, s0, s1, s2, s3))
        elif address == STUB_2C5978:
            stack_args = struct.unpack("<3I", self.uc.mem_read(sp, 12))
            self.call_log.append(
                (address, self._read_cstr(r0), r1, r2, r3, stack_args)
            )
            self.task_seq += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x00600000 + self.task_seq * 0x100)
        elif address == STUB_2C4C00:
            stack_args = struct.unpack("<4I", self.uc.mem_read(sp, 16))
            self.call_log.append(
                (address, self._read_cstr(r0), r1, r2, r3, stack_args)
            )
            self.task_seq += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x00600000 + self.task_seq * 0x100)

    def _on_write(
        self,
        uc: unicorn.Uc,
        access: int,
        address: int,
        size: int,
        value: int,
        user_data: object,
    ) -> None:
        allowed = (
            (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            or (PTR_WORK <= address < PTR_WORK + 4)
            or (WORK_ADDR <= address < WORK_ADDR + 0x534)
        )
        if not allowed:
            self.bad_writes.append((address, size, value))

    def run(
        self, code: bytes, rodata_blobs: dict[int, bytes], case: dict
    ) -> dict:
        self.task_seq = 0
        self.call_log = []
        self.bad_writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * max(FUNC_SIZE, len(code) + 16))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(RODATA_ADDR, b"\x00" * RODATA_SIZE)
        for base, blob in rodata_blobs.items():
            self.uc.mem_write(base, blob)

        self.uc.mem_write(STACK_ADDR, b"\xCD" * STACK_SIZE)
        self.uc.mem_write(GLOBALS_PAGE, b"\x00" * PAGE_SIZE)
        self.uc.mem_write(WORK_ADDR, b"\xEE" * 0x534)

        self.uc.reg_write(arm.UC_ARM_REG_R0, case["mode"] & 0xFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000, count=200_000)

        return {
            "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "calls": list(self.call_log),
            "ptr_work": bytes(self.uc.mem_read(PTR_WORK, 4)),
            "work": bytes(self.uc.mem_read(WORK_ADDR, 0x534)),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {"name": "mode_0", "mode": 0},
        {"name": "mode_1", "mode": 1},
        {"name": "mode_0xff", "mode": 0xFF},
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("r0", "pc", "sp", "callee", "calls", "ptr_work", "work", "bad_writes"):
        if orig[key] != cand[key]:
            diffs.append(f"{name}: {key} orig={orig[key]!r} cand={cand[key]!r}")
    if cand["sp"] != ENTRY_SP:
        diffs.append(f"{name}: sp not restored: {cand['sp']:#x}")
    if cand["callee"] != CALLEE_SAVED_START:
        diffs.append(f"{name}: callee-saved clobbered: {cand['callee']!r}")
    if cand["bad_writes"]:
        diffs.append(f"{name}: unexpected writes: {cand['bad_writes']!r}")
    return diffs


def main() -> int:
    orig_bytes = get_orig_bytes()
    cand_bytes, cand_rodata = compile_candidate()

    orig_runner = Runner()
    cand_runner = Runner()
    cases = build_cases()

    for case in cases:
        orig_res = orig_runner.run(orig_bytes, {}, case)
        cand_res = cand_runner.run(cand_bytes, cand_rodata, case)
        diffs = compare_outputs(case["name"], orig_res, cand_res)
        if diffs:
            for d in diffs:
                print("FAIL:", d)
            return 1

    mutants = [
        ("work_size", "kWorkSize = 0x534;", "kWorkSize = 0x538;"),
        ("far_z", "kFarZ = 25600.0f;", "kFarZ = 12800.0f;"),
        ("near_z", "kNearZ = 0.1f;", "kNearZ = 0.2f;"),
        ("draw_up_tag", "kDrawUp3dTag = 0x70;", "kDrawUp3dTag = 0x71;"),
        ("draw_down_alt_tag", "kDrawDown2dAltTag = 0x84;", "kDrawDown2dAltTag = 0x85;"),
        ("mode_branch", "if (work[0x530] != 0)", "if (work[0x530] == 0)"),
    ]
    for m_name, old, new in mutants:
        mut_bytes, mut_rodata = compile_candidate_mutant(m_name, old, new)
        mut_runner = Runner()
        detected = False
        for case in cases:
            orig_res = orig_runner.run(orig_bytes, {}, case)
            mut_res = mut_runner.run(mut_bytes, mut_rodata, case)
            if compare_outputs(case["name"], orig_res, mut_res):
                detected = True
                break
        if not detected:
            print(f"FAIL: mutant {m_name} was not detected")
            return 1

    print(
        f"PASS: EffectProcess_func_002217d8 (0x002217d8) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
