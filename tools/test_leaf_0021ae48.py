#!/usr/bin/env python3
"""Differential test for btlGameOver_func_0021ae48 (0x0021ae48) with Unicorn ARM.

Compiles src/battle/battle_extras.cpp, extracts btlGameOver_func_0021ae48,
resolves its direct calls and literal-pool relocations against the pinned
target addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC (0x90000000), final SP, callee-saved r4-r11;
  * ordered call log including stack arguments and task-name strings for
    camp_func_002c4c00 (x3) and engine_func_002c4b84, plus
    Save_GetGameOverStateIndex and Flag_CheckEventBit(0x557);
  * g_pBtlGameOverState_00435d60 (0x00435D60), BtlGameOverState (+0x00..+0x40),
    and BtlGameOverWork (+0x00..+0x44A4);
  * unexpected writes outside allowed buffers and stack.

Coverage:
  * save flag == 0 (Flag_CheckEventBit not called, flags unchanged);
  * save flag != 0 and Flag_CheckEventBit(0x557) != 0 (flags unchanged);
  * save flag != 0 and Flag_CheckEventBit(0x557) == 0 (state->field_04 |= 1,
    work->flags |= 0x80000000);
  * negative/mutation controls on kCalcTag, kDrawUpLeftTag, kStateSize,
    kSaveFlagOffset, kEventBitId, and `work->flags |= 0x80000000u`.
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
OUT_DIR = ROOT / "build/test_leaf_0021ae48"

FUNC_ADDR = 0x0021AE48
FUNC_SIZE = 428

CODE_ADDR = 0x00200000
CODE_SIZE = 0x000F0000  # covers 0x0020EDB0..0x002E0640
GLOBALS_PAGE = 0x00435000
PTR_STATE = 0x00435D60
WORK_ADDR = 0x00500000
WORK_SIZE = 0x00005000
STATE_ADDR = 0x00510000
SAVE_BASE_ADDR = 0x00520000
SAVE_PAGE_SIZE = 0x00026000  # covers SAVE_BASE_ADDR + 0x24B29
RODATA_ADDR = 0x00700000
PAGE_SIZE = 0x00001000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2C4C00 = 0x002C4C00
STUB_2C4B84 = 0x002C4B84
STUB_2C0B94 = 0x002C0B94
STUB_2C0BA8 = 0x002C0BA8

FN_20EDB0 = 0x0020EDB0
FN_2E0640 = 0x002E0640
FN_2C9FDC = 0x002C9FDC

STUB_NAMES = {
    STUB_2C4C00: "camp_func_002c4c00",
    STUB_2C4B84: "engine_func_002c4b84",
    STUB_2C0B94: "Save_GetGameOverStateIndex",
    STUB_2C0BA8: "Flag_CheckEventBit",
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
    if "Save_GetGameOverStateIndex" in symbol_name:
        return STUB_2C0B94
    if "Flag_CheckEventBit" in symbol_name:
        return STUB_2C0BA8
    for address in STUB_NAMES:
        if f"{address:08x}" in symbol_name:
            return address
    return None


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "btlGameOver_func_0021ae48" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"btlGameOver_func_0021ae48 not found in {obj_file}: {sorted(funcs)}"
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
            if "g_pBtlGameOverState_00435d60" in sym:
                target = PTR_STATE + addend
            elif "0020edb0" in sym:
                target = FN_20EDB0 + addend
            elif "002e0640" in sym:
                target = FN_2E0640 + addend
            elif "002c9fdc" in sym:
                target = FN_2C9FDC + addend
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
    """One Unicorn machine with deterministic stubs for btlGameOver_func_0021ae48."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBALS_PAGE, PAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(STATE_ADDR, PAGE_SIZE)
        self.uc.mem_map(SAVE_BASE_ADDR, SAVE_PAGE_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for addr in STUB_NAMES:
            self.uc.mem_write(addr, bx_lr)
        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE320F000))

        self.case: dict = {}
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

        if address == STUB_2C4C00:
            stack_args = struct.unpack("<4I", self.uc.mem_read(sp, 16))
            self.call_log.append(
                (address, self._read_cstr(r0), r1, r2, r3, stack_args)
            )
            self.task_seq += 1
            uc.reg_write(arm.UC_ARM_REG_R0, 0x00600000 + self.task_seq * 0x100)
        elif address == STUB_2C4B84:
            stack_args = struct.unpack("<1I", self.uc.mem_read(sp, 4))
            self.call_log.append((address, r0, r1, r2, r3, stack_args))
            uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
        elif address == STUB_2C0B94:
            self.call_log.append((address,))
            uc.reg_write(arm.UC_ARM_REG_R0, SAVE_BASE_ADDR)
        elif address == STUB_2C0BA8:
            self.call_log.append((address, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["event_bit"])

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
            or (PTR_STATE <= address < PTR_STATE + 4)
            or (WORK_ADDR <= address < WORK_ADDR + 0x44A4)
            or (STATE_ADDR <= address < STATE_ADDR + 0x40)
        )
        if not allowed:
            self.bad_writes.append((address, size, value))

    def run(
        self, code: bytes, rodata_blobs: dict[int, bytes], case: dict
    ) -> dict:
        self.case = case
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

        work = bytearray(b"\x00" * 0x44A4)
        struct.pack_into("<I", work, 0x00, case["parent"])
        struct.pack_into("<I", work, 0x44A0, case["init_flags"])
        self.uc.mem_write(WORK_ADDR, bytes(work))

        state = bytearray(b"\x00" * 0x40)
        struct.pack_into("<I", state, 0x04, case["init_state_04"])
        self.uc.mem_write(STATE_ADDR, bytes(state))

        self.uc.mem_write(SAVE_BASE_ADDR + 0x24B29, bytes([case["save_flag"]]))

        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000, count=200_000)

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "calls": list(self.call_log),
            "ptr_state": bytes(self.uc.mem_read(PTR_STATE, 4)),
            "work_calc": bytes(self.uc.mem_read(WORK_ADDR + 0x2C, 4)),
            "work_flags": bytes(self.uc.mem_read(WORK_ADDR + 0x44A0, 4)),
            "state": bytes(self.uc.mem_read(STATE_ADDR, 0x40)),
            "bad_writes": list(self.bad_writes),
        }


def build_cases() -> list[dict]:
    return [
        {
            "name": "save_flag_zero",
            "parent": 0x00601000,
            "init_flags": 0x00000002,
            "init_state_04": 0x00000010,
            "save_flag": 0,
            "event_bit": 0,
        },
        {
            "name": "save_flag_nonzero_event_set",
            "parent": 0x00602000,
            "init_flags": 0x00000004,
            "init_state_04": 0x00000020,
            "save_flag": 1,
            "event_bit": 1,
        },
        {
            "name": "save_flag_nonzero_event_clear",
            "parent": 0x00000000,
            "init_flags": 0x00000008,
            "init_state_04": 0x00000040,
            "save_flag": 0xFF,
            "event_bit": 0,
        },
    ]


def compare_outputs(name: str, orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee", "calls", "ptr_state", "work_calc", "work_flags", "state", "bad_writes"):
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
        ("calc_tag", "kCalcTag = 2;", "kCalcTag = 3;"),
        ("draw_up_left_tag", "kDrawUpLeftTag = 0x7A;", "kDrawUpLeftTag = 0x7B;"),
        ("state_size", "kStateSize = sizeof(BtlGameOverState);", "kStateSize = 0x44;"),
        ("save_offset", "kSaveFlagOffset = 0x24B29;", "kSaveFlagOffset = 0x24B28;"),
        ("event_bit", "kEventBitId = 0x557;", "kEventBitId = 0x558;"),
        ("work_flags", "work->flags |= 0x80000000u;", "work->flags |= 0x40000000u;"),
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
        f"PASS: btlGameOver_func_0021ae48 (0x0021ae48) matched original across "
        f"{len(cases)} cases and detected {len(mutants)}/{len(mutants)} mutants "
        f"(candidate {len(cand_bytes)} B vs original {len(orig_bytes)} B)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
