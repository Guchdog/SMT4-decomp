#!/usr/bin/env python3
"""Differential test for func_002ac0c4 (0x002AC0C4), single-precision expf.

The pinned original (extracted/exefs/code.bin) and the compiled candidate from
src/engine/leaf_batch45_b.cpp run in separate Unicorn ARM machines with
identical fixtures.  The three library helpers the function reaches are placed
at their pinned addresses:

* 0x002A4600 - real bytes (raw-float classifier, ARM) so candidate and original
  execute identical classification logic;
* 0x002A462C - real bytes (synthetic underflow squaring, ARM) so the IEEE
  underflow-flag side effect is reproduced;
* 0x002A464E - deterministic Thumb stub that records the errno code it receives
  and stores it in a private errno cell (the real code calls 0x002C6840).

Compared per case: return s0 bits, continuation PC, final SP, callee-saved
r4-r11 and d8-d15, the ordered helper call log (classifier input bits, squaring
entries, errno codes), the errno cell, and that no memory is written outside the
private stack frame or the errno cell.  FPSCR is compared with the cumulative
exception flags (bits 0-4) masked; the synthesised +inf returns are compiler
constants and are not guaranteed to raise the overflow flag (documented limit).

Coverage: both ends of the normal band (2^-24 and 84.0), the split band up to
104.0, the huge-magnitude ERANGE band, every polynomial table index, denormal
results, underflow-to-zero, overflow-to-inf, +-0, +-inf and quiet/signalling
NaNs.  Five compiled negative controls must each be detected.
"""

from __future__ import annotations

import hashlib
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_002ac0c4"

FUNC_ADDR = 0x002AC0C4
FUNC_SIZE = 560
FUNC_SYMBOL = "func_002ac0c4"

CODE_ADDR = 0x00200000
CODE_SIZE = 0x00200000  # 0x200000..0x400000: function, helpers and literal pools
ORIG_RODATA_ADDR = 0x00400000
ORIG_RODATA_SIZE = 0x00020000
CAND_RODATA_ADDR = 0x00500000
CAND_RODATA_SIZE = 0x00001000
ERRNO_ADDR = 0x00700000
ERRNO_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

HELPER_CLASS = 0x002A4600   # int classify(u32 bits)
HELPER_SQUARE = 0x002A462C  # float square_tiny(void)
HELPER_ERRNO = 0x002A464E   # void errno_store(u32)  (Thumb)

HELPER_ADDRS = (HELPER_CLASS, HELPER_SQUARE, HELPER_ERRNO)
THUMB_STUBS = {HELPER_ERRNO}

CALLEE_REGS = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}
DFP_REGS = {f"d{i}": getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16)}
DFP_START = {f"d{i}": 0x0102030405060708 * (i - 7) for i in range(8, 16)}


def orig_bytes(addr: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(addr - 0x00100000)
        return f.read(size)


def float_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def elf_sections(path: Path) -> tuple[dict[str, bytes], list[tuple]]:
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
    return result, sections


def resolve_helper(symbol_name: str) -> int:
    for address in HELPER_ADDRS:
        if f"{address:08x}" in symbol_name:
            return address
    raise RuntimeError(f"unexpected call relocation target: {symbol_name!r}")


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if FUNC_SYMBOL in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"{FUNC_SYMBOL} not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    sections, _ = elf_sections(obj_file)
    rodata = sections.get(".rodata.cst16", b"")

    for rel in relocs:
        offset = rel.offset
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = resolve_helper(rel.symbol_name)
            pc = FUNC_ADDR + offset + 8
            displacement = target - pc
            if target in THUMB_STUBS:
                if displacement & 1:
                    raise RuntimeError(f"odd Thumb target 0x{target:08x}")
                insn = (
                    0xFA000000
                    | ((displacement >> 2) & 0x00FFFFFF)
                    | ((displacement & 2) << 23)
                )
                struct.pack_into("<I", code, offset, insn)
            else:
                if displacement & 3:
                    raise RuntimeError(f"unaligned ARM target 0x{target:08x}")
                original = struct.unpack_from("<I", code, offset)[0]
                struct.pack_into(
                    "<I",
                    code,
                    offset,
                    (original & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF),
                )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata.cst16
            addend = struct.unpack_from("<I", code, offset)[0]
            if addend + 4 > len(rodata):
                raise RuntimeError(f"rodata addend 0x{addend:x} out of range")
            struct.pack_into("<I", code, offset, CAND_RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name!r}"
            )
    if not rodata:
        raise RuntimeError("candidate has no .rodata.cst16 table section")
    return bytes(code), rodata


def compile_candidate() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"compilation failed:\n{res.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"mutant {name} failed to compile:\n{res.stderr}")
    return relocate_candidate(obj_file)


class ExpfMachine:
    """One Unicorn machine with the pinned helper code and fixtures."""

    def __init__(self, candidate: bool) -> None:
        self.candidate = candidate
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(ORIG_RODATA_ADDR, ORIG_RODATA_SIZE)
        self.uc.mem_map(CAND_RODATA_ADDR, CAND_RODATA_SIZE)
        self.uc.mem_map(ERRNO_ADDR, ERRNO_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        # Enable the VFP/NEON unit (FPEXC.EN); Unicorn starts with it disabled.
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        # Real pinned tables used by the original's PC-relative add accesses.
        self.uc.mem_write(
            ORIG_RODATA_ADDR, orig_bytes(ORIG_RODATA_ADDR, ORIG_RODATA_SIZE)
        )
        # Real helper bodies for the classifier and the underflow squaring.
        self.uc.mem_write(HELPER_CLASS, orig_bytes(HELPER_CLASS, 0x30))
        self.uc.mem_write(HELPER_SQUARE, orig_bytes(HELPER_SQUARE, 0x10))
        # Deterministic Thumb errno stub.
        self.uc.mem_write(HELPER_ERRNO, struct.pack("<H", 0x4770))  # bx lr

        self.log: list[tuple] = []
        self.writes: list[int] = []
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_class, begin=HELPER_CLASS, end=HELPER_CLASS)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_square, begin=HELPER_SQUARE, end=HELPER_SQUARE)
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._on_errno, begin=HELPER_ERRNO, end=HELPER_ERRNO)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self._rodata_written = False

    def _on_class(self, uc, address, size, user_data):
        self.log.append(("classify", uc.reg_read(arm.UC_ARM_REG_R0) & 0xFFFFFFFF))

    def _on_square(self, uc, address, size, user_data):
        self.log.append(("square",))

    def _on_errno(self, uc, address, size, user_data):
        code = uc.reg_read(arm.UC_ARM_REG_R0) & 0xFFFFFFFF
        self.log.append(("errno", code))
        uc.mem_write(ERRNO_ADDR, struct.pack("<I", code))

    def _on_write(self, uc, access, address, size, value, user_data):
        self.writes.append(address)

    def install(self, code: bytes, rodata: bytes | None) -> None:
        self.uc.mem_write(FUNC_ADDR, code)
        if rodata is not None:
            self.uc.mem_write(CAND_RODATA_ADDR, rodata)

    def run(self, x_bits: int) -> dict:
        self.log = []
        self.writes = []
        self.uc.mem_write(ERRNO_ADDR, b"\x00" * ERRNO_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_PC, FUNC_ADDR)
        for name, reg in CALLEE_REGS.items():
            self.uc.reg_write(reg, CALLEE_START[name])
        for name, reg in DFP_REGS.items():
            self.uc.reg_write(reg, DFP_START[name])
        self.uc.reg_write(arm.UC_ARM_REG_S0, x_bits)
        self.uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as exc:  # pragma: no cover - crash diagnostics
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"crash at PC=0x{pc:08x}: {exc}") from exc

        outside = [
            address
            for address in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
            and not (ERRNO_ADDR <= address < ERRNO_ADDR + ERRNO_SIZE)
        ]
        return {
            "s0": self.uc.reg_read(arm.UC_ARM_REG_S0) & 0xFFFFFFFF,
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC) & 0xFFFFFFFF,
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP) & 0xFFFFFFFF,
            "r": {
                name: self.uc.reg_read(reg) & 0xFFFFFFFF
                for name, reg in CALLEE_REGS.items()
            },
            "d": {
                name: self.uc.reg_read(reg)
                for name, reg in DFP_REGS.items()
            },
            "fpscr": self.uc.reg_read(arm.UC_ARM_REG_FPSCR) & 0xFFFFFFFF,
            "errno": bytes(self.uc.mem_read(ERRNO_ADDR, 0x40)),
            "log": list(self.log),
            "outside": outside,
        }


def describe(bits: int) -> str:
    return f"0x{bits:08x} ({struct.unpack('<f', struct.pack('<I', bits))[0]!r})"


CASES: list[tuple[str, int]] = [
    # zero / tiny (returns 1.0)
    ("+0.0", 0x00000000),
    ("-0.0", 0x80000000),
    ("+min denormal", 0x00000001),
    ("-min denormal", 0x80000001),
    ("largest below 2^-24", 0x337FFFFF),
    ("2^-24 boundary (poly)", 0x33800000),
    ("smallest poly above 2^-24", 0x33800001),
    # polynomial table indices
    ("1.0 (idx 2)", float_bits(1.0)),
    ("0.0->idx0", float_bits(0.125)),
    ("0.2 (idx 1)", float_bits(0.2)),
    ("0.5 (idx 3)", float_bits(0.5)),
    ("-0.2", float_bits(-0.2)),
    ("-0.5", float_bits(-0.5)),
    ("-1.0 (idx 2, negative)", float_bits(-1.0)),
    ("0.3", float_bits(0.3)),
    ("1.7", float_bits(1.7)),
    ("2.2", float_bits(2.2)),
    ("-2.2", float_bits(-2.2)),
    ("10.0", float_bits(10.0)),
    ("-10.0", float_bits(-10.0)),
    ("50.0", float_bits(50.0)),
    ("-50.0", float_bits(-50.0)),
    # normal-band upper edge / split band
    ("84.0 boundary (poly)", float_bits(84.0)),
    ("84.0 next float (split)", 0x42A80001),
    ("84.5", float_bits(84.5)),
    ("86.5", float_bits(86.5)),
    ("88.0 (split, fits)", float_bits(88.0)),
    ("88.72 (split, near overflow)", float_bits(88.72)),
    ("89.0 (split, overflow)", float_bits(89.0)),
    ("100.0 (split, overflow)", float_bits(100.0)),
    ("104.0 boundary (split)", float_bits(104.0)),
    ("104.0 next float (errno)", 0x42D00001),
    ("-84.0 boundary (poly)", float_bits(-84.0)),
    ("-84.0 next float (split)", 0xC2A80001),
    ("-88.0", float_bits(-88.0)),
    ("-89.0 (denormal)", float_bits(-89.0)),
    ("-90.0 (denormal)", float_bits(-90.0)),
    ("-100.0 (denormal)", float_bits(-100.0)),
    ("-103.9", float_bits(-103.9)),
    ("-104.0 (underflow zero)", float_bits(-104.0)),
    # range-error band
    ("+105.0", float_bits(105.0)),
    ("-105.0", float_bits(-105.0)),
    ("+1000.0", float_bits(1000.0)),
    ("-1000.0", float_bits(-1000.0)),
    ("+1e30", float_bits(1e30)),
    ("-1e30", float_bits(-1e30)),
    ("max float", 0x7F7FFFFF),
    ("-max float", 0xFF7FFFFF),
    # inf / NaN
    ("+inf", 0x7F800000),
    ("-inf", 0xFF800000),
    ("quiet NaN", 0x7FC00000),
    ("-quiet NaN", 0xFFC00000),
    ("signalling NaN", 0x7F800001),
    ("NaN payload", 0x7FBFFFFF),
]


def compare(case_name: str, x_bits: int, orig: dict, cand: dict) -> list[str]:
    problems: list[str] = []
    for key in ("s0", "pc", "sp"):
        if orig[key] != cand[key]:
            problems.append(
                f"{key}: orig=0x{orig[key]:08x} cand=0x{cand[key]:08x}"
            )
    if (orig["fpscr"] & ~0x1F) != (cand["fpscr"] & ~0x1F):
        problems.append(
            f"fpscr(control): orig=0x{orig['fpscr']:08x} cand=0x{cand['fpscr']:08x}"
        )
    for name in CALLEE_REGS:
        if orig["r"][name] != cand["r"][name]:
            problems.append(
                f"{name}: orig=0x{orig['r'][name]:08x} cand=0x{cand['r'][name]:08x}"
            )
    for name in DFP_REGS:
        if orig["d"][name] != cand["d"][name]:
            problems.append(
                f"{name}: orig=0x{orig['d'][name]:016x} cand=0x{cand['d'][name]:016x}"
            )
    if orig["errno"] != cand["errno"]:
        problems.append(
            f"errno: orig={orig['errno'][:8].hex()} cand={cand['errno'][:8].hex()}"
        )
    if orig["log"] != cand["log"]:
        problems.append(f"call log: orig={orig['log']} cand={cand['log']}")
    if orig["outside"]:
        problems.append(f"original wrote outside private memory: {orig['outside']}")
    if cand["outside"]:
        problems.append(f"candidate wrote outside private memory: {cand['outside']}")
    return problems


def run_suite(orig_code: bytes, cand_code: bytes, rodata: bytes | None,
              cases: list[tuple[str, int]], verbose: bool = False) -> list[str]:
    orig_machine = ExpfMachine(candidate=False)
    cand_machine = ExpfMachine(candidate=True)
    orig_machine.install(orig_code, None)
    cand_machine.install(cand_code, rodata)

    failures: list[str] = []
    for name, x_bits in cases:
        orig = orig_machine.run(x_bits)
        cand = cand_machine.run(x_bits)
        problems = compare(name, x_bits, orig, cand)
        if verbose:
            status = "PASS" if not problems else "FAIL"
            print(f"  [{status}] {name:<34} {describe(x_bits)} -> "
                  f"0x{orig['s0']:08x} log={orig['log']}")
        if problems:
            failures.append(f"{name} ({describe(x_bits)}): " + "; ".join(problems))
    return failures


MUTANTS = [
    ("reduction_constant",
     "    float r = x - nf * 0x1.62ep-3f;",
     "    float r = x - nf * 0x1.630p-3f;"),
    ("index_mask",
     "    const u32 index = static_cast<u32>(n) & 3u;",
     "    const u32 index = static_cast<u32>(n) & 1u;"),
    ("negative_infinity_return",
     "        return (raw == 0xff800000u) ? 0.0f : x + x;",
     "        return (raw == 0xff800000u) ? x : x + x;"),
    ("range_error_sign_swap",
     "    if ((raw & 0x80000000u) == 0u) {",
     "    if ((raw & 0x80000000u) != 0u) {"),
    ("classifier_threshold",
     "    if (math_func_002a4600(result_bits) == 4) {",
     "    if (math_func_002a4600(result_bits) == 5) {"),
    ("tiny_result_constant",
     "        return 1.0f;",
     "        return 0x1.000002p+0f;"),
]


def main() -> int:
    print(f"Testing {FUNC_SYMBOL} (0x{FUNC_ADDR:08X})...")
    orig_code = orig_bytes(FUNC_ADDR, FUNC_SIZE)
    cand_code, rodata = compile_candidate()
    print(f"  original: {len(orig_code)} B; candidate: {len(cand_code)} B, "
          f"rodata {len(rodata)} B")

    failures = run_suite(orig_code, cand_code, rodata, CASES, verbose=True)
    total = len(CASES)
    if failures:
        print("\nFAILURES:")
        for failure in failures:
            print(f"  - {failure}")
        print(f"\n{total - len(failures)}/{total} differential cases passed.")
        return 1
    print(f"\nAll {total}/{total} differential cases PASSED.")

    print("\nNegative controls (must be detected):")
    undetected = []
    for name, old, new in MUTANTS:
        try:
            mutant_code, mutant_rodata = compile_mutant(name, old, new)
        except RuntimeError as exc:
            print(f"  [skip] {name}: {exc}")
            undetected.append(name)
            continue
        mutant_failures = run_suite(
            orig_code, mutant_code, mutant_rodata, CASES, verbose=False
        )
        if mutant_failures:
            print(f"  [detected] {name}: {len(mutant_failures)} mismatching cases")
        else:
            print(f"  [MISSED] {name}")
            undetected.append(name)

    if undetected:
        print(f"\nNegative controls not detected: {undetected}")
        return 1
    print("\nAll negative controls detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
