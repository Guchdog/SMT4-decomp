#!/usr/bin/env python3
"""Differential test for ui_func_00290a68 (0x00290a68) using Unicorn ARM.

The pinned original is a decimal formatter: it appends full-width Shift-JIS
digits ("\x82\x4f" .. "\x82\x58") for each place value from 100000000 down to
1, advancing the destination by the byte count returned by the Thumb formatter
at 0x002BE7FC.  A zero argument is tail-called through the 0x002BE7F4
ARM->Thumb veneer.  The candidate is the readable C++ in
src/engine/leaf_batch41_c.cpp.

Both machines get the same deterministic stubs for the two direct calls:
  * 0x002C615C returns the unsigned quotient in r0 and the remainder in r1,
    and logs (numerator, denominator);
  * 0x002BE7FC copies the four-byte literal pointed to by r1 into r0, returns
    the copied length, and logs (destination offset, literal bytes).

Compared outputs: return r0, continuation PC, final SP, callee-saved r4-r11,
the ordered call log, the whole destination page, and the set of writes made
outside the private stack and destination page.  Coverage includes zero,
positive/signed boundaries, every place transition, the natural quotient >9
"no glyph" path, and forced helper quotients 0..11 plus 0xFFFFFFFF.  Three
compiled negative controls must each be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_00290a68"

FUNC_ADDR = 0x00290A68
FUNC_SIZE = 464

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and both call targets
DATA_ADDR = 0x00700000
DATA_SIZE = 0x00010000
RODATA_ADDR = 0x00710000
RODATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
DST_ADDR = DATA_ADDR + 0x100

STUB_2C615C = 0x002C615C
STUB_2BE7FC = 0x002BE7FC
VENEER_2BE7F4 = 0x002BE7F4

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

EXPECTED_DIGITS = b"".join(
    bytes((0x82, 0x4F + index, 0x00, 0x00)) for index in range(10)
)
assert len(EXPECTED_DIGITS) == 40


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def get_veneer_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(VENEER_2BE7F4 - 0x00100000)
        return handle.read(8)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def encode_call(target: int, pc: int, base_instruction: int, thumb: bool) -> int:
    offset = target - pc
    if thumb:
        if offset & 3:
            raise RuntimeError(f"unaligned Thumb call target 0x{target:08x}")
        # BLX (immediate): cond=1111 101H, H = offset bit 1.
        return (
            0xFA000000
            | ((offset >> 2) & 0x00FFFFFF)
            | ((offset & 2) << 23)
        )
    original = base_instruction
    cond = original & 0xFF000000
    return cond | ((offset >> 2) & 0x00FFFFFF)


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "00290a68" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_00290a68 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            symbol = rel.symbol_name
            original = struct.unpack_from("<I", code, rel.offset)[0]
            pc = FUNC_ADDR + rel.offset + 8
            if "002c615c" in symbol:
                target = STUB_2C615C
                struct.pack_into(
                    "<I", code, rel.offset,
                    encode_call(target, pc, original, thumb=False),
                )
            elif "002be7fc" in symbol:
                if rel.relocation_type == 29:
                    # A tail `b` cannot switch to Thumb; keep LR intact by
                    # branching to the real 0x002BE7F4 veneer.
                    struct.pack_into(
                        "<I", code, rel.offset,
                        encode_call(VENEER_2BE7F4, pc, original, thumb=False),
                    )
                else:
                    struct.pack_into(
                        "<I", code, rel.offset,
                        encode_call(STUB_2BE7FC, pc, original, thumb=True),
                    )
            else:
                raise RuntimeError(f"unresolved call relocation: {symbol}")
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata
            if rel.symbol_name not in ("", ".rodata"):
                raise RuntimeError(
                    f"unexpected ABS32 symbol {rel.symbol_name!r}"
                )
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if addend + len(EXPECTED_DIGITS) > len(
                elf_sections(obj_file).get(".rodata", b"")
            ):
                raise RuntimeError(f"ABS32 addend 0x{addend:x} outside .rodata")
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )

    rodata = elf_sections(obj_file).get(".rodata", b"")
    expected_at = rodata.find(EXPECTED_DIGITS)
    if expected_at < 0:
        raise RuntimeError("full-width digit table not found in .rodata")
    # The patched literal must point at the table we just located.
    for rel in relocs:
        if rel.relocation_type == 2:
            patched = struct.unpack_from("<I", code, rel.offset)[0]
            if patched != RODATA_ADDR + expected_at:
                raise RuntimeError(
                    "digit table literal does not match the .rodata table"
                )
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
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


def read_literal(uc, address: int, limit: int = 4) -> bytes:
    raw = bytes(uc.mem_read(address, limit))
    end = raw.find(b"\x00")
    if end >= 0:
        raw = raw[:end]
    return raw


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        veneer = get_veneer_bytes()
        self.uc.mem_write(VENEER_2BE7F4, veneer)
        self.uc.mem_write(STUB_2C615C, struct.pack("<I", 0xE12FFF1E))  # bx lr
        self.uc.mem_write(STUB_2BE7FC, struct.pack("<H", 0x4770))  # thumb bx lr
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub, begin=STUB_2C615C, end=STUB_2C615C
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub, begin=STUB_2BE7FC, end=STUB_2BE7FC
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_2C615C:
            self.call_log.append(("ui_func_002c615c", r0, r1))
            if r1 == 0:
                quotient = 0
                remainder = r0
            else:
                quotient = r0 // r1
                remainder = r0 % r1
            forced = self.case.get("force_digit")
            if forced is not None:
                quotient = forced & 0xFFFFFFFF
            uc.reg_write(arm.UC_ARM_REG_R0, quotient & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R1, remainder & 0xFFFFFFFF)
        elif address == STUB_2BE7FC:
            glyph = read_literal(uc, r1)
            self.call_log.append(("ui_func_002be7fc", r0 - DST_ADDR, glyph))
            uc.mem_write(r0, glyph + b"\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, len(glyph))
        else:  # pragma: no cover - hook registration guards this
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, bytes([0xCC]) * DATA_SIZE)
        self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, DST_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["value"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_data = DATA_ADDR <= address < DATA_ADDR + DATA_SIZE
            if not in_stack and not in_data:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["data"] != cand["data"]:
        offset = next(
            index
            for index, (left, right) in enumerate(zip(orig["data"], cand["data"]))
            if left != right
        )
        problems.append(
            f"destination page differs from offset 0x{offset:x}: "
            f"orig={orig['data'][offset:offset + 0x20]!r} "
            f"cand={cand['data'][offset:offset + 0x20]!r}"
        )
    if orig["unexpected_writes"] != cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Zero takes the tail-called formatter path.
    cases.append({"name": "value 0 (tail formatter)", "value": 0})

    # Every decimal-place transition and the sign boundary.
    for value in (
        1, 2, 9, 10, 11, 99, 100, 101, 999, 1000, 9999, 10000, 12345,
        99999999, 100000000, 100000001, 123456789, 999999999, 1000000000,
        2147483647,
    ):
        label = str(value) if value >= 0 else f"-{abs(value)}"
        cases.append({"name": f"value {label}", "value": value})

    # Negative arguments skip every place because 100000000 > value holds.
    for value in (-1, -2, -9, -10, -12345, -100000000, -2147483648):
        cases.append({"name": f"negative value {value}", "value": value})

    # Forced helper quotients exercise the `digit < 10` guard directly:
    # 0..9 select each glyph, 10.. and 0xFFFFFFFF are dropped without a call.
    for digit in (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0xFFFFFFFF):
        cases.append(
            {
                "name": f"forced quotient {digit} multi-place",
                "value": 12345,
                "force_digit": digit,
            }
        )
        cases.append(
            {
                "name": f"forced quotient {digit} single-place",
                "value": 9,
                "force_digit": digit,
            }
        )

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, rodata, case)
        cand = Runner().run(cand_code, rodata, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing ui_func_00290a68 (0x00290a68)...")
    orig_code = get_orig_bytes()
    cand_code, cand_rodata = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("glyph_bound", "if (digit < 10) {", "if (digit <= 10) {"),
        ("place_compare", "if (place <= value) {", "if (place < value) {"),
        ("dead_return", "    return 0;\n}\n\n// DECOMP_FUNC(0x002c2210",
         "    return 1;\n}\n\n// DECOMP_FUNC(0x002c2210"),
    ):
        mutant_code, mutant_rodata = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, cand_rodata, case)
            bad = Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
