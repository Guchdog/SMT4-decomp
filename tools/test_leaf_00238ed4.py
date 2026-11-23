#!/usr/bin/env python3
"""Differential test for engine_func_00238ed4 (0x00238ed4) using Unicorn ARM.

Compiles ``src/engine/leaf_batch45_b.cpp``, extracts the
``engine_func_00238ed4`` body, resolves its eleven direct-call relocations to
deterministic stubs placed at the pinned original addresses, and runs the
original (``extracted/exefs/code.bin``) against the candidate in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: every helper, every register argument and the
    architected stack arguments (the two ``s64`` timeout words of 0x002C42FC);
  * the ``svc #0x23`` (svcCloseHandle) events with their handle argument;
  * state bytes at 0x004656CA / 0x00472A40 / 0x004E629C and every emulated
    write outside the private stack.

Coverage: state bytes 0/non-zero, the 0x00239BEC gate returning 0, +1, -1 and
-128, flags[1] shut/open, the 0x0035B0A4 setup Result negative (several bit
patterns) and non-negative, flags[2] pre-set, kind 0/non-zero, mode
0/1/0xFFFFFFFF, a negative and a non-negative 0x00359288 wait Result with
zero/non-zero output handles, 0x002C42FC Results matching and not matching the
``Result << 22 == 0xFF800000`` poll predicate (including the 0x3FE/0x3FF/0x7FFFF3FE
boundaries and negative/aborting Results), status 0/1/2, a status-1 exit on the
last permitted iteration, and the full 62-iteration exhaustion.

Negative controls compile source mutants (loop bound 0x3C -> 0x3B, poll mask
0x3FE -> 0x3FF, failure sentinel, and the kind-selected slot index) and require
each to be detected by the same comparison.
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
OUT_DIR = ROOT / "build/test_leaf_00238ed4"

FUNC_ADDR = 0x00238ED4
FUNC_SIZE = 452

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers 0x238ED4 and every stub up to 0x359288
DATA_ADDR = 0x00460000
DATA_SIZE = 0x00090000  # covers 0x4656CA, 0x472A40 and the lock at 0x4E629C
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STATE_ADDR = 0x004656CA
STATE_SIZE = 3
SIGNED_BYTE_ADDR = 0x00472A40
LOCK_ADDR = 0x004E629C

STUB_239BEC = 0x00239BEC
STUB_239BB0 = 0x00239BB0
STUB_2C3AA8 = 0x002C3AA8
STUB_2C3A24 = 0x002C3A24
STUB_35B0A4 = 0x0035B0A4
STUB_2BB490 = 0x002BB490
STUB_2C42FC = 0x002C42FC
STUB_2C5468 = 0x002C5468
STUB_359288 = 0x00359288
STUB_359088 = 0x00359088

STUB_NAMES = {
    STUB_239BEC: "engine_func_00239bec",
    STUB_239BB0: "func_00239bb0",
    STUB_2C3AA8: "engine_func_002c3aa8",
    STUB_2C3A24: "engine_func_002c3a24",
    STUB_35B0A4: "func_0035b0a4",
    STUB_2BB490: "camp_func_002bb490",
    STUB_2C42FC: "engine_func_002c42fc",
    STUB_2C5468: "engine_func_002c5468",
    STUB_359288: "func_00359288",
    STUB_359088: "func_00359088",
}

# Register arguments each helper receives beyond r0-r3.
STACK_ARGS = {
    STUB_2C42FC: 2,  # s64 timeout low/high words
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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get("engine_func_00238ed4")
    if entry is None:
        raise RuntimeError(f"engine_func_00238ed4 not found: {sorted(funcs)}")
    code_raw, relocs = entry
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (1, 28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name or name == rel.symbol_name:
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


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {count} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def read_string(uc, address: int, limit: int = 64) -> bytes:
    out = bytearray()
    for index in range(limit):
        try:
            byte = uc.mem_read(address + index, 1)[0]
        except unicorn.UcError:
            break
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def pick(sequence, index: int):
    if not sequence:
        return 0
    return sequence[min(index, len(sequence) - 1)]


class Runner238ED4:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(DATA_ADDR, DATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_INTR, self._on_intr)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.svc_log: list = []
        self.writes: list = []
        self.return_serial = 0
        self.wait_calls = 0
        self.status_calls = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _norm(self, uc, value: int):
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _read_u32(self, address: int) -> int:
        try:
            return struct.unpack("<I", self.uc.mem_read(address, 4))[0]
        except unicorn.UcError:
            return None

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_intr(self, uc, intno, user_data) -> None:
        # ARM SVC (intno 2): record svcCloseHandle(handle). Unicorn has already
        # advanced PC past the SVC opcode when it delivers this interrupt.
        self.svc_log.append(("svc", intno, self._norm(uc, uc.reg_read(arm.UC_ARM_REG_R0))))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        stack = self._stack_words(STACK_ARGS.get(address, 0))

        if address == STUB_239BEC:
            self.call_log.append(("engine_func_00239bec",))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["signed_byte"] & 0xFFFFFFFF)

        elif address == STUB_239BB0:
            self.call_log.append(("func_00239bb0", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("slot_value", 0x51) & 0xFFFFFFFF)

        elif address in (STUB_2C3AA8, STUB_2C3A24):
            self.call_log.append((STUB_NAMES[address], self._norm(uc, r0)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)

        elif address == STUB_35B0A4:
            self.call_log.append(("func_0035b0a4", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["setup_result"] & 0xFFFFFFFF)

        elif address == STUB_2BB490:
            self.call_log.append(("camp_func_002bb490", r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)

        elif address == STUB_2C42FC:
            handle = self._read_u32(r1)
            self.call_log.append(
                ("engine_func_002c42fc", self._norm(uc, r0), self._norm(uc, r1),
                 handle, r2, r3, *stack)
            )
            index = self.wait_calls
            self.wait_calls += 1
            result = pick(self.case["wait_results"], index)
            # The real trampoline stores the kernel's r1 into its first
            # argument; nothing reads that slot, so a distinct marker is used.
            uc.mem_write(r0, struct.pack("<I", 0x00010000 | (index & 0xFFFF)))
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)

        elif address == STUB_2C5468:
            self.call_log.append(("engine_func_002c5468", r0))
            # The real reporter never returns; give the continuation a fixed
            # register state so both machines stay comparable.
            for reg, value in (
                (arm.UC_ARM_REG_R0, 0xBAD00000),
                (arm.UC_ARM_REG_R1, 0),
                (arm.UC_ARM_REG_R2, 0),
                (arm.UC_ARM_REG_R3, 0),
            ):
                uc.reg_write(reg, value)

        elif address == STUB_359288:
            self.call_log.append(("func_00359288", self._norm(uc, r0)))
            uc.mem_write(r0, struct.pack("<I", self.case["handle_out"] & 0xFFFFFFFF))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["wait_alloc_result"] & 0xFFFFFFFF)

        elif address == STUB_359088:
            self.call_log.append(("func_00359088", self._norm(uc, r0)))
            status = pick(self.case["statuses"], self.status_calls)
            self.status_calls += 1
            uc.mem_write(r0, struct.pack("<I", status & 0xFFFFFFFF))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case.get("status_result", 0) & 0xFFFFFFFF)

        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.svc_log = []
        self.writes = []
        self.return_serial = 0
        self.wait_calls = 0
        self.status_calls = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        state = case.get("state", (0, 1, 1))
        self.uc.mem_write(STATE_ADDR, bytes(state))
        self.uc.mem_write(SIGNED_BYTE_ADDR, bytes([case.get("signed_byte_raw", 0) & 0xFF]))
        lock_blob = case.get("lock_blob", b"\x00" * 0x10)
        self.uc.mem_write(LOCK_ADDR, lock_blob)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, case.get("kind", 0) & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case.get("mode", 0) & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        self.writes = []

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=20_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(
                f"Crash at PC=0x{pc:08x} in case {case['name']}: {error}"
            ) from error

        unexpected_writes = []
        for address, size, _value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self.call_log,
            "svc_log": self.svc_log,
            "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
            "signed_byte": bytes(self.uc.mem_read(SIGNED_BYTE_ADDR, 1)),
            "lock": bytes(self.uc.mem_read(LOCK_ADDR, len(lock_blob))),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "call_log", "svc_log",
                "state", "signed_byte", "lock", "unexpected_writes"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "state": (0x01, 0x01, 0x01),   # gate open, initialised, setup done
        "signed_byte": 1,
        "setup_result": 0,
        "kind": 1,
        "mode": 0,
        "handle_out": 0x1234,
        "wait_alloc_result": 0,
        "wait_results": [0x3FE],
        "statuses": [1],
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- the 0x004656CA gate byte: 0 asks 0x00239BEC, non-zero skips it.
    cases.append(base_case("gate 0 signed byte 0 -> failure", state=(0, 1, 1), signed_byte=0))
    cases.append(base_case("gate 0 signed byte +1", state=(0, 1, 1), signed_byte=1))
    cases.append(base_case("gate 0 signed byte -1", state=(0, 1, 1), signed_byte=-1))
    cases.append(base_case("gate 0 signed byte -128", state=(0, 1, 1), signed_byte=-128))
    cases.append(base_case("gate 0x80 non-zero", state=(0x80, 1, 1), signed_byte=0))
    cases.append(base_case("gate 0xFF non-zero", state=(0xFF, 1, 1), signed_byte=0))

    # --- flags[1]: shut means unlock + failure without touching flags[2].
    cases.append(base_case("flags1 zero -> failure", state=(1, 0, 0)))
    cases.append(base_case("flags1 zero, gate 0 byte 0", state=(0, 0, 0), signed_byte=0))
    cases.append(base_case("flags1 0xFF", state=(1, 0xFF, 1)))

    # --- flags[2] / 0x0035B0A4 setup Result (signed bit 31 test).
    for result in (0, 1, 0x7FFFFFFF, 0x80000000, 0xC8A10BF0, 0xFFFFFFFF):
        cases.append(base_case(f"setup result 0x{result:08x}", state=(1, 1, 0),
                               setup_result=result))
    cases.append(base_case("flags2 pre-set", state=(1, 1, 1), setup_result=0xC8A10BF0))
    cases.append(base_case("flags2 0xFF pre-set", state=(1, 1, 0xFF), setup_result=0))

    # --- kind selects the slot index; mode != 0 skips the wait loop.
    for kind in (0, 1, 0xFFFFFFFF):
        for mode in (1, 0xFFFFFFFF):
            cases.append(base_case(f"kind {kind} mode 0x{mode:08x}", kind=kind, mode=mode))
    cases.append(base_case("kind 0 mode 0 wait path", kind=0, mode=0))
    cases.append(base_case("mode 1 no handle close", kind=1, mode=1, handle_out=0x9999))

    # --- 0x00359288 wait-alloc Result and the output handle.
    cases.append(base_case("wait alloc negative discards handle",
                           wait_alloc_result=0x80000000, handle_out=0x5678))
    cases.append(base_case("wait alloc -1 discards handle",
                           wait_alloc_result=0xFFFFFFFF, handle_out=0x5678))
    cases.append(base_case("wait alloc 0 with zero handle",
                           wait_alloc_result=0, handle_out=0))
    cases.append(base_case("wait alloc max with handle",
                           wait_alloc_result=0x7FFFFFFF, handle_out=0xCAFEBABE))

    # --- 0x002C42FC poll predicate: (Result << 22) == 0xFF800000.
    for result in (0x3FE, 0x3FF, 0x7FFFF3FE, 0xFFFFF3FE, 0, 0x200, 0x80000000,
                   0xFFFFFFFF, 0x7FFFFFFF):
        cases.append(base_case(f"poll result 0x{result:08x}", wait_results=[result]))

    # --- status handling after a matching poll Result.
    for status in (0, 1, 2, 0xFFFFFFFF):
        cases.append(base_case(f"status {status} after match",
                               wait_results=[0x3FE], statuses=[status]))

    # --- the poll loop takes at most 62 bodies; status 1 on the last body wins
    #     over the exhaustion failure.
    cases.append(base_case("loop exhaustion -> failure", wait_results=[0x3FE],
                           statuses=[0]))
    cases.append(base_case("status 1 on last body",
                           wait_results=[0x3FE],
                           statuses=[0] * 61 + [1]))
    cases.append(base_case("status 1 on second body",
                           wait_results=[0x3FE], statuses=[0, 1]))

    # --- abort reporter: negative Results, then the poll predicate decides.
    for result in (0x80000000, 0x800003FE, 0xFFFFFFFF):
        cases.append(base_case(f"abort on 0x{result:08x}", wait_results=[result]))
        cases.append(base_case(f"abort on 0x{result:08x} mode 1", mode=1,
                               wait_results=[result]))

    # --- a mixed sequence across iterations.
    cases.append(base_case("mixed sequence",
                           wait_results=[0x3FE, 0x3FE, 0x3FF],
                           statuses=[0, 0, 0]))

    # --- lock payload is never written (transactional behaviour check).
    cases.append(base_case("lock payload untouched",
                           lock_blob=bytes(range(0x10))))
    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner238ED4().run(orig_code, case)
        cand = Runner238ED4().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
              f"{len(orig['svc_log'])} svc)")
    return passed


def main() -> None:
    print("Testing engine_func_00238ed4 (0x00238ed4)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    controls = (
        ("iteration_limit",
         "constexpr u32 kWaitIterationLimit = 0x3Cu;",
         "constexpr u32 kWaitIterationLimit = 0x3Bu;"),
        ("poll_mask",
         "0xFF800000u", "0x7F800000u"),
        ("failure_sentinel",
         "constexpr u32 kFailure = 0xC8A10BF0u;",
         "constexpr u32 kFailure = 0xC8A10BF1u;"),
        ("slot_index",
         "(kind != 0) ? 0x0Cu : 0x0Bu", "0x0Bu"),
    )
    for name, old, new in controls:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner238ED4().run(orig_code, case)
            bad = Runner238ED4().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED; "
          f"{len(controls)} negative controls detected.")


if __name__ == "__main__":
    main()
