#!/usr/bin/env python3
"""Differential test for camp_func_001103bc (0x001103bc) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the camp_func_001103bc body,
resolves every direct call to a deterministic stub placed at the pinned
original address, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Coverage:
  * early ``0x002BB608()==0 && 0x002BB420()==0`` fatal return;
  * both ``0x002BB420`` results of the setup (thread state two / not two);
  * the ``0x002BB608`` gated initialisation block, every ``0x002BB5B4``
    result, and the two byte stores into the 0x0044E360 state block;
  * the retry loop for each of the three "not ready" sentinels and for all
    three in sequence (ordered calls, 10 ms sleeps);
  * signed statuses 0 / positive / 0x7FFFFFFF / 0x80000000 / 0xFFFFFFFF for
    the ``0x002BBD10`` negative-status report and its error-site argument;
  * both latched-thread-flag forms and both opposite re-checks of
    0x002BB410 (zero / non-zero / sign-extended negative);
  * the final 0x002BB608 result and the 0x0011D4AC follow-up;
  * the final 0x002BB420 result selecting the ``svc #3`` exit trap with its
    r0 argument.

Compared outputs: return r0, continuation PC, final SP, callee-saved
r4-r11, the ordered call log with every register argument, the ordered
``svc #3`` log with its r0, the whole observable 0x00440000 data page and
any emulated write outside the private stack.  Negative controls mutate a
sentinel, the retry delay, the error-site constant, the state-block address
and the signed-status boundary; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001103bc"

FUNC_ADDR = 0x001103BC
FUNC_SIZE = 480

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and all stubs below 0x00300000
DATA_ADDR = 0x00440000
DATA_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; the stubs sit at the same addresses so the
# original bytes and the relocated candidate resolve to identical helpers.
STUB_11D728 = 0x0011D728
STUB_11D4AC = 0x0011D4AC
STUB_129AF4 = 0x00129AF4
STUB_12A6EC = 0x0012A6EC
STUB_2BB410 = 0x002BB410
STUB_2BB420 = 0x002BB420
STUB_2BB490 = 0x002BB490
STUB_2BB4C0 = 0x002BB4C0
STUB_2BB4D4 = 0x002BB4D4
STUB_2BB54C = 0x002BB54C
STUB_2BB5B4 = 0x002BB5B4
STUB_2BB608 = 0x002BB608
STUB_2BB648 = 0x002BB648
STUB_2BB6B8 = 0x002BB6B8
STUB_2BBD10 = 0x002BBD10
STUB_2C57C4 = 0x002C57C4

# (symbol, register-argument count, returns a value in r0)
STUBS = {
    STUB_11D728: ("func_0011d728", 4, True),
    STUB_11D4AC: ("func_0011d4ac", 1, True),
    STUB_129AF4: ("func_00129af4", 0, False),
    STUB_12A6EC: ("func_0012a6ec", 0, False),
    STUB_2BB410: ("func_002bb410", 0, True),
    STUB_2BB420: ("func_002bb420", 0, True),
    STUB_2BB490: ("camp_func_002bb490", 2, False),
    STUB_2BB4C0: ("func_002bb4c0", 0, False),
    STUB_2BB4D4: ("func_002bb4d4", 1, False),
    STUB_2BB54C: ("func_002bb54c", 0, False),
    STUB_2BB5B4: ("func_002bb5b4", 0, True),
    STUB_2BB608: ("func_002bb608", 0, True),
    STUB_2BB648: ("engine_func_002bb648", 0, False),
    STUB_2BB6B8: ("engine_func_002bb6b8", 0, False),
    STUB_2BBD10: ("nn_sdk_func_002bbd10", 2, False),
    STUB_2C57C4: ("engine_func_002c57c4", 1, False),
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

K_NOT_READY = (0xC8A0CFF0, 0xE0A0CC08, 0xC8A0CC02)
K_NO_STATE = 0xC8A0CC04


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001103bc" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_001103bc not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, (name, _argc, _ret) in STUBS.items():
            if rel.symbol_name == name or rel.symbol_name.endswith("_" + name):
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
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
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address in STUBS:
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        # The conditional SVC is intercepted after execution; Unicorn only
        # reports it when its condition passes and continues at PC+4.
        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_interrupt)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.svc_log: list = []
        self.writes: list = []
        self.return_index: dict = {}
        self.case: dict = {}

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        name, argc, returns = STUBS[address]
        registers = (
            arm.UC_ARM_REG_R0,
            arm.UC_ARM_REG_R1,
            arm.UC_ARM_REG_R2,
            arm.UC_ARM_REG_R3,
        )
        args = tuple(uc.reg_read(reg) for reg in registers[:argc])
        self.call_log.append((name, args))
        if returns:
            values = self.case["returns"].get(name, ())
            index = self.return_index.get(name, 0)
            if index >= len(values):
                raise AssertionError(
                    f"stub {name} called {index + 1} times without a return value"
                )
            self.return_index[name] = index + 1
            uc.reg_write(arm.UC_ARM_REG_R0, values[index] & 0xFFFFFFFF)

    def _on_interrupt(self, uc, intno, user_data) -> None:
        # UC_HOOK_INTR reports the SVC after the PC has advanced past it.
        pc = uc.reg_read(arm.UC_ARM_REG_PC)
        word = struct.unpack("<I", uc.mem_read(pc - 4, 4))[0]
        if (word & 0x0F000000) != 0x0F000000:
            raise AssertionError(
                f"unexpected ARM exception {intno} at 0x{pc - 4:08x}"
            )
        self.svc_log.append((word & 0x00FFFFFF, uc.reg_read(arm.UC_ARM_REG_R0)))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.svc_log = []
        self.writes = []
        self.return_index = {}
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case["args"][0] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["args"][1] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["args"][2] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["args"][3] & 0xFFFFFFFF)
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
            if not (in_stack or in_data):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "svc_log": list(self.svc_log),
            "data": bytes(self.uc.mem_read(DATA_ADDR, DATA_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    for key in ("call_log", "svc_log"):
        if orig[key] != cand[key]:
            problems.append(
                f"{key}:\n    orig=" + repr(orig[key]) + "\n    cand=" + repr(cand[key])
            )
    if orig["data"] != cand["data"]:
        diffs = [
            index
            for index, (left, right) in enumerate(zip(orig["data"], cand["data"]))
            if left != right
        ]
        problems.append(
            "data page differs at "
            + ", ".join(f"0x{DATA_ADDR + index:08x}" for index in diffs[:16])
        )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def make_case(
    name: str,
    *,
    r608,
    r420,
    r410,
    statuses,
    r5b4=(0,),
    r11d4ac=(0,),
    args=(0x0011D728, 0x22223333, 0x44445555, 0x66667777),
) -> dict:
    """Build one fixture with return values listed in exact call order.

    Control-flow call order (the bracketed calls are conditional):
      0x002BB608 a;  [0x002BB420 a if a == 0];  0x002BB420 b;
      [0x002BB608 b if b_420 == 0];  [0x002BB5B4];  0x002BB410 a;
      0x0011D728 (one per loop attempt);  0x002BB410 b;
      0x002BB608 c;  [0x0011D4AC];  0x002BB420 c.
    """
    return {
        "name": name,
        "args": tuple(args),
        "returns": {
            "func_002bb608": tuple(r608),
            "func_002bb420": tuple(r420),
            "func_002bb5b4": tuple(r5b4),
            "func_002bb410": tuple(r410),
            "func_0011d728": tuple(statuses),
            "func_0011d4ac": tuple(r11d4ac),
        },
    }


def make_cases() -> list:
    cases: list = []

    # --- the fatal early return: 608 == 0 and 420 == 0
    cases.append(make_case("fatal early return", r608=(0,), r420=(0,),
                           r410=(), statuses=()))

    # --- setup: thread state two (skip the initialisation block)
    cases.append(
        make_case(
            "setup state two",
            r608=(1, 0),
            r420=(1, 0),
            r410=(0, 0),
            statuses=(1,),
        )
    )
    cases.append(
        make_case(
            "setup state two negative flag",
            r608=(1, 0),
            r420=(1, 0),
            r410=(-1, -1),
            statuses=(0,),
        )
    )

    # --- setup: 420 == 0 and 608 == 0 -> no initialisation block.
    # (The early 420 must be non-zero when the early 608 is zero.)
    cases.append(
        make_case("setup skipped block", r608=(0, 0, 0), r420=(1, 0, 0),
                  r410=(0, 0), statuses=(1,))
    )

    # --- setup block, both 0x002BB5B4 forms
    cases.append(
        make_case(
            "setup block no cleanup",
            r608=(0, 1, 0),
            r420=(1, 0, 0),
            r5b4=(0,),
            r410=(0, 0),
            statuses=(1,),
        )
    )
    cases.append(
        make_case(
            "setup block cleanup",
            r608=(0, 1, 0),
            r420=(1, 0, 0),
            r5b4=(-1,),
            r410=(1, 1),
            statuses=(1,),
        )
    )
    cases.append(
        make_case(
            "setup block cleanup positive",
            r608=(0, 2, 0),
            r420=(1, 0, 0),
            r5b4=(0x7F,),
            r410=(0x80, 0),
            statuses=(1,),
        )
    )

    # --- loop: each "not ready" sentinel individually, then a status
    for sentinel in K_NOT_READY:
        cases.append(
            make_case(
                f"retry sentinel 0x{sentinel:08x}",
                r608=(1, 0),
                r420=(1, 0),
                r410=(0, 0),
                statuses=(sentinel, 0x12345678),
            )
        )
    # --- loop: all three sentinels in order, then a normal status
    cases.append(
        make_case(
            "retry all sentinels",
            r608=(1, 0),
            r420=(1, 0),
            r410=(1, 0),
            statuses=(K_NOT_READY[0], K_NOT_READY[1], K_NOT_READY[2], 0x600D),
        )
    )
    # --- loop: repeated same sentinel then a normal status
    cases.append(
        make_case(
            "retry repeated sentinel",
            r608=(1, 0),
            r420=(1, 0),
            r410=(0, 1),
            statuses=(K_NOT_READY[1], K_NOT_READY[1], 0, 1),
        )
    )

    # --- signed status boundaries for 0x002BBD10
    for status in (0x00000000, 0x00000001, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF):
        cases.append(
            make_case(
                f"status 0x{status:08x}",
                r608=(1, 0),
                r420=(1, 0),
                r410=(0, 0),
                statuses=(status,),
            )
        )

    # --- post-loop 0x002BB410 opposite re-checks
    cases.append(
        make_case(
            "latched flag zero, recheck nonzero",
            r608=(1, 0),
            r420=(1, 0),
            r410=(0, 1),
            statuses=(1,),
        )
    )
    cases.append(
        make_case(
            "latched flag nonzero, recheck zero",
            r608=(1, 0),
            r420=(1, 0),
            r410=(1, 0),
            statuses=(1,),
        )
    )
    cases.append(
        make_case(
            "latched flag nonzero, recheck negative",
            r608=(1, 0),
            r420=(1, 0),
            r410=(-1, -2),
            statuses=(1,),
        )
    )

    # --- post-loop 0x002BB608 and the 0x0011D4AC follow-up
    cases.append(
        make_case(
            "follow-up called",
            r608=(1, 1, 1),
            r420=(1, 0),
            r410=(0, 0),
            statuses=(0x10,),
            r11d4ac=(0xDEADBEEF,),
        )
    )
    cases.append(
        make_case(
            "follow-up negative result",
            r608=(1, 1, 1),
            r420=(1, 0),
            r410=(0, 0),
            statuses=(5,),
            r11d4ac=(0x80000000,),
        )
    )
    cases.append(
        make_case(
            "follow-up not called",
            r608=(1, 0, 0),
            r420=(1, 0),
            r410=(0, 0),
            statuses=(0x20,),
        )
    )

    # --- final 0x002BB420 selecting the svc #3 trap
    cases.append(
        make_case("svc taken", r608=(1, 0), r420=(1, 1), r410=(0, 0),
                  statuses=(1,))
    )
    cases.append(
        make_case(
            "svc taken negative code",
            r608=(1, 0),
            r420=(1, 0xFFFFFFFF),
            r410=(0, 0),
            statuses=(1,),
        )
    )
    cases.append(
        make_case("svc skipped", r608=(1, 0), r420=(1, 0), r410=(0, 0),
                  statuses=(1,))
    )

    # --- argument forwarding, including sign-bit and all-ones words
    for args in (
        (0, 0, 0, 0),
        (0xFFFFFFFF, 0x80000000, 0x7FFFFFFF, 0xDEADBEEF),
        (0x0044E360, 0x00110530, 0xC8A0CC04, 0x00000001),
    ):
        cases.append(
            make_case(
                "args " + ",".join(f"0x{arg:08x}" for arg in args),
                r608=(1, 1, 1),
                r420=(1, 0),
                r410=(0, 0),
                statuses=(0x33,),
                r11d4ac=(args[0] ^ 0xA5A5A5A5,),
                args=args,
            )
        )

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list) -> int:
    passed = 0
    for case in cases:
        fixture = case
        orig = Runner().run(orig_code, fixture)
        cand = Runner().run(cand_code, fixture)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
            f"{len(orig['svc_log'])} svc)"
        )
    return passed


def main() -> None:
    print("Testing camp_func_001103bc (0x001103bc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("sentinel_1", "kNotReady1 = 0xE0A0CC08u;", "kNotReady1 = 0xE0A0CC09u;"),
        ("retry_delay", "kRetryDelayNs = 10000000u;", "kRetryDelayNs = 10000001u;"),
        ("error_site", "kErrorSite = 0x00110530u;", "kErrorSite = 0x00110534u;"),
        ("state_block", "kStateBlock = 0x0044E360u;", "kStateBlock = 0x0044E368u;"),
        (
            "signed_boundary",
            "if (static_cast<s32>(status) < 0) {",
            "if (static_cast<s32>(status) <= 0) {",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            fixture = case
            orig = Runner().run(orig_code, fixture)
            bad = Runner().run(mutant_code, fixture)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
