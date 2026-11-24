#!/usr/bin/env python3
"""Differential test for func_00159028 (0x00159028), 840 bytes.

The pinned original is an internally-called extended-precision mantissa
division core with a private register convention (dividend in r0/r1/r2,
divisor in r3/r4/r5; quotient sign in r0, mantissa in r1/r2, biased exponent
in r3 and guard word in r6).  The reconstruction keeps those values as a
C++ parameter/return contract, so this test compiles the real translation
unit plus a tiny AAPCS wrapper that calls the C++ function with six value
arguments and stores the five results.

What is compared per case:
  * the five contract outputs (sign, mantissa hi/lo, exponent, guard) against
    r0, r1, r2, r3 and r6 of the original;
  * preserved registers: the original must return r7, r8, r9, r10, r11
    unchanged; the compiled wrapper must return r4-r11 unchanged;
  * return PC and final SP (both return to the trap with the entry SP);
  * every byte of the input fixtures, the reciprocal-table page and the code
    page must be unchanged (the routine is a leaf that only writes its own
    stack);
  * the original executes no instruction outside its own 840-byte span, and
    the compiled core has no call/undefined relocation, i.e. an empty ordered
    call log for both.

Coverage includes both return paths (normal renormalisation and the
sign-set early exit), zero/one/maximum mantissas, exponent boundaries,
signed quotient combinations, divisors on every reciprocal-table page, and
non-normalised divisors (which select the function's own instruction bytes,
reproduced verbatim in the reconstruction's lookup table).

Negative controls compile mutated sources and require the case set to detect
each one: the a_lo rounding seed, the exponent bias, the remainder sticky bit
and one reciprocal-table entry.
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
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_00159028"

FUNC_ADDR = 0x00159028
FUNC_SIZE = 840

# Original execution image and private helpers.
ORIG_CODE_ADDR = 0x00100000
ORIG_CODE_SIZE = 0x00400000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Candidate image: core, AAPCS wrapper, lookup table, argument/output pages.
CAND_CODE_ADDR = 0x001F0000
CAND_CODE_SIZE = 0x00040000
CORE_ADDR = 0x001F0000
WRAPPER_ADDR = 0x001F1000
TABLE_ADDR = 0x001F2000
ARGS_ADDR = 0x001F3000
OUT_ADDR = 0x001F3040

PRESERVED_ORIG = ("r8", "r9", "r10", "r11")
PRESERVED_CAND = ("r4", "r5", "r6", "r7", "r8", "r9", "r10", "r11")
ENTRY_SENTINELS = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}


# --------------------------------------------------------------- ELF helpers
def elf_sections(path: Path) -> list[tuple[str, int, bytes]]:
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
    out = []
    for section in sections:
        name = shstrtab[section[0] :].split(b"\x00")[0].decode("ascii", "replace")
        out.append((name, section[3], data[section[4] : section[4] + section[5]]))
    return out


def extract_table(path: Path) -> bytes:
    for name, _addr, payload in elf_sections(path):
        if "kDivisorLut" in name:
            return payload
    raise RuntimeError("kDivisorLut section not found")


def extract_function(obj: Path, needle: str):
    funcs = extract_elf_functions_detailed(obj)
    for name, value in funcs.items():
        if needle in name:
            return value
    raise RuntimeError(f"{needle} not found in {obj}: {sorted(funcs)}")


def compile_harness(source: Path, out_obj: Path) -> Path:
    harness = OUT_DIR / "harness.cpp"
    harness.write_text(
        f'#include "{source.resolve().as_posix()}"\n'
        "\n"
        'extern "C" __attribute__((noinline)) void test_entry_00159028('
        "const u32* in, u32* out) {\n"
        "    const auto r = func_00159028(in[0], in[1], in[2], in[3], in[4], in[5]);\n"
        "    out[0] = r.sign;\n"
        "    out[1] = r.mantissa_hi;\n"
        "    out[2] = r.mantissa_lo;\n"
        "    out[3] = r.exponent;\n"
        "    out[4] = r.guard;\n"
        "}\n",
        encoding="utf-8",
    )
    result = compile_tu_armv6k(harness, out_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return out_obj


def build_candidate(source: Path, tag: str):
    obj = compile_harness(source, OUT_DIR / f"harness_{tag}.o")
    core_code, core_relocs = extract_function(obj, "func_00159028")
    wrapper_code, wrapper_relocs = extract_function(obj, "test_entry_00159028")
    table = extract_table(obj)

    if len(core_code) < 4:
        raise RuntimeError("empty core")
    for rel in core_relocs:
        if rel.relocation_type != 2:
            raise RuntimeError(
                f"core has a non-data relocation ({rel.relocation_type}, "
                f"{rel.symbol_name}); the reconstruction must be a leaf"
            )
    for rel in wrapper_relocs:
        if rel.relocation_type not in (28, 29) or "func_00159028" not in rel.symbol_name:
            raise RuntimeError(f"unexpected wrapper relocation {rel}")

    core = bytearray(core_code)
    wrapper = bytearray(wrapper_code)
    for rel in core_relocs:
        addend = struct.unpack_from("<I", core, rel.offset)[0]
        struct.pack_into("<I", core, rel.offset, TABLE_ADDR + addend)
    for rel in wrapper_relocs:
        displacement = (CORE_ADDR - (WRAPPER_ADDR + rel.offset + 8)) >> 2
        struct.pack_into("<I", wrapper, rel.offset, 0xEB000000 | (displacement & 0xFFFFFF))
    return bytes(core), bytes(wrapper), table


# ------------------------------------------------------------------- machines
def load_original_machine() -> unicorn.Uc:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(ORIG_CODE_ADDR, ORIG_CODE_SIZE)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(TRAP_ADDR, 0x1000)
    uc.mem_write(ORIG_CODE_ADDR, ORIG_BIN.read_bytes())
    return uc


def load_candidate_machine(core: bytes, wrapper: bytes, table: bytes) -> unicorn.Uc:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.mem_map(CAND_CODE_ADDR, CAND_CODE_SIZE)
    uc.mem_map(STACK_ADDR, STACK_SIZE)
    uc.mem_map(TRAP_ADDR, 0x1000)
    uc.mem_write(CORE_ADDR, core)
    uc.mem_write(WRAPPER_ADDR, wrapper)
    uc.mem_write(TABLE_ADDR, table)
    uc.mem_write(ARGS_ADDR, b"\x00" * 0x40)
    uc.mem_write(OUT_ADDR, b"\x00" * 0x40)
    return uc


def read_regs(uc) -> dict:
    return {f"r{i}": uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(13)}


def run_original(uc, operands: tuple[int, int, int, int, int, int]) -> dict:
    uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    for name, value in ENTRY_SENTINELS.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), value)
    for index, value in enumerate(operands):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), value)
    executed: list[int] = []
    uc.hook_add(
        unicorn.UC_HOOK_CODE,
        lambda u, address, size, data: executed.append(address),
        begin=ORIG_CODE_ADDR,
        end=ORIG_CODE_ADDR + ORIG_CODE_SIZE - 4,
    )
    uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
    regs = read_regs(uc)
    pc = uc.reg_read(arm.UC_ARM_REG_PC)
    sp = uc.reg_read(arm.UC_ARM_REG_SP)
    return {
        "outputs": (regs["r0"], regs["r1"], regs["r2"], regs["r3"], regs["r6"]),
        "regs": regs,
        "pc": pc,
        "sp": sp,
        "executed": executed,
        "code": bytes(uc.mem_read(ORIG_CODE_ADDR, ORIG_CODE_SIZE)),
    }


def run_candidate(uc, operands: tuple[int, int, int, int, int, int]) -> dict:
    uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
    uc.mem_write(ARGS_ADDR, b"\x00" * 0x40)
    uc.mem_write(OUT_ADDR, b"\x00" * 0x40)
    uc.mem_write(ARGS_ADDR, struct.pack("<6I", *operands))
    uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
    uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R0, ARGS_ADDR)
    uc.reg_write(arm.UC_ARM_REG_R1, OUT_ADDR)
    for name, value in ENTRY_SENTINELS.items():
        uc.reg_write(getattr(arm, f"UC_ARM_REG_{name.upper()}"), value)
    writes: list[tuple[int, int]] = []
    executed: list[int] = []
    uc.hook_add(
        unicorn.UC_HOOK_MEM_WRITE,
        lambda u, access, address, size, value, data: writes.append((address, size)),
    )
    uc.hook_add(
        unicorn.UC_HOOK_CODE,
        lambda u, address, size, data: executed.append(address),
        begin=CAND_CODE_ADDR,
        end=CAND_CODE_ADDR + CAND_CODE_SIZE - 4,
    )
    uc.emu_start(WRAPPER_ADDR, TRAP_ADDR, timeout=5_000_000)
    regs = read_regs(uc)
    pc = uc.reg_read(arm.UC_ARM_REG_PC)
    sp = uc.reg_read(arm.UC_ARM_REG_SP)
    out = struct.unpack("<5I", bytes(uc.mem_read(OUT_ADDR, 20)))
    return {
        "outputs": out,
        "regs": regs,
        "pc": pc,
        "sp": sp,
        "writes": writes,
        "executed": executed,
        "args": bytes(uc.mem_read(ARGS_ADDR, 0x40)),
        "code": bytes(uc.mem_read(CAND_CODE_ADDR, CAND_CODE_SIZE)),
        "table": bytes(uc.mem_read(TABLE_ADDR, 256)),
    }


# --------------------------------------------------------------------- cases
def ext(exp: int, hi: int, lo: int, sign: int = 0) -> tuple[int, int, int]:
    return (((sign & 1) << 31) | (exp & 0xFFFFFF), hi & 0xFFFFFFFF, lo & 0xFFFFFFFF)


def make_cases() -> list[tuple[str, tuple[int, int, int, int, int, int]]]:
    cases: list[tuple[str, tuple]] = []

    def add(name, a, b):
        cases.append((name, (*a, *b)))

    one = ext(0x3FFF, 0x80000000, 0x00000000)
    half = ext(0x3FFE, 0x80000000, 0x00000000)
    two = ext(0x4000, 0x80000000, 0x00000000)

    add("1 / 1", one, one)
    add("1 / 2 (exponent down)", one, half)
    add("2 / 1 (exponent up)", two, one)
    add("100 / 3", ext(0x4005, 0xC8000000, 0x00000000),
        ext(0x4000, 0xC0000000, 0x00000000))
    add("3 / 100", ext(0x4000, 0xC0000000, 0x00000000),
        ext(0x4005, 0xC8000000, 0x00000000))
    add("1 / 3 (repeating)", one, ext(0x4000, 0xC0000000, 0x00000000))
    add("2/3 / 1", ext(0x3FFF, 0xAAAAAAAA, 0xAAAAAAAA), one)
    add("all-one mantissa / 1", ext(0x3FFF, 0xFFFFFFFF, 0xFFFFFFFF), one)
    add("1 / all-one mantissa", one, ext(0x3FFF, 0xFFFFFFFF, 0xFFFFFFFF))
    add("min normal / max", ext(0x0001, 0x80000000, 0x00000000),
        ext(0xFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF))
    add("max exp / min normal", ext(0xFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF),
        ext(0x0001, 0x80000000, 0x00000000))
    add("zero exponent both", ext(0x0000, 0x80000000, 0x00000000),
        ext(0x0000, 0x80000000, 0x00000000))

    # Sign combinations: the quotient sign is the XOR of the operand signs.
    for sa in (0, 1):
        for sb in (0, 1):
            add(f"sign {sa}/{sb}", ext(0x3FFF, 0xC0000000, 0x12345678, sa),
                ext(0x4002, 0xA0000000, 0x9ABCDEF0, sb))

    # Mantissa low-word boundaries, including the wrapping bit used to seed r0.
    for lo in (0x00000000, 0x00000001, 0x00000002, 0x7FFFFFFF, 0x80000000,
               0xFFFFFFFE, 0xFFFFFFFF):
        add(f"dividend lo 0x{lo:08x}", ext(0x3FFC, 0x9ABCDEF0, lo),
            ext(0x4001, 0x81234567, 0x89ABCDEF))
    for lo in (0x00000000, 0x00000001, 0xFFFFFFFF, 0x80000001):
        add(f"divisor lo 0x{lo:08x}", ext(0x3FFC, 0x9ABCDEF0, 0x0F1E2D3C),
            ext(0x4001, 0x81234567, lo))

    # High-word boundaries: top byte covers the whole reciprocal-table page.
    for hi in (0x80000000, 0x81000000, 0x9F000000, 0xBF000000, 0xFE000000,
               0xFF000000, 0xFFFFFFFF):
        add(f"divisor hi 0x{hi:08x}", ext(0x3FFD, 0xC3D2E1F0, 0x0A0B0C0D),
            ext(0x3FFA, hi, 0x10203040))

    # Non-normalised divisors reach the first half of the lookup table.
    for hi in (0x00000000, 0x01000000, 0x3F000000, 0x7F000000, 0x7FFFFFFF):
        add(f"unnormalised divisor hi 0x{hi:08x}",
            ext(0x3FFE, 0x88776655, 0x44332211), ext(0x4001, hi, 0x99887766))

    # Exponents that force the biased difference to wrap around zero.
    for a_exp, b_exp in ((0x3FFF, 0x3FFF), (0x3FFF, 0x4000), (0x4000, 0x3FFF),
                         (0x0000, 0x3FFF), (0x3FFF, 0x0000),
                         (0x0000, 0x0000), (0xFFFFFF, 0x3FFF),
                         (0x3FFF, 0xFFFFFF), (0x8000, 0x7FFF)):
        add(f"exp 0x{a_exp:06x}/0x{b_exp:06x}",
            ext(a_exp, 0xE0000000, 0x00000001),
            ext(b_exp, 0xC0000000, 0xFFFFFFFF))

    return cases


# ------------------------------------------------------------------ checks
def describe(regs: dict) -> str:
    return " ".join(
        f"r{i}=0x{regs[f'r{i}']:08x}" for i in range(13)
    )


def compare_case(original: dict, candidate: dict, name: str) -> list[str]:
    problems: list[str] = []
    if original["outputs"] != candidate["outputs"]:
        problems.append(
            f"outputs differ: orig={[hex(v) for v in original['outputs']]} "
            f"cand={[hex(v) for v in candidate['outputs']]}"
        )
    for reg in PRESERVED_ORIG:
        if original["regs"][reg] != ENTRY_SENTINELS[reg]:
            problems.append(
                f"original did not preserve {reg} "
                f"(0x{original['regs'][reg]:08x} != 0x{ENTRY_SENTINELS[reg]:08x})"
            )
    # Documented original quirk: r7 is preloaded with (divisor exponent word &
    # 0xFFFFFF) before the prologue push, so the epilogue restores that value
    # rather than the caller's r7.  It is not consumed by the rounding partner.
    if original["regs"]["r7"] != (original["inputs"][3] & 0x00FFFFFF):
        problems.append(
            f"original r7 artifact: 0x{original['regs']['r7']:08x} != "
            f"0x{original['inputs'][3] & 0x00FFFFFF:08x}"
        )
    for reg in PRESERVED_CAND:
        if candidate["regs"][reg] != ENTRY_SENTINELS[reg]:
            problems.append(
                f"candidate did not preserve {reg} "
                f"(0x{candidate['regs'][reg]:08x} != 0x{ENTRY_SENTINELS[reg]:08x})"
            )
    if original["pc"] != TRAP_ADDR or candidate["pc"] != TRAP_ADDR:
        problems.append(
            f"return PC: orig=0x{original['pc']:08x} cand=0x{candidate['pc']:08x}"
        )
    if original["sp"] != ENTRY_SP or candidate["sp"] != ENTRY_SP:
        problems.append(
            f"final SP: orig=0x{original['sp']:08x} cand=0x{candidate['sp']:08x}"
        )
    # The original must stay inside its own span and issue no calls.
    outside = [
        pc for pc in original["executed"]
        if not (FUNC_ADDR <= pc < FUNC_ADDR + FUNC_SIZE)
    ]
    if outside:
        problems.append(f"original left its span: {[hex(p) for p in outside[:4]]}")
    # The compiled core must be the only thing the wrapper calls.
    for pc in candidate["executed"]:
        if not (CORE_ADDR <= pc < CORE_ADDR + 0x1000 or
                WRAPPER_ADDR <= pc < WRAPPER_ADDR + 0x1000):
            problems.append(f"candidate executed outside core/wrapper: 0x{pc:08x}")
            break
    if candidate["args"][:24] != struct.pack("<6I", *candidate["inputs"]):
        problems.append("candidate modified its argument buffer")
    if candidate["table"] != candidate["table_image"]:
        problems.append("candidate modified its lookup table")
    # No writes outside the candidate's private stack and output buffer.
    for address, _size in candidate["writes"]:
        if not (
            STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            or OUT_ADDR <= address < OUT_ADDR + 0x20
        ):
            problems.append(f"candidate wrote outside private storage at 0x{address:08x}")
            break
    return problems


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    original_uc = load_original_machine()
    core, wrapper, table = build_candidate(SOURCE, "baseline")
    original_table = ORIG_BIN.read_bytes()[
        0x159270 - ORIG_CODE_ADDR : 0x159370 - ORIG_CODE_ADDR
    ]
    if table != original_table:
        raise SystemExit("reconstruction table does not match the original bytes")

    candidate_uc = load_candidate_machine(core, wrapper, table)
    print(
        f"Original {FUNC_SIZE} B, candidate core {len(core)} B, "
        f"wrapper {len(wrapper)} B, table {len(table)} B."
    )

    cases = make_cases()
    seen_early = seen_normal = False
    seen_table_low = seen_table_high = False
    passed = 0
    for name, operands in cases:
        original = run_original(original_uc, operands)
        candidate = run_candidate(candidate_uc, operands)
        original["inputs"] = operands
        candidate["inputs"] = operands
        candidate["table_image"] = table
        problems = compare_case(original, candidate, name)
        if problems:
            print(f"  [FAIL] {name}")
            for problem in problems:
                print(f"    {problem}")
            print(f"    orig  {describe(original['regs'])}")
            print(f"    cand  {describe(candidate['regs'])}")
            raise SystemExit(1)
        # Coverage bookkeeping.
        seen_early |= bool(original["outputs"][1] & 0x80000000)
        seen_normal |= not (original["outputs"][1] & 0x80000000)
        index = (operands[4] >> 24) & 0xFF
        if index >= 0x80:
            seen_table_high = True
        else:
            seen_table_low = True
        passed += 1
        print(f"  [PASS] {name}  -> "
              f"{[hex(v) for v in original['outputs']]}")

    if not (seen_early and seen_normal):
        raise SystemExit(
            f"case set missed a return path (early={seen_early}, normal={seen_normal})"
        )
    if not (seen_table_low and seen_table_high):
        raise SystemExit(
            f"case set missed a table half (low={seen_table_low}, high={seen_table_high})"
        )

    print("\nNegative controls:")
    source_text = SOURCE.read_text(encoding="utf-8")
    mutations = (
        ("a_lo_seed", "r0 = a_lo_lsb ? 0x80000000u : 0u;", "r0 = 0u;"),
        ("exponent_bias", "const u32 saved_exponent = r3 + 0xFFu;",
         "const u32 saved_exponent = r3 + 0xFEu;"),
        ("sticky_bit", "if ((r1 | r2) != 0) {", "if ((r1 | r2) != 1) {"),
        ("reciprocal_entry", "    0x80, 0x80, 0x7F, 0x7E,", "    0x40, 0x80, 0x7F, 0x7E,"),
    )
    for tag, old, new in mutations:
        if source_text.count(old) != 1:
            raise SystemExit(f"mutation anchor {old!r} occurs {source_text.count(old)} times")
        mutant_source = OUT_DIR / f"mutant_{tag}.cpp"
        mutant_source.write_text(source_text.replace(old, new), encoding="utf-8")
        try:
            mutant_core, mutant_wrapper, mutant_table = build_candidate(
                mutant_source, tag
            )
        except RuntimeError as error:
            print(f"  [PASS] {tag} mutant rejected ({error})")
            continue
        mutant_uc = load_candidate_machine(
            mutant_core, mutant_wrapper, mutant_table
        )
        detected = False
        for name, operands in cases:
            original = run_original(original_uc, operands)
            candidate = run_candidate(mutant_uc, operands)
            original["inputs"] = operands
            candidate["inputs"] = operands
            candidate["table_image"] = mutant_table
            if compare_case(original, candidate, name):
                detected = True
                print(f"  [PASS] {tag} mutant detected by '{name}'")
                break
        if not detected:
            raise SystemExit(f"negative control failed: {tag} was not detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
