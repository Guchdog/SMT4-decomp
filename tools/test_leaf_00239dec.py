#!/usr/bin/env python3
"""Differential test for func_00239dec (0x00239dec) using Unicorn ARM.

Compiles ``src/engine/leaf_batch41_c.cpp``, extracts the ``func_00239dec``
body, resolves its two direct calls to deterministic stubs placed at the
original target addresses (0x003FC300 / 0x003FC46C), and runs the pinned
original (``extracted/exefs/code.bin``) against the candidate on two Unicorn
machines with identical fixtures.

Compared outputs per case:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register argument and the three architected
    stack arguments of both helpers, including whether the second helper's two
    scratch output pointers are writable stack locations;
  * every emulated write outside the private stack, in order;
  * the full record page, halfword page and UI context page.

Coverage: first-call success (including the positive form of the distinguished
status pattern), every distinguished-status component (sign bit, module 0x11,
description 0x6F), first-call non-distinguished failures, second-call success
and its two literals, second-call non-distinguished failures, hash counts
0..16/31/32 and the wrapped-count boundaries (0x80000000, 0x80000001,
0x40000000, 0x40000001, 0xC0000000, 0xC0000001, 0xFFFFFFFF) with unmapped
buffers to prove the no-read paths, zero-extended halfword values, seed
boundaries, data-pointer offsets, and records mutated by the first helper
before the second hash (seed, count and buffer pointer re-reads).

Negative controls recompile mutated source (seed constant, rotate, mix
operator, halfword extension, derived count, byte length, status mask and
constants, context offset, cached second hash, branch direction); each mutant
must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_00239dec"

FUNC_NAME = "func_00239dec"
FUNC_ADDR = 0x00239DEC
FUNC_SIZE = 408

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x00239DEC and both helper addresses
KEY_ADDR = 0x00800000
KEY_SIZE = 0x00001000
DATA_ADDR = 0x00810000
DATA_SIZE = 0x00010000
CTX_ADDR = 0x00820000
CTX_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
KEY_RECORD = KEY_ADDR + 0x100
UNMAPPED_DATA = 0x00DE0000  # never mapped; proves the no-read count paths

# Original direct-call targets; stubs live at the same addresses so the
# original bytes and the relocated candidate resolve to them.
STUB_3FC300 = 0x003FC300
STUB_3FC46C = 0x003FC46C

STUB_NAMES = {
    STUB_3FC300: "ui_func_003fc300",
    STUB_3FC46C: "ui_func_003fc46c",
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

# Status values exercised by the branches.  The distinguished value is
# level bit 31 + module (bits 10..17) 0x11 + description (bits 0..9) 0x6F.
DISTINGUISHED = 0x8000446F
DISTINGUISHED_SUMMARY = 0xC880446F
SUCCESS = 0x00000000
SUCCESS_MAX = 0x7FFFFFFF
POSITIVE_PATTERN = 0x4880446F  # distinguished pattern with bit 31 clear
OTHER_MODULE = 0x8000406F      # module 0x10
OTHER_DESCRIPTION = 0x8000446E # description 0x6E
OTHER_DESCRIPTION_HIGH = 0x80004470
LITERAL_SECOND_SUCCESS = 0xE0C04702
LITERAL_SECOND_FAILURE = 0xC8804471


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "239dec" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(
                f"unresolved relocation {rel.relocation_type} -> {rel.symbol_name}"
            )
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def build_key(case: dict) -> bytes:
    page = bytearray(b"\xCC" * KEY_SIZE)
    struct.pack_into(
        "<III",
        page,
        KEY_RECORD - KEY_ADDR,
        case["seed"] & 0xFFFFFFFF,
        case["count"] & 0xFFFFFFFF,
        case["data_ptr"] & 0xFFFFFFFF,
    )
    return bytes(page)


def build_data(case: dict) -> bytes:
    page = bytearray(DATA_SIZE)
    # Distinct deterministic halfwords everywhere so a wrong index, count or
    # width reads a different value.
    for index in range(DATA_SIZE // 2):
        struct.pack_into("<H", page, 2 * index, (0xA000 + index * 7) & 0xFFFF)
    for index, value in case.get("halfwords", {}).items():
        struct.pack_into("<H", page, 2 * index, value & 0xFFFF)
    return bytes(page)


def build_ctx(case: dict) -> bytes:
    page = bytearray(b"\x3C" * CTX_SIZE)
    struct.pack_into("<I", page, 0x28, 0xDEADBEEF)
    return bytes(page)


# ---------------------------------------------------------------------- runner
class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (KEY_ADDR, KEY_SIZE),
            (DATA_ADDR, DATA_SIZE),
            (CTX_ADDR, CTX_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    @staticmethod
    def _norm(value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _stack_args(self) -> tuple:
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack("<III", self.uc.mem_read(sp, 12))

    def _apply_mutation(self) -> None:
        mutation = self.case.get("mutate")
        if not mutation:
            return
        seed = mutation.get("seed", self.case["seed"])
        count = mutation.get("count", self.case["count"])
        data_ptr = mutation.get("data_ptr", self.case["data_ptr"])
        self.uc.mem_write(
            KEY_RECORD,
            struct.pack(
                "<III", seed & 0xFFFFFFFF, count & 0xFFFFFFFF,
                data_ptr & 0xFFFFFFFF,
            ),
        )

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        stack0, stack1, stack2 = self._stack_args()

        if address == STUB_3FC300:
            self.call_log.append(
                ("ui_func_003fc300", r0, r1, r2, r3, stack0, stack1, stack2)
            )
            self._apply_mutation()
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["first_status"])
        elif address == STUB_3FC46C:
            stack_top = STACK_ADDR + STACK_SIZE
            in_stack_word = STACK_ADDR <= r1 < stack_top
            in_stack_block = STACK_ADDR <= r2 < stack_top
            self.call_log.append(
                (
                    "ui_func_003fc46c",
                    r0,
                    self._norm(r1),
                    self._norm(r2),
                    r3,
                    stack0,
                    stack1,
                    stack2,
                    in_stack_word,
                    in_stack_block,
                    r1 != r2,
                    in_stack_block and r2 + 0x14 <= stack_top,
                )
            )
            # Model the helper writing both scratch outputs; a bogus pointer in
            # the candidate would fault or clobber observable memory here.
            uc.mem_write(r1, struct.pack("<I", 0xA5A50001))
            uc.mem_write(r2, bytes(range(0x14)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["second_status"])
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.case = case
        uc = self.uc

        uc.mem_write(FUNC_ADDR, code)
        uc.mem_write(KEY_ADDR, build_key(case))
        uc.mem_write(DATA_ADDR, build_data(case))
        uc.mem_write(CTX_ADDR, build_ctx(case))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, case["context"])
        uc.reg_write(arm.UC_ARM_REG_R1, case["arg1"])
        uc.reg_write(arm.UC_ARM_REG_R2, case["arg2"])
        uc.reg_write(arm.UC_ARM_REG_R3, KEY_RECORD)
        for name, value in CALLEE_SAVED_START.items():
            uc.reg_write(CALLEE_SAVED[name], value)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = [
            (address, size, value)
            for address, size, value in self.writes
            if not STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
        ]

        return {
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "writes": unexpected_writes,
            "key": bytes(uc.mem_read(KEY_ADDR, KEY_SIZE)),
            "data": bytes(uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "ctx": bytes(uc.mem_read(CTX_ADDR, CTX_SIZE)),
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
    if orig["writes"] != cand["writes"]:
        problems.append(
            "writes:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    for key in ("key", "data", "ctx"):
        if orig[key] != cand[key]:
            for offset in range(len(orig[key])):
                if orig[key][offset] != cand[key][offset]:
                    problems.append(
                        f"fixture {key} differs from offset 0x{offset:x}"
                    )
                    break
    return problems


# ----------------------------------------------------------------------- cases
def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "seed": 0x12345678,
        "count": 4,
        "data_ptr": DATA_ADDR,
        "halfwords": {0: 0x1111, 1: 0x2222, 2: 0x3333, 3: 0x4444},
        "first_status": SUCCESS,
        "second_status": SUCCESS,
        "mutate": None,
        "context": CTX_ADDR,
        "arg1": 0x11111111,
        "arg2": 0x22222222,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- first-call success: bit 31 clear, including the positive form of the
    #     distinguished status pattern.
    for status in (SUCCESS, 0x00000001, SUCCESS_MAX, LITERAL_SECOND_SUCCESS,
                   POSITIVE_PATTERN):
        cases.append(base_case(f"first success 0x{status:08x}",
                               first_status=status))

    # --- first-call failures that are not the distinguished status: the
    #     helper result is returned unchanged and the second call is skipped.
    for status in (OTHER_MODULE, OTHER_DESCRIPTION, OTHER_DESCRIPTION_HIGH,
                   0x80000000, 0xFFFFFFFF, 0x8000446E, 0x80004470,
                   0xA5A5446F, 0x8002446F, 0x8006446F):
        cases.append(base_case(f"first failure 0x{status:08x}",
                               first_status=status,
                               mutate={"seed": 0, "count": 0}))

    # --- distinguished first status: second helper success => 0xE0C04702.
    for status in (DISTINGUISHED, DISTINGUISHED_SUMMARY):
        for second in (SUCCESS, 0x00000001, SUCCESS_MAX, POSITIVE_PATTERN):
            cases.append(base_case(
                f"first 0x{status:08x} second success 0x{second:08x}",
                first_status=status, second_status=second))

    # --- distinguished first status: second helper failure paths.
    for second in (DISTINGUISHED, DISTINGUISHED_SUMMARY):
        cases.append(base_case(
            f"second distinguished 0x{second:08x}",
            first_status=DISTINGUISHED, second_status=second))
    for second in (OTHER_MODULE, OTHER_DESCRIPTION, 0x80000000, 0xFFFFFFFF):
        cases.append(base_case(
            f"second failure 0x{second:08x}",
            first_status=DISTINGUISHED, second_status=second))

    # --- derived element count: every parity / small bound, plus the wrapped
    #     high-bit forms.  Unmapped buffers prove that no element is read.
    for count in range(0, 17):
        cases.append(base_case(f"count {count}", count=count))
    for count in (31, 32):
        cases.append(base_case(f"count {count}", count=count))
    for count in (0xFFFFFFFF, 0x80000000, 0xC0000000, 0x40000000,
                  0xC0000001):
        cases.append(base_case(f"no-read count 0x{count:08x}", count=count,
                               data_ptr=UNMAPPED_DATA))
    # 0x80000001 derives 1 and 0x40000001 derives a negative count; both are
    # read/no-read boundary pairs for the doubled-count arithmetic.
    cases.append(base_case("count 0x80000001 reads one",
                           count=0x80000001))
    cases.append(base_case("count 0x40000001 derives negative",
                           count=0x40000001, data_ptr=UNMAPPED_DATA))

    # --- halfword values: zero extension (0xFFFF / 0x8000 must not sign
    #     extend), plus alternating patterns.
    patterns = {
        "all zero": {i: 0x0000 for i in range(8)},
        "all ffff": {i: 0xFFFF for i in range(8)},
        "all 8000": {i: 0x8000 for i in range(8)},
        "mixed": {i: v for i, v in enumerate(
            (0x0000, 0xFFFF, 0x8000, 0x7FFF, 0x0001, 0xFFFE, 0x00FF,
             0xFF00))},
    }
    for name, pattern in patterns.items():
        cases.append(base_case(f"halfwords {name}", count=len(pattern),
                               halfwords=pattern))

    # --- seed boundaries.
    for seed in (0x00000000, 0xFFFFFFFF, 0x80000000, 0x075BCD15):
        cases.append(base_case(f"seed 0x{seed:08x}", seed=seed, count=8))

    # --- data pointer offsets and argument forwarding.
    for offset in (2, 0x100, 0x2000):
        cases.append(base_case(f"data offset 0x{offset:x}", data_ptr=DATA_ADDR + offset))
    cases.append(base_case("forwarded context/args",
                           context=CTX_ADDR + 0x40, arg1=0xDEADBEEF,
                           arg2=0x80000001))

    # --- the first helper mutates the record before returning; the second
    #     pass must re-read seed, count and buffer pointer.
    cases.append(base_case(
        "second pass re-reads seed",
        first_status=DISTINGUISHED, count=4,
        mutate={"seed": 0x0BADF00D}))
    cases.append(base_case(
        "second pass re-reads count",
        first_status=DISTINGUISHED, count=4,
        mutate={"count": 6}))
    cases.append(base_case(
        "second pass re-reads pointer",
        first_status=DISTINGUISHED, count=4,
        mutate={"data_ptr": DATA_ADDR + 0x100}))
    cases.append(base_case(
        "second pass re-reads a zero count",
        first_status=DISTINGUISHED, count=4,
        mutate={"count": 0, "data_ptr": UNMAPPED_DATA}))
    cases.append(base_case(
        "second pass re-reads a negative count",
        first_status=DISTINGUISHED, count=4,
        mutate={"count": 0xFFFFFFFF, "data_ptr": UNMAPPED_DATA}))
    cases.append(base_case(
        "mutating first helper with second distinguished",
        first_status=DISTINGUISHED, second_status=DISTINGUISHED,
        count=5, mutate={"seed": 0xFFFFFFFF, "count": 0xC0000001,
                         "data_ptr": UNMAPPED_DATA}))

    return cases


# ------------------------------------------------------------------------ main
def run_cases(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
    orig_runner = Runner()
    cand_runner = Runner()
    passed = 0
    for case in cases:
        orig = orig_runner.run(orig_code, case)
        cand = cand_runner.run(cand_code, case)
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
    print(f"Testing {FUNC_NAME} (0x{FUNC_ADDR:08x})...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_cases(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("seed_constant",
         "constexpr u32 kSeedXor = 0x075BCD15;",
         "constexpr u32 kSeedXor = 0x075BCD14;"),
        ("rotate_amount",
         "hash = value ^ ((hash >> 5) | (hash << 27));",
         "hash = value ^ ((hash >> 4) | (hash << 27));"),
        ("mix_operator",
         "hash = value ^ ((hash >> 5) | (hash << 27));",
         "hash = value + ((hash >> 5) | (hash << 27));"),
        ("halfword_sign_extension",
         "const u32 value = record.values[i];  // zero-extended ldrh",
         "const u32 value = static_cast<u32>(static_cast<s32>("
         "static_cast<s16>(record.values[i])));"),
        ("derived_count_shift",
         "return static_cast<s32>(count << 1) >> 1;",
         "return static_cast<s32>(count << 2) >> 1;"),
        ("byte_length_shift",
         "return record.count << 1;",
         "return record.count << 2;"),
        ("failure_level",
         "return (status & func_239dec::kFailureLevel) != 0 &&",
         "return (status & func_239dec::kFailureLevel) == 0 &&"),
        ("module_mask",
         "constexpr u32 kModuleMask = 0x0003FC00;",
         "constexpr u32 kModuleMask = 0x0001FC00;"),
        ("module_value",
         "constexpr u32 kModule11 = 0x00004400;",
         "constexpr u32 kModule11 = 0x00004000;"),
        ("description_value",
         "constexpr u32 kDescription6F = 0x0000006F;",
         "constexpr u32 kDescription6F = 0x0000006E;"),
        ("second_success_literal",
         "constexpr u32 kResultAfterSecondSuccess = 0xE0C04702;",
         "constexpr u32 kResultAfterSecondSuccess = 0xE0C04703;"),
        ("second_failure_literal",
         "constexpr u32 kResultAfterSecondFailure = 0xC8804471;",
         "constexpr u32 kResultAfterSecondFailure = 0xC8804470;"),
        ("context_offset",
         "constexpr u32 kContextOffset = 0x28;",
         "constexpr u32 kContextOffset = 0x2C;"),
        ("cached_second_hash",
         "const u32 second_hash = HashRecord(*record);",
         "const u32 second_hash = first_hash;"),
        ("first_success_direction",
         "if ((first & func_239dec::kFailureLevel) == 0) {",
         "if ((first & func_239dec::kFailureLevel) != 0) {"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        orig_runner = Runner()
        mutant_runner = Runner()
        detected = False
        for case in cases:
            orig = orig_runner.run(orig_code, case)
            try:
                bad = mutant_runner.run(mutant_code, case)
            except RuntimeError:
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED; "
          f"all {len(mutants)} mutants detected.")


if __name__ == "__main__":
    main()
